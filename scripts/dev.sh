#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

find_free_port() {
  python3 - "$1" <<'PY'
import socket
import sys

start = int(sys.argv[1])

for port in range(start, start + 20):
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            continue
        print(port)
        raise SystemExit(0)

raise SystemExit(1)
PY
}

mkdir -p var/media

if [ ! -f .env ]; then
  cp .env.example .env
fi

if [ ! -d node_modules ] || [ ! -d frontend/node_modules ]; then
  echo "Installing frontend dependencies..."
  pnpm install
fi

if [ ! -x .venv/bin/python ]; then
  echo "Creating backend virtualenv..."
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -e ./backend pytest pytest-django ruff mypy
fi

cleanup() {
  if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

BACKEND_PORT="$(find_free_port 8000)"

echo "Starting backend on http://localhost:${BACKEND_PORT} ..."
.venv/bin/python backend/manage.py runserver "${BACKEND_PORT}" >/tmp/knowledge-keeper-backend.log 2>&1 &
BACKEND_PID=$!

sleep 2

if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo "Backend failed to start. Log:"
  cat /tmp/knowledge-keeper-backend.log
  exit 1
fi

echo "Starting frontend on http://localhost:3000 ..."
VITE_BACKEND_TARGET="http://localhost:${BACKEND_PORT}" pnpm --filter @knowledge-keeper/frontend dev
