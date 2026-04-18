#!/bin/sh
set -e

# Migrations are handled by the dedicated 'migrate' service in docker-compose.
# This entrypoint only starts the application.

echo "Starting application..."
exec "$@"
