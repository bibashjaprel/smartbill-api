#!/usr/bin/env sh
set -eu

echo "[entrypoint] Waiting for database at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."
python - <<'PY'
import os
import socket
import time

host = os.getenv("POSTGRES_HOST", "db")
port = int(os.getenv("POSTGRES_PORT", "5432"))
for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print("[entrypoint] Database is reachable")
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit("[entrypoint] Database is not reachable after 60s")
PY

echo "[entrypoint] Running alembic migrations..."
alembic upgrade head

echo "[entrypoint] Starting API..."
exec "$@"
