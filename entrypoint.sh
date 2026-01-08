#!/bin/sh

# Verify if database is ready (optional, or rely on depends_on / health check)
# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Collect static files
echo "Collect static files"
python manage.py collectstatic --noinput

# Start server
echo "Starting server"
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000
