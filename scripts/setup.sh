#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

pnpm install
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ./backend pytest pytest-django ruff mypy
mkdir -p var/media

if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "Setup complete."
