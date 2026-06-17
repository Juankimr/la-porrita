#!/bin/bash
set -e

# Use persistent DB in /data only when running in Docker (mounted volume)
if [ -d /data ]; then
  export DATABASE_PATH="/data/db.sqlite3"
fi

echo "Running migrations..."
.venv/bin/python manage.py migrate --noinput

echo "Creating superuser..."
.venv/bin/python manage.py shell -c "
import os
from django.contrib.auth.models import User

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@porrita.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'Superuser created: {username}')
else:
    print(f'Superuser already exists: {username}')
"

# Seed teams and matches from API
if [ -n "$FOOTBALL_DATA_TOKEN" ]; then
  echo "Syncing football data..."
  .venv/bin/python manage.py sync_football_data
else
  echo "FOOTBALL_DATA_TOKEN not set, skipping sync"
fi

echo "Starting server..."
exec "$@"
