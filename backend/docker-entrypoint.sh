#!/usr/bin/env sh
set -e

echo "Applying database migrations..."
python -m alembic upgrade head

if [ "${CALENDAR_SEED_ON_START:-false}" = "true" ]; then
  echo "Seeding database..."
  python scripts/seed.py
fi

exec "$@"
