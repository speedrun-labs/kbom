#!/usr/bin/env bash
# Stop the KBOM demo servers.

set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/.logs"

API_PORT=8765
WEB_PORT=3737

echo "▸ Stopping API on :$API_PORT…"
lsof -ti:$API_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true

echo "▸ Stopping Next.js on :$WEB_PORT…"
lsof -ti:$WEB_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true

rm -f "$LOG_DIR/api.pid" "$LOG_DIR/web.pid" 2>/dev/null

echo "✓ Stopped"
