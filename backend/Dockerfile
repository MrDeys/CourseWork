# Используем легкий образ Python
FROM python:3.11-slim

# Устанавливаем системные зависимости для psycopg2 и работы с сетью
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь код бэкенда
COPY . .

# Устанавливаем переменную окружения, чтобы Python видел папку src
ENV PYTHONPATH=/app

# Открываем порт
EXPOSE 5000

# Команда запуска (сначала инициализация БД, потом запуск приложения)
# Вместо python run.py
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app", "--timeout", "120"]