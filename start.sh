#!/bin/sh

echo "Waiting for database to be ready..."
sleep 5

echo "Running database migrations..."
alembic upgrade head

echo "Starting Budget Planning Bot..."
python3 -m src.run