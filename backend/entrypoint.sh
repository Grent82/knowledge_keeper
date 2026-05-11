#!/bin/bash
set -e

echo "==> Waiting for database..."
python backend/manage.py wait_for_db 2>/dev/null || true

echo "==> Running migrations..."
python backend/manage.py migrate --noinput

if [ "${DJANGO_COLLECT_STATIC:-false}" = "true" ]; then
    echo "==> Collecting static files..."
    python backend/manage.py collectstatic --noinput
fi

echo "==> Starting: $*"
exec "$@"
