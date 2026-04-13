# ── Aria Agent — Docker Image ────────────────────────────────────────────────
# Port: 8000 = FastAPI agent + viewer UI + HLS video stream
#
# Build:  docker build -t costcodemoagent .
# Run:    docker run -p 8000:8000 --env-file agent/.env costcodemoagent

FROM python:3.11-slim-bookworm

# ── System packages ───────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        xvfb \
        chromium \
        chromium-driver \
        scrot \
        ffmpeg \
        xterm \
        xdotool \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user (Claude Code CLI refuses bypassPermissions as root) ─────────
RUN useradd -m -u 1000 appuser

WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
COPY agent/requirements.txt ./agent/requirements.txt
RUN pip install --no-cache-dir -r agent/requirements.txt

# ── Application code ──────────────────────────────────────────────────────────
COPY agent/ ./agent/

# ── Retail Excel data ─────────────────────────────────────────────────────────
COPY ["data/", "./data/"]

# ── Local skill definitions (S3 fallback) ────────────────────────────────────
COPY .claude/ ./.claude/

# ── Startup script ────────────────────────────────────────────────────────────
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# ── Ownership ─────────────────────────────────────────────────────────────────
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["/app/start.sh"]
