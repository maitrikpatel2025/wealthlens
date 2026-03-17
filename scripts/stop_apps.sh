#!/usr/bin/env bash
set -euo pipefail

echo "Stopping backend (port 8000)..."
lsof -ti:8000 | xargs kill -9 2>/dev/null && echo "  Stopped." || echo "  Not running."

echo "Stopping frontend (port 3000)..."
lsof -ti:3000 | xargs kill -9 2>/dev/null && echo "  Stopped." || echo "  Not running."
