#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."

# Wait for PostgreSQL to be available (max 30 seconds)
counter=0
until nc -z "$DB_HOST" "$DB_PORT" || [ $counter -ge 30 ]; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
  counter=$((counter + 1))
done

if [ $counter -ge 30 ]; then
  echo "Warning: Could not connect to PostgreSQL after 30 seconds"
  echo "Continuing anyway in case command doesn't need database..."
else
  echo "PostgreSQL is up - executing command"
fi

# Check if we're running a command that shouldn't trigger migrations/collectstatic
SKIP_SETUP=false
if [ "$1" = "python" ] && [ "$2" = "manage.py" ]; then
  case "$3" in
    makemigrations|shell|dbshell|showmigrations|sqlmigrate|migrate_squash|test|createcachetable)
      SKIP_SETUP=true
      ;;
  esac
fi

# Run migrations and collectstatic only if not skipped
if [ "$SKIP_SETUP" = false ]; then
  # Collect static files (non-blocking)
  echo "Collecting static files..."
  python manage.py collectstatic --noinput 2>&1 || echo "Note: Static files collection skipped or failed (this is OK for development)"

  # Run migrations (non-blocking - will fail gracefully if tables don't exist yet)
  echo "Running database migrations..."
  python manage.py migrate --noinput 2>&1 || echo "Note: Migrations skipped or failed (run 'makemigrations' first if needed)"
fi

# Execute the command passed as arguments
exec "$@"
