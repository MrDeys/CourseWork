FROM python:3.11-slim

# Устанавливаем системные зависимости + curl
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Создаем папку, куда soccerdata хочет положить библиотеку, и качаем её заранее
RUN mkdir -p /usr/local/lib/python3.11/site-packages/tls_requests/bin/
RUN curl -L https://github.com/bogdanfinn/tls-client/releases/download/v1.13.1/tls-client-xgo-1.13.1-linux-amd64.so -o /usr/local/lib/python3.11/site-packages/tls_requests/bin/tls-client-xgo-1.13.1-linux-amd64.so

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
# Важно: на Render для Docker-сервисов порт обычно 10000
CMD python -m gunicorn --bind 0.0.0.0:10000 run:app --timeout 120 --workers 1