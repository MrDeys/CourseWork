FROM python:3.11-slim

# Устанавливаем зависимости и curl
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Трюк: устанавливаем soccerdata и tls-client заранее, чтобы создать папки
RUN pip install --upgrade pip
RUN pip install soccerdata tls-client tls-requests

# 2. Качаем библиотеку напрямую в ту папку, где её ищет Python в Linux
RUN mkdir -p /root/.local/share/tls_requests/bin/
RUN curl -L https://github.com/bogdanfinn/tls-client/releases/download/v1.13.1/tls-client-xgo-1.13.1-linux-amd64.so -o /root/.local/share/tls_requests/bin/tls-client-xgo-1.13.1-linux-amd64.so

# Копируем остальное
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
# Запускаем через модуль gunicorn
CMD python -m gunicorn --bind 0.0.0.0:10000 run:app --timeout 120 --workers 1