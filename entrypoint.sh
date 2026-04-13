#!/bin/sh
set -e

echo ">>> Starte Alembic-Migrationen..."
alembic upgrade head

echo ">>> Starte Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
