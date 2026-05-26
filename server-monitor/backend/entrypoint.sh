#!/bin/sh
set -e

python manage.py migrate --noinput

if [ "$1" = "web" ]; then
  python manage.py collectstatic --noinput
  exec gunicorn server_monitor.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${WEB_CONCURRENCY:-1}" \
    --timeout 90
fi

if [ "$1" = "monitor" ]; then
  exec python manage.py monitor_scheduler
fi

exec "$@"
