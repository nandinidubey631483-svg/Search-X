#!/bin/sh
set -e

echo "==> [SearchX] Starting corpus seeding and database initialization..."
python3 scripts/seed_corpus.py

PORT_TO_USE="${PORT:-8000}"
echo "==> [SearchX] Starting Uvicorn server on port $PORT_TO_USE..."
exec python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT_TO_USE"
