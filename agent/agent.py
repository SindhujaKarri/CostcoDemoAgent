"""
agent.py - Retail Stockout Prevention Agent

Capabilities
------------
• Skill tool  – invokes .claude/skills/retail-stockout-prevention/ (SKILL.md decision logic)
• Bash tool   – runs Python scripts in agent/scripts/ to query retail Excel data
• WebSearch   – fetches live signals (weather.gov, competitors, BLS, supplier portals)
• Computer    – GUI automation (screenshot / click / type); enable via ENABLE_COMPUTER_TOOL=true

Data scripts (call via Bash):
    python scripts/read_data.py --sheet <name> [--filter col=val] [--cols a,b] [--max N]
    python scripts/stockout_summary.py [--sku N] [--region N] [--threshold N]
    python scripts/log_escalation.py --code E3 --severity critical --message "..." --action "..."

Usage (CLI):
    python agent.py "Check stockout risk for region 3"
    python agent.py --query "Scan all regions for 6+ store stockouts"

Usage (programmatic):
    from agent import run_agent
    result = await run_agent("Check PO pipeline for supplier 4")
"""

import base64
import os
import subprocess
import sys
import json
import logging
import time
import uuid
import asyncio
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from claude_agent_sdk import query, ClaudeAgentOptions
from tools import AGENT_MCP_SERVER, DESKTOP_MCP_SERVER, ALLOWED_MCP_TOOLS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(name)s] %(message)s",
)
logger = logging.getLogger("AGENT")

_DISPLAY    = os.environ.get("DISPLAY", "")   # Set in Docker; empty on Windows
_SS_PATH    = "/tmp/aria_ss.png"
_AGENT_LOG  = "/tmp/agent.log"


def _log_to_display(text: str) -> None:
    """Write a line to the xterm activity log visible in the video feed."""
    if not _DISPLAY:
        return
    try:
        ts = time.strftime("%H:%M:%S")
        with open(_AGENT_LOG, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"[{ts}] {text}\n")
    except Exception:
        pass


async def _take_screenshot() -> Optional[str]:
    """
    Capture the virtual display (Xvfb) with scrot.
    Returns base64-encoded PNG string, or None if unavailable (e.g. Windows).
    """
    if not _DISPLAY:
        return None
    logger.info(f"[SCREENSHOT] Taking screenshot on DISPLAY={_DISPLAY} ...")
    try:
        proc = await asyncio.create_subprocess_exec(
            "scrot", "--overwrite", _SS_PATH,
            env={**os.environ, "DISPLAY": _DISPLAY},
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=5.0)
        if proc.returncode == 0 and Path(_SS_PATH).exists():
            data = Path(_SS_PATH).read_bytes()
            logger.info(f"[SCREENSHOT] OK — {len(data):,} bytes captured, encoding to base64")
            return base64.b64encode(data).decode()
        else:
            logger.warning(f"[SCREENSHOT] scrot exited with code {proc.returncode}")
    except asyncio.TimeoutError:
        logger.warning("[SCREENSHOT] scrot timed out after 5s")
    except Exception as e:
        logger.warning(f"[SCREENSHOT] error: {e}")
    return None


