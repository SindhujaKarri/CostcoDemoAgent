# Aria Agent — Computer-Use AI with Live Video Viewer

A containerised AI agent built on the **Claude Agent SDK** that:
- Executes tasks using **Bash**, **WebSearch**, and the **Computer tool** (full GUI automation)
- Loads **skills** dynamically from S3 per session
- Streams a **live HLS video** of the virtual desktop to the browser
- Shows real-time **agent reasoning, tool calls, and thinking** in a two-pane viewer UI

---

## Architecture

```
Browser (two-pane viewer)
├── Left pane  — agent reasoning, tool calls, thinking, skill events
└── Right pane — live HLS video of virtual desktop (Xvfb + Chromium)
                 + activity log (every Bash/WebSearch command in sync)

Docker container
├── Xvfb        — virtual display :1 (1920x1080)
├── Chromium    — runs on virtual display (visible in video)
├── ffmpeg      — records Xvfb → HLS stream (/tmp/hls/) + MP4 (/tmp/recordings/)
└── FastAPI     — agent server + static UI + HLS file serving (port 8000)
```

**Endpoints**

| Path | Description |
|------|-------------|
| `GET /` | Redirects to viewer UI |
| `WS /ws` | WebSocket — send query, stream agent events |
| `POST /query` | REST — synchronous query, returns full result JSON |
| `GET /hls/stream.m3u8` | Live HLS video stream |
| `GET /download-recording` | Download MP4 of full session |
| `GET /health` | Health check |

---

## Skills

Skills are Markdown/JSON files stored in S3 and downloaded at query time. The agent loads skills matching the session ID before running.

**S3 structure:**
```
s3://<S3_SKILL_BUCKET>/<S3_SKILL_PREFIX>/<session_id>/<skill-name>/SKILL.md
```

Local fallback skills (for testing) live in `.claude/skills/`.

---

## Quick Start

### Prerequisites
- Docker
- An Anthropic API key
- AWS credentials with S3 read access (for skill loading)

### 1. Configure environment

```bash
cp agent/.env.example agent/.env
# Edit agent/.env and fill in your real values
```

`.env` fields:

```
ANTHROPIC_API_KEY=sk-ant-...
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-west-2
S3_SKILL_BUCKET=your-s3-bucket-name
S3_SKILL_PREFIX=skills
CLAUDE_MODEL=claude-sonnet-4-6
MAX_TURNS=40
PERMISSION_MODE=bypassPermissions
ENABLE_COMPUTER_TOOL=true
COMPUTER_DISPLAY_WIDTH=1920
COMPUTER_DISPLAY_HEIGHT=1080
```

### 2. Build and run

```bash
docker build -t aria-agent .
docker run -p 8000:8000 --env-file agent/.env aria-agent
```

### 3. Open the viewer

Navigate to `http://localhost:8000`

The right pane shows the live virtual desktop video within ~3 seconds of the container starting.

### 4. Send a query

Use the input box in the viewer, or call the API directly:

```bash
curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "Open Chromium, go to news.ycombinator.com and summarise the top 3 stories", "session_id": "demo-001"}'
```

Or connect via WebSocket:

```json
{ "query": "Search for supply chain news from 2025", "session_id": "demo-001" }
```

---

## WebSocket Event Reference

The agent streams typed events over `/ws`:

| `type` | Description |
|--------|-------------|
| `skill_loading` | Skills download started from S3 |
| `skills_ready` | Skills loaded, agent about to start |
| `agent_started` | Agent loop begins |
| `thinking` | Claude's internal reasoning (`text` field contains content) |
| `tool_use` | Tool call with name + input |
| `activity_log` | Lightweight log shown above the video |
| `skill_start` | A skill was invoked |
| `text` | Agent text output |
| `result` | Tool result preview |
| `final_response` | Complete answer with stats |
| `screenshot` | Screenshot captured (shown as left-pane card) |
| `error` | Error message |
| `done` | Session complete |

---

## Project Structure

```
.
├── Dockerfile
├── start.sh                   # Xvfb → Chromium → ffmpeg → uvicorn
├── agent/
│   ├── main.py                # FastAPI server (REST + WebSocket + HLS serving)
│   ├── agent.py               # Agent runner (Claude Agent SDK)
│   ├── skill_loader.py        # S3 skill downloader
│   ├── tools.py               # MCP tool definitions
│   ├── scripts/
│   │   ├── read_data.py       # Excel data reader
│   │   ├── stockout_summary.py
│   │   └── log_escalation.py
│   ├── static/
│   │   └── viewer.html        # Two-pane browser UI
│   ├── requirements.txt
│   └── .env.example
└── .claude/
    └── skills/                # Local skill definitions (S3 fallback)
```

---

## Security Notes

- `agent/.env` is excluded from both `.gitignore` and `.dockerignore` — **never commit it**
- The container runs as a non-root user (`appuser`, UID 1000) — required by the Claude Code CLI `bypassPermissions` mode
- For production, inject secrets via ECS task definition environment variables or AWS Secrets Manager, not an `.env` file

---

## Requirements

Python packages (`agent/requirements.txt`):

```
anthropic
claude-agent-sdk
fastapi
uvicorn[standard]
pandas
openpyxl
boto3
python-dotenv
pydantic
requests
aiofiles
```

System packages (installed in Dockerfile):

```
xvfb  chromium  chromium-driver  scrot  ffmpeg  xterm
```
