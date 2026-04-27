#!/usr/bin/env bash
# Start the KBOM demo: FastAPI backend + Next.js frontend.
#
# Usage:
#   ./start-demo.sh         # starts both servers, prints URLs, leaves them running
#   ./start-demo.sh --tail  # also tails the logs
#
# Stop with: ./stop-demo.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

API_PORT=8765
WEB_PORT=3737
LOG_DIR="$ROOT_DIR/.logs"
mkdir -p "$LOG_DIR"

# --- 1. Stop any existing servers ---
echo "▸ Stopping any prior demo servers…"
lsof -ti:$API_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:$WEB_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1

# --- 2. Verify Python venv + dependencies ---
if [[ ! -d "$ROOT_DIR/.venv" ]]; then
  echo "▸ Creating Python venv (Python 3.12)…"
  python3.12 -m venv "$ROOT_DIR/.venv"
fi
"$ROOT_DIR/.venv/bin/pip" install --quiet --upgrade pip 2>/dev/null
"$ROOT_DIR/.venv/bin/pip" install --quiet \
  fastapi 'uvicorn[standard]' python-multipart \
  pdfplumber pymupdf openpyxl Pillow xlrd anthropic 2>&1 | tail -3 || true

# --- 3. Verify Node deps ---
if [[ ! -d "$ROOT_DIR/web/node_modules" ]]; then
  echo "▸ Installing Node deps…"
  (cd "$ROOT_DIR/web" && npm install --silent)
fi

# --- 4. Start FastAPI ---
echo "▸ Starting FastAPI on :$API_PORT…"
nohup "$ROOT_DIR/.venv/bin/python" -m uvicorn server.main:app \
  --host 127.0.0.1 --port $API_PORT --reload \
  >"$LOG_DIR/api.log" 2>&1 &
API_PID=$!
echo $API_PID > "$LOG_DIR/api.pid"

# --- 5. Start Next.js ---
echo "▸ Starting Next.js on :$WEB_PORT…"
(cd "$ROOT_DIR/web" && nohup npm run dev -- --port $WEB_PORT \
  >"$LOG_DIR/web.log" 2>&1 &
echo $! > "$LOG_DIR/web.pid")

# --- 6. Wait for both to come up ---
echo -n "▸ Waiting for servers"
for i in $(seq 1 30); do
  if curl -sS -o /dev/null -w "%{http_code}" "http://localhost:$API_PORT/api/health" 2>/dev/null | grep -q 200; then
    if curl -sS -o /dev/null -w "%{http_code}" "http://localhost:$WEB_PORT/" 2>/dev/null | grep -q 200; then
      echo " ✓"
      break
    fi
  fi
  echo -n "."
  sleep 1
done

# --- 7. Print URLs ---
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  KBOM demo is running"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Frontend (open this):  http://localhost:$WEB_PORT"
echo "  API:                   http://localhost:$API_PORT"
echo "  Logs:                  tail -f .logs/api.log .logs/web.log"
echo ""
echo "  Click 'Use sample' on the home page to load 화성태안3 A2BL."
echo ""
echo "  Stop with: ./stop-demo.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ "${1:-}" == "--tail" ]]; then
  tail -f "$LOG_DIR/api.log" "$LOG_DIR/web.log"
fi
