#!/bin/sh

echo "Waiting for database to be ready..."
sleep 5

# Запуск миграций
echo "Running database migrations..."
alembic upgrade head

# Запуск бота
echo "Starting Budget Planning Bot..."
python3 -m src.run