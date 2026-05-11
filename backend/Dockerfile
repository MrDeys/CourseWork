FROM python:3.11-slim

# 1. Системные зависимости для базы данных
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Установка библиотек
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# 3. Копируем код
COPY . .

# 4. Настройки окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 5. Запуск сервера (Render сам подставит $PORT)
CMD gunicorn --bind 0.0.0.0:$PORT run:app --timeout 120 --workers 1