#!/usr/bin/env bash
# Serve the Lumi Codebase Wiki app on http://localhost:8000/app/
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${PORT:-8000}"
echo "Lumi Codebase Wiki  →  http://localhost:${PORT}/app/"
exec python3 -m http.server "${PORT}"
