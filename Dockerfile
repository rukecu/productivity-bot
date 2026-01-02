FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаем non-root пользователя
RUN useradd -m -u 1000 worker
USER worker

# Запускаем приложение
CMD ["sh", "-c", "python bot.py & gunicorn web_app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --worker-class gthread"]
