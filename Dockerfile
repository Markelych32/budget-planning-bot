FROM python:3.11-alpine

WORKDIR /app

# Установка необходимых зависимостей
RUN apk add --no-cache gcc python3-dev postgresql-dev musl-dev

# Копирование и установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода и конфигурации
COPY src/ ./src/
COPY alembic.ini .
COPY start.sh .
COPY .env .

# Установка прав на выполнение скрипта запуска
RUN chmod +x ./start.sh

# Запуск скрипта при старте контейнера
CMD ["./start.sh"]