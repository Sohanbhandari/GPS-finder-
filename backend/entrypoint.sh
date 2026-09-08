#!/bin/sh
set -e

echo "=== System Startup: Waiting for PostgreSQL ==="
python -c "
import asyncio
import os
import sys
import asyncpg

async def check_db():
    db_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@postgres:5432/gps_tracker')
    clean_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    if clean_url.startswith('postgres://'):
        clean_url = clean_url.replace('postgres://', 'postgresql://', 1)
    for attempt in range(30):
        try:
            conn = await asyncpg.connect(clean_url)
            await conn.close()
            print('Database connection established successfully.')
            return True
        except Exception as e:
            print(f'Database connection pending (attempt {attempt+1}/30): {e}')
            await asyncio.sleep(1)
    return False

if not asyncio.run(check_db()):
    print('Failed to connect to database within timeout period.')
    sys.exit(1)
"

echo "=== Executing Database Migrations (Alembic Upgrade Head) ==="
alembic upgrade head

echo "=== Seeding Initial System Data ==="
python -m app.db.seed

echo "=== Starting FastAPI Server (Uvicorn) ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
