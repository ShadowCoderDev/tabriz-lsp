#!/bin/bash
set -e

echo "Waiting for MongoDB to be ready..."

# Wait for MongoDB to be available (max 30 seconds)
counter=0
until nc -z "$MONGODB_HOST" "$MONGODB_PORT" || [ $counter -ge 30 ]; do
  echo "MongoDB is unavailable - sleeping"
  sleep 1
  counter=$((counter + 1))
done

if [ $counter -ge 30 ]; then
  echo "Warning: Could not connect to MongoDB after 30 seconds"
  echo "Continuing anyway in case command doesn't need database..."
else
  echo "MongoDB is up - executing command"
fi

# Check if we're running a command that shouldn't trigger collectstatic
SKIP_SETUP=false
if [ "$1" = "python" ] && [ "$2" = "manage.py" ]; then
  case "$3" in
    shell|dbshell|test|createsuperuser)
      SKIP_SETUP=true
      ;;
  esac
fi

# Collect static files only if not skipped
if [ "$SKIP_SETUP" = false ]; then
  # Collect static files (non-blocking)
  echo "Collecting static files..."
  python manage.py collectstatic --noinput 2>&1 || echo "Note: Static files collection skipped or failed (this is OK for development)"
fi

# Execute the command passed as arguments
exec "$@"
