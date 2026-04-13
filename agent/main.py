"""
main.py - FastAPI Server for Aria Agent

Flow for every request
-----------------------
1. Receive { "query": "...", "session_id": "abc123" }
2. Download skills from S3:  s3://qdojo-skill-files-costco/skills/abc123/
3. Save skills to local:     .claude/skills/{skill_name}/...
4. Run agent (loads skills from .claude/skills/, applies matching ones)
5. Stream events back over WebSocket until done

Endpoints
---------
POST  /query   - Synchronous (blocks until agent finishes)
WS    /ws      - Real-time streaming
GET   /health  - Health check

Start:
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import asyncio
import json
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict

# ── Load .env with explicit path (works even inside uvicorn --reload child) ─
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

if not os.environ.get("ANTHROPIC_API_KEY"):
    raise RuntimeError(
        "ANTHROPIC_API_KEY not set. Add to agent/.env:  ANTHROPIC_API_KEY=sk-ant-..."
    )

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from pydantic import BaseModel

from agent import run_agent
from skill_loader import load_skills_for_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(name)s] %(message)s",
)
logger = logging.getLogger("MAIN")

# Thread pool — each agent call runs in its own thread with a fresh asyncio
# event loop to avoid the Windows ProactorEventLoop + SDK subprocess conflict.
_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="agent")


# ---------------------------------------------------------------------------
# Core: load skills from S3, then run agent in isolated thread
# ---------------------------------------------------------------------------

def _load_and_run(
    query_text: str,
    session_id: str,
    event_queue: asyncio.Queue,
    caller_loop: asyncio.AbstractEventLoop,
) -> Dict[str, Any]:
    """
    Runs inside a ThreadPoolExecutor worker (blocking context).

    Step 1 — Download skills from S3 for this session_id.
    Step 2 — Run the agent (fresh asyncio loop, avoids uvicorn conflict).
    Step 3 — Emit final_response, then sentinel to signal done.
    """

    def _put(event: Dict[str, Any]) -> None:
        caller_loop.call_soon_threadsafe(event_queue.put_nowait, event)

    # ── Step 1: S3 skill loading ────────────────────────────────────────────
    _put({"type": "skill_loading", "session_id": session_id,
          "message": f"Loading skills from S3 for session: {session_id}"})

    # Pass _put as the emit callback so every loader log line streams to Postman
    skill_names = load_skills_for_session(session_id, emit=_put)

    logger.info(f"[{session_id}] Skills ready: {skill_names}")
    _put({"type": "skills_ready", "skills": skill_names, "session_id": session_id,
          "message": f"{len(skill_names)} skill(s) active — starting agent"})

    # ── Step 2: Run agent ──────────────────────────────────────────────────
    async def _on_event(event: Dict[str, Any]) -> None:
        _put(event)

    result = asyncio.run(
        run_agent(query_text=query_text, session_id=session_id, on_event=_on_event)
    )

    # ── Step 3: Emit final_response before signalling done ─────────────────
    _put({
        "type": "final_response",
        "session_id":      session_id,
        "response":        result.get("response", ""),
        "turns":           result.get("turns", 0),
        "tools_used":      result.get("tools_used", 0),
        "skills_invoked":  result.get("skills_invoked", 0),
        "elapsed_seconds": result.get("elapsed_seconds", 0),
        "skills_loaded":   skill_names,
        "error":           result.get("error"),          # None if clean run
    })

    caller_loop.call_soon_threadsafe(event_queue.put_nowait, None)   # sentinel
    return result


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Aria Agent",
    description="General-purpose AI agent with S3-loaded skills",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve two-pane viewer UI
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# Serve HLS stream files (produced by ffmpeg in /tmp/hls/)
_hls_dir = Path("/tmp/hls")
_hls_dir.mkdir(parents=True, exist_ok=True)
app.mount("/hls", StaticFiles(directory=str(_hls_dir)), name="hls")


@app.get("/")
async def root():
    return RedirectResponse(url="/static/viewer.html")


@app.get("/download-recording")
async def download_recording():
    """Download the MP4 recording of the current session."""
    mp4_path = Path("/tmp/recordings/session.mp4")
    if not mp4_path.exists():
        raise HTTPException(status_code=404, detail="No recording available yet")
    return FileResponse(
        path=str(mp4_path),
        media_type="video/mp4",
        filename="aria-agent-session.mp4",
    )


# ---------------------------------------------------------------------------
# REST  POST /query
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None


@app.post("/query")
async def query_endpoint(request: QueryRequest) -> Dict[str, Any]:
    """
    Run agent synchronously (no streaming). Returns full result JSON.

    Example:
        curl -X POST http://localhost:8000/query \\
             -H "Content-Type: application/json" \\
             -d '{"query": "Check stockout risk for region 3", "session_id": "abc123"}'
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")

    session_id = request.session_id or f"rest-{uuid.uuid4().hex[:8]}"
    logger.info(f"REST /query session={session_id}: {request.query[:60]}")

    loop = asyncio.get_event_loop()
    event_queue: asyncio.Queue = asyncio.Queue()

    future = loop.run_in_executor(
        _executor, _load_and_run, request.query, session_id, event_queue, loop
    )

    # Drain queue until sentinel
    while True:
        event = await event_queue.get()
        if event is None:
            break

    return await future


# ---------------------------------------------------------------------------
# WebSocket  WS /ws
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Stream agent events in real time.

    Client sends:   { "query": "...", "session_id": "abc123" }

    Server streams:
        { "type": "skill_loading",  "session_id": "abc123" }
        { "type": "skills_ready",   "skills": ["retail-stockout-prevention"], "session_id": "abc123" }
        { "type": "agent_started",  "session_id": "...", "query": "...", "skills": [...] }
        { "type": "thinking" }
        { "type": "tool_use",       "tool": "WebSearch", "input": {...} }
        { "type": "skill_start",    "skill": "retail-stockout-prevention" }
        { "type": "text",           "text": "Step 1: ..." }
        { "type": "result",         "text": "..." }
        { "type": "completed",      "elapsed_seconds": 45.2, "turns": 6, ... }
        { "type": "error",          "error": "..." }
        { "type": "done" }
    """
    await websocket.accept()
    logger.info("WebSocket connected")

    loop = asyncio.get_event_loop()

    try:
        while True:
            raw = await websocket.receive_text()

            # ── Parse incoming message ──────────────────────────────────────
            try:
                data = json.loads(raw)
                user_query = data.get("query", "").strip()
                session_id = data.get("session_id") or f"ws-{uuid.uuid4().hex[:8]}"
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "error": "Invalid JSON"})
                continue

            if not user_query:
                await websocket.send_json({"type": "error", "error": "query is required"})
                continue

            logger.info(f"WS session={session_id}: {user_query[:60]}")

            # ── Launch: S3 skill load → agent (in thread) ───────────────────
            event_queue: asyncio.Queue = asyncio.Queue()

            loop.run_in_executor(
                _executor, _load_and_run, user_query, session_id, event_queue, loop
            )

            # ── Stream events to WebSocket ──────────────────────────────────
            while True:
                event = await event_queue.get()
                if event is None:          # sentinel = agent finished
                    break
                try:
                    await websocket.send_json(event)
                except Exception:
                    break

            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as exc:
        logger.exception(f"WebSocket error: {exc}")
        try:
            await websocket.send_json({"type": "error", "error": str(exc)})
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "service": "aria-agent"}