async def _open_url_in_chromium(url: str) -> None:
    """Open a URL in Chromium on the virtual display (non-blocking)."""
    if not _DISPLAY or not url.startswith("http"):
        return
    try:
        subprocess.Popen(
            ["chromium", "--no-sandbox", "--disable-dev-shm-usage",
             "--disable-gpu", "--new-tab", url],
            env={**os.environ, "DISPLAY": _DISPLAY},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        logger.debug(f"[CHROMIUM] failed to open {url}: {e}")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"
DATA_DIR = PROJECT_ROOT / "data" / "Retail data raw" / "Retail data raw"
SCRIPTS_DIR = Path(__file__).parent / "scripts"

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
MAX_TURNS = int(os.environ.get("MAX_TURNS", "15"))
PERMISSION_MODE = os.environ.get("PERMISSION_MODE", "bypassPermissions").split("#")[0].strip()

COMPUTER_DISPLAY_WIDTH = int(os.environ.get("COMPUTER_DISPLAY_WIDTH", "1920"))
COMPUTER_DISPLAY_HEIGHT = int(os.environ.get("COMPUTER_DISPLAY_HEIGHT", "1080"))
ENABLE_COMPUTER_TOOL = os.environ.get("ENABLE_COMPUTER_TOOL", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Skill loader
# ---------------------------------------------------------------------------

def _load_skill_content(skill_name: str) -> str:
    """Read all files from a skill directory into one string."""
    skill_dir = SKILLS_DIR / skill_name
    if not skill_dir.exists():
        return ""
    sections: List[str] = []
    for ext in ["*.md", "*.json", "*.txt", "*.yaml"]:
        for fp in sorted(skill_dir.glob(ext)):
            try:
                content = fp.read_text(encoding="utf-8")
                sections.append(f"### {fp.name}\n{content}")
            except Exception:
                pass
    return "\n\n".join(sections)


def _load_all_skills() -> Dict[str, str]:
    if not SKILLS_DIR.exists():
        return {}
    return {
        d.name: _load_skill_content(d.name)
        for d in sorted(SKILLS_DIR.iterdir())
        if d.is_dir()
    }


def _build_skills_prompt(skills: Dict[str, str]) -> str:
    if not skills:
        return ""
    skill_names = ", ".join(skills)
    blocks = [f"## SKILL: {name}\n\n{content}" for name, content in skills.items()]
    return f"""
---
## LOADED SKILLS

Available skills: [{skill_names}]

**Priority Rule:** When the user's query involves stockouts, supply chain, POs, or
escalations — invoke the **Skill tool** with skill name `retail-stockout-prevention`
to execute that skill's 8-step decision logic BEFORE anything else.
The full skill content is pre-loaded below for your reference.

{chr(10).join(blocks)}
---
"""


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def _build_system_prompt(skills_prompt: str) -> str:
    data_path = str(DATA_DIR).replace("\\", "/")
    scripts_path = str(SCRIPTS_DIR).replace("\\", "/")
    computer_status = "*(enabled)*" if ENABLE_COMPUTER_TOOL else "*(disabled — set ENABLE_COMPUTER_TOOL=true to activate)*"

    return f"""
You are **Aria** — a highly capable general-purpose AI agent. You can research any topic,
answer any question, analyze data, run code, browse the web, and automate tasks.
You also carry a specialized retail supply chain skill for stockout and inventory scenarios.

---
## IDENTITY & CAPABILITIES

- Intelligent, curious, and direct. No domain limits. No disclaimers. Just answers.
- Handle ANY query: research, news, coding, data analysis, web browsing, reasoning.
- When a query involves retail stockouts / inventory / supply chain → apply the loaded skill.
- For all other queries → use WebSearch, Bash, WebFetch, and your knowledge.

---
## SKILL ACTIVATION RULE

Check if ANY loaded skill is relevant to the query:
- If YES → invoke that skill and follow its decision logic as the backbone of your reasoning.
- If NO → proceed with general tools (WebSearch, Bash, WebFetch, etc.).

Loaded skills: see LOADED SKILLS section below.

---
## HOW TO REASON AND RESPOND — MANDATORY FORMAT

**You must narrate every intermediate step AS YOU WORK.**
Show your reasoning, tool calls, and results inline — do not wait until the end.

Use this format for EVERY response, whether retail or general:

```
Step N: [Step Name]

🔧 [tool]: [what you ran / searched / fetched]

→ [What the result shows — key facts, numbers, quotes]

💡 [SKILL / KNOWLEDGE]: "[Relevant rule, tribal knowledge, or insight that applies]"

→ [Your conclusion from this step]
```

Then end with a summary block:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
[Key findings]

ACTIONS / RECOMMENDATIONS
[Numbered list]

[For retail: GUARDRAILS block with thresholds]

COMPLETE | N steps | N tool calls | N sources
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Rules for intermediate reasoning:**
- Label every tool call: `🔧 bash_tool:`, `🔧 web_search:`, `🔧 web_fetch:`, `🔧 skill:`
- Show results immediately after with `→`
- Apply relevant knowledge/skill rules with `💡 SKILL:` or `💡 KNOWLEDGE:`
- Draw a step conclusion with `→`
- Never skip steps silently — narrate everything
- For general queries: adapt step names to the topic (e.g. "Step 1: Understand the Question", "Step 2: Search for Current Data", "Step 3: Cross-reference Sources")
- For retail queries: follow the skill's 8-step framework exactly

---
## RETAIL DATA ACCESS (for supply chain queries)

Scripts live at: {scripts_path}
Excel data lives at: {data_path}

Available scripts (run with `python`):
- `scripts/read_data.py --sheet <name> [--filter col=val] [--cols a,b]`
  Short names are auto-mapped to actual Excel tabs — use these EXACT short names:
    inventory, purchase_order, purchase_order_line, sales_transaction,
    sales_line_item, order, order_line, return, daily_sales_summary,
    employee_schedule, store, warehouse, product, supplier, region,
    brand, category, customer, employee, department, promotion
  DO NOT run discovery commands — the mapping is already handled internally.
- `scripts/stockout_summary.py [--sku N] [--region N] [--threshold N]`
- `scripts/log_escalation.py --code E3 --severity critical --message "..." --action "..."`

---
## AVAILABLE TOOLS

| Tool | Purpose |
|------|---------|
| **WebSearch** | Search the web for current info, news, research, prices, events |
| **WebFetch** | Fetch and read a specific URL in full |
| **Bash** | Run Python, shell commands, data scripts, calculations |
| **Skill** | Invoke loaded skill decision logic |
| **mcp__desktop__computer_tool** | GUI automation on the virtual desktop — `screenshot`, `left_click`, `type`, `key`, `scroll` {computer_status}. Use this to visually browse websites, click buttons, fill forms, and see what's on screen. |

---
## EXECUTION RULES

- Work autonomously — no confirmations needed.
- Always show intermediate reasoning using the step format above.
- Chain tools logically: each step's output informs the next step.
- Cite all web sources at the end.
- For retail queries: always check if escalation rules (E1–E8) are triggered and log them.
- **GUI automation**: ONLY use `mcp__desktop__computer_tool` for screenshots, clicks, and typing. NEVER call `scrot`, `xdotool`, or `import` directly via Bash for GUI interaction — those run on a separate process and may fail. The computer_tool handles all display interaction correctly.
- **Display**: The virtual desktop runs on `DISPLAY=:1`. The computer_use tool is already configured for this — no need to specify it manually.
{skills_prompt}
"""


# ---------------------------------------------------------------------------
# Allowed tools
# ---------------------------------------------------------------------------

def _build_allowed_tools() -> List[str]:
    tools = ["Bash", "Read", "Write", "Edit", "Glob", "Grep",
             "Skill", "WebSearch", "WebFetch"]
    tools.extend(ALLOWED_MCP_TOOLS)
    return tools


# ---------------------------------------------------------------------------
# Message processor
# ---------------------------------------------------------------------------

def _msg_type(message: Any) -> str:
    t = getattr(message, "type", None) or message.__class__.__name__
    return str(t).lower()


async def _emit_screenshot(
    on_event: Optional[Callable],
    cid: str,
    label: str,
) -> None:
    """Take a scrot screenshot and emit it as a WebSocket event."""
    img = await _take_screenshot()
    if img and on_event:
        logger.info(f"[{cid}] SCREENSHOT sent to viewer ({label})")
        await on_event({"type": "screenshot", "image": img, "media_type": "image/png"})
    elif _DISPLAY:
        logger.warning(f"[{cid}] SCREENSHOT failed ({label}) — scrot returned nothing")


async def _process_message(
    message: Any,
    on_event: Optional[Callable],
    cid: str,
    counters: Dict[str, int],
) -> None:
    # ── Handle raw dicts (ToolResultBlock.content items are list[dict], not objects)
    if isinstance(message, dict):
        if message.get("type") == "image":
            source = message.get("source", {})
            img_data   = source.get("data", "")
            media_type = source.get("media_type", "image/png")
            if img_data and on_event:
                logger.info(f"[{cid}] SCREENSHOT from Computer tool ({len(img_data)} chars b64)")
                await on_event({"type": "screenshot", "image": img_data, "media_type": media_type})
        return

    mt = _msg_type(message)

    if "text" in mt:
        text = getattr(message, "text", str(message))
        logger.info(f"[{cid}] TEXT: {text[:100]}")
        if on_event:
            await on_event({"type": "text", "text": text})

    elif "tooluse" in mt or "tool_use" in mt:
        name = getattr(message, "name", "unknown")
        inp  = getattr(message, "input", {})
        counters["tools"] += 1
        logger.info(f"[{cid}] TOOL: {name} | {json.dumps(inp)[:100]}")

        if name.lower() == "skill":
            counters["skills"] += 1
            sname = inp.get("skill", "unknown")
            logger.info(f"[{cid}] SKILL: {sname}")
            _log_to_display(f"⚡ SKILL: {sname}")
            if on_event:
                await on_event({"type": "skill_start", "skill": sname, "input": inp})
                await on_event({"type": "activity_log", "text": f"⚡ SKILL: {sname}"})
        elif name.lower() == "bash":
            cmd = inp.get("command", "")
            _log_to_display(f"🔧 BASH  $ {cmd[:300]}")
            if on_event:
                await on_event({"type": "tool_use", "tool": name, "input": inp})
                await on_event({"type": "activity_log", "text": f"🔧 BASH\n  $ {cmd[:300]}"})
        elif name.lower() == "websearch":
            q = inp.get("query", "")
            _log_to_display(f"🔍 WEBSEARCH: {q[:120]}")
            if on_event:
                await on_event({"type": "tool_use", "tool": name, "input": inp})
                await on_event({"type": "activity_log", "text": f"🔍 WEBSEARCH: {q[:120]}"})
        elif name.lower() == "webfetch":
            url = inp.get("url", "")
            _log_to_display(f"🌐 WEBFETCH: {url[:120]}")
            if on_event:
                await on_event({"type": "tool_use", "tool": name, "input": inp})
                await on_event({"type": "activity_log", "text": f"🌐 WEBFETCH: {url[:120]}"})
        elif "computer_tool" in name.lower():
            action = inp.get("action", "")
            detail = inp.get("text") or inp.get("coordinate") or inp.get("key") or ""
            _log_to_display(f"🖥  COMPUTER: {action} {str(detail)[:80]}")
            if on_event:
                await on_event({"type": "tool_use", "tool": name, "input": inp})
                await on_event({"type": "activity_log", "text": f"🖥  COMPUTER: {action} {str(detail)[:80]}"})
        else:
            _log_to_display(f"🛠  {name}: {json.dumps(inp)[:120]}")
            if on_event:
                await on_event({"type": "tool_use", "tool": name, "input": inp})
                await on_event({"type": "activity_log", "text": f"🛠  {name}: {json.dumps(inp)[:120]}"})

        # ── Open URL in Chromium so it's visible in the video feed ──────────
        if name.lower() == "websearch":
            q = inp.get("query", "")
            await _open_url_in_chromium(f"https://www.google.com/search?q={q.replace(' ', '+')}")
        elif name.lower() == "webfetch":
            await _open_url_in_chromium(inp.get("url", ""))

    elif "toolresult" in mt or "tool_result" in mt:
        # ToolResultBlock.content is str | list[dict] | None
        # Computer tool returns image dicts here — handled by the dict branch above
        content = getattr(message, "content", [])
        if isinstance(content, list):
            for block in content:
                await _process_message(block, on_event, cid, counters)

    elif "thinking" in mt:
        thinking_text = getattr(message, "thinking", None) or getattr(message, "text", None)
        if on_event:
            await on_event({"type": "thinking", "text": thinking_text or ""})

    elif "assistant" in mt or "user" in mt:
        content = getattr(message, "content", [])
        if isinstance(content, list):
            for block in content:
                await _process_message(block, on_event, cid, counters)

    elif "result" in mt:
        counters["turns"] += 1
        result_text = getattr(message, "result", getattr(message, "text", str(message)))
        logger.info(f"[{cid}] RESULT turn={counters['turns']}: {str(result_text)[:100]}")
        # Write result preview to xterm log (first 400 chars)
        result_preview = str(result_text)[:300].replace("\n", " ").strip()
        _log_to_display(f"→ {result_preview}")
        _log_to_display("─" * 60)
        if on_event:
            await on_event({"type": "result", "text": str(result_text)})
            await on_event({"type": "activity_log", "text": f"→ {result_preview}\n{'─'*60}"})


# ---------------------------------------------------------------------------
# run_agent
# ---------------------------------------------------------------------------

async def run_agent(
    query_text: str,
    session_id: Optional[str] = None,
    on_event: Optional[Callable] = None,
) -> Dict[str, Any]:
    """
    Run the Retail Stockout Prevention Agent.

    Args:
        query_text:  User question or alert description.
        session_id:  Optional session ID (auto-generated if omitted).
        on_event:    Optional async callback receiving event dicts.

    Returns:
        {"session_id", "response", "turns", "tools_used", "skills_invoked", "elapsed_seconds"}
    """
    if not session_id:
        session_id = f"session-{uuid.uuid4().hex[:8]}"
    cid = f"RETAIL-{uuid.uuid4().hex[:6].upper()}"

    logger.info(f"[{cid}] session={session_id} query={query_text[:80]}")

    start = time.time()
    counters: Dict[str, int] = {"turns": 0, "tools": 0, "skills": 0}
    final_response = ""

    skills = _load_all_skills()
    logger.info(f"[{cid}] Skills loaded: {list(skills.keys())}")

    system_prompt = _build_system_prompt(_build_skills_prompt(skills))
    allowed_tools = _build_allowed_tools()

    options = ClaudeAgentOptions(
        model=CLAUDE_MODEL,
        system_prompt=system_prompt,
        allowed_tools=allowed_tools,
        mcp_servers={
            "retail-tools": AGENT_MCP_SERVER,
            **( {"desktop": DESKTOP_MCP_SERVER} if DESKTOP_MCP_SERVER else {} ),
        },
        permission_mode=PERMISSION_MODE,
        max_turns=MAX_TURNS,
    )

    _log_to_display("=" * 60)
    _log_to_display(f"QUERY: {query_text}")
    _log_to_display(f"SKILLS: {', '.join(skills.keys()) or 'none'}")
    _log_to_display("=" * 60)

    if on_event:
        await on_event({"type": "activity_log",
                        "text": f"{'='*60}\nQUERY: {query_text}\nSKILLS: {', '.join(skills.keys()) or 'none'}\n{'='*60}"})
        await on_event({
            "type": "agent_started",
            "session_id": session_id,
            "query": query_text,
            "skills": list(skills.keys()),
        })

    agent_error: Optional[str] = None
    try:
        async for message in query(prompt=query_text, options=options):
            await _process_message(message, on_event, cid, counters)
            mt = _msg_type(message)
            if "result" in mt:
                # ResultMessage may carry is_error=True when the last tool failed.
                # That is a tool-level outcome, not a fatal crash — capture the text
                # but only treat it as a hard error if there's no partial response yet.
                is_err = getattr(message, "is_error", False)
                result_val = getattr(message, "result", getattr(message, "text", None))
                if result_val is not None:
                    final_response = str(result_val)
                if is_err and not final_response:
                    agent_error = str(result_val)
                    logger.warning(f"[{cid}] ResultMessage is_error=True: {agent_error[:120]}")
    except BaseException as exc:
        # Unwrap ExceptionGroup (Python 3.11+ / anyio TaskGroup errors)
        inner = exc
        if hasattr(exc, "exceptions") and exc.exceptions:
            inner = exc.exceptions[0]
        err_msg = str(inner)

        # "Command failed with exit code N" is a tool failure, not a Python crash.
        # Log it but don't surface it as a fatal error if we already have a response.
        if "exit code" in err_msg.lower() or "command failed" in err_msg.lower():
            logger.warning(f"[{cid}] Tool exited non-zero (non-fatal): {err_msg[:120]}")
            if not final_response:
                agent_error = err_msg
                if on_event:
                    await on_event({"type": "error", "error": agent_error})
        else:
            agent_error = err_msg
            logger.error(f"[{cid}] Agent error: {agent_error}")
            if on_event:
                await on_event({"type": "error", "error": agent_error})

    if agent_error:
        return {
            "session_id": session_id,
            "response": f"Agent error: {agent_error}",
            "turns": counters["turns"],
            "tools_used": counters["tools"],
            "skills_invoked": counters["skills"],
            "elapsed_seconds": round(time.time() - start, 2),
            "error": agent_error,
        }

    elapsed = round(time.time() - start, 2)
    logger.info(
        f"[{cid}] Done {elapsed}s | turns={counters['turns']} "
        f"tools={counters['tools']} skills={counters['skills']}"
    )

    if on_event:
        await on_event({
            "type": "completed",
            "session_id": session_id,
            "elapsed_seconds": elapsed,
            "turns": counters["turns"],
            "tools_used": counters["tools"],
            "skills_invoked": counters["skills"],
        })

    return {
        "session_id": session_id,
        "response": final_response,
        "turns": counters["turns"],
        "tools_used": counters["tools"],
        "skills_invoked": counters["skills"],
        "elapsed_seconds": elapsed,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Retail Stockout Prevention Agent")
    parser.add_argument("query", nargs="?", help="Query text")
    parser.add_argument("--query", dest="query_flag", help="Query via --query flag")
    args = parser.parse_args()

    user_query = args.query or args.query_flag or (
        "What can you help me with? Give me a brief overview of your capabilities."
    )

    async def _print_event(event: Dict[str, Any]) -> None:
        etype = event.get("type", "")
        if etype == "text":
            print(f"\n[AGENT] {event['text']}")
        elif etype == "tool_use":
            print(f"  -> Tool: {event['tool']}")
        elif etype == "skill_start":
            print(f"  -> Skill invoked: {event['skill']}")
        elif etype == "thinking":
            print("  ~ Thinking...")
        elif etype == "error":
            print(f"\n[ERROR] {event['error']}")
        elif etype == "completed":
            print(
                f"\n[DONE] {event['elapsed_seconds']}s | "
                f"turns={event['turns']} tools={event['tools_used']} "
                f"skills={event['skills_invoked']}"
            )

    result = asyncio.run(run_agent(user_query, on_event=_print_event))
    print("\n" + "=" * 60)
    print("FINAL RESPONSE:")
    print("=" * 60)
    print(result.get("response", "(no response captured)"))
