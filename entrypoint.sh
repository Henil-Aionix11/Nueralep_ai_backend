#!/bin/bash
set -e

# Show debug information
echo "Environment validation..."
# Check for essential database environment variables
if [ -z "$POSTGRES_DATABASE_HOST" ] || [ -z "$POSTGRES_DATABASE_USERNAME" ] || [ -z "$POSTGRES_DATABASE_PASSWORD" ] || [ -z "$POSTGRES_DATABASE_NAME" ]; then
  echo " ERROR: Required database environment variables are not set"
  echo "Required variables: POSTGRES_DATABASE_HOST, POSTGRES_DATABASE_USERNAME, POSTGRES_DATABASE_PASSWORD, POSTGRES_DATABASE_NAME"
  echo "Available environment variables:"
  env | sort
  exit 1
fi

# Apply migrations with better error handling
echo " Running database migrations..."
SQLALCHEMY_SILENCE_UBER_WARNING=1 python -m alembic upgrade head || {
  echo " Migration failed with error code $?"
  exit 1
}

# Mark migrations as completed
echo " Marking migrations as completed"
python -m alembic stamp head

echo " Starting application..."

# Start the application
exec python -m main
