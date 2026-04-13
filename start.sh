#!/bin/bash
# ── Aria Agent Startup Script ─────────────────────────────────────────────────
# Launches: Xvfb → Chromium → ffmpeg (HLS + MP4) → uvicorn

set -e

DISPLAY_NUM=:1
SCREEN_RES="1920x1080x24"
HLS_DIR="/tmp/hls"
REC_DIR="/tmp/recordings"

echo "=========================================================="
echo "  ARIA AGENT — STARTING"
echo "=========================================================="

# ── 1. Virtual display ────────────────────────────────────────────────────────
echo "[1/4] Starting virtual display (Xvfb $DISPLAY_NUM $SCREEN_RES)..."
Xvfb $DISPLAY_NUM -screen 0 $SCREEN_RES -ac +extension GLX +render -noreset &
XVFB_PID=$!
export DISPLAY=$DISPLAY_NUM
sleep 1
echo "      Display ready: DISPLAY=$DISPLAY"

# ── 2. Chromium — full display (video shows only browser, log is in HTML) ─────
echo "[2/4] Launching Chromium on virtual display..."
chromium \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --disable-software-rasterizer \
    --window-size=1920,1080 \
    --start-maximized \
    --display=$DISPLAY_NUM \
    about:blank &
CHROMIUM_PID=$!
sleep 2
echo "      Chromium ready (full display)"

# ── 3. ffmpeg: record display → HLS stream + MP4 file ─────────────────────────
echo "[3/4] Starting ffmpeg (HLS stream + MP4 recording)..."
mkdir -p $HLS_DIR $REC_DIR

ffmpeg \
    -f x11grab \
    -r 15 \
    -s 1920x1080 \
    -i $DISPLAY_NUM \
    -c:v libx264 \
    -preset ultrafast \
    -tune zerolatency \
    -pix_fmt yuv420p \
    -g 15 \
    -keyint_min 15 \
    -sc_threshold 0 \
    -f hls \
        -hls_time 1 \
        -hls_list_size 6 \
        -hls_flags delete_segments+append_list+omit_endlist \
        $HLS_DIR/stream.m3u8 \
    -c:v libx264 \
    -preset ultrafast \
    -pix_fmt yuv420p \
    $REC_DIR/session.mp4 \
    -loglevel warning &
FFMPEG_PID=$!
sleep 3
echo "      ffmpeg recording — HLS: $HLS_DIR/stream.m3u8 | MP4: $REC_DIR/session.mp4"

# ── 4. FastAPI agent server ───────────────────────────────────────────────────
echo "[4/4] Starting Aria Agent (uvicorn port 8000)..."
echo "=========================================================="
echo "  Viewer UI   : http://localhost:8000"
echo "  Agent WS    : http://localhost:8000/ws"
echo "  HLS stream  : http://localhost:8000/hls/stream.m3u8"
echo "  MP4 download: http://localhost:8000/download-recording"
echo "=========================================================="

cd /app/agent
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
