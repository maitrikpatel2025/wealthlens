#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting backend server..."
cd "$ROOT_DIR/app/server"
poetry run python main.py &
BACKEND_PID=$!

echo "Starting frontend dev server..."
cd "$ROOT_DIR/app/client"
pnpm dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID (port 8000)"
echo "Frontend PID: $FRONTEND_PID (port 3000)"

wait
