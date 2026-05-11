FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# СКАЧИВАЕМ БИБЛИОТЕКУ TLS ЗАРАНЕЕ (самый надежный способ)
RUN mkdir -p /root/.local/share/tls_requests/bin/ && \
    curl -L https://github.com/bogdanfinn/tls-client/releases/download/v1.13.1/tls-client-xgo-1.13.1-linux-amd64.so -o /root/.local/share/tls_requests/bin/tls-client-linux-amd64-v1.13.1.so && \
    chmod +x /root/.local/share/tls_requests/bin/tls-client-linux-amd64-v1.13.1.so

COPY . .

ENV PYTHONPATH=/app
ENV PORT=10000

CMD gunicorn --bind 0.0.0.0:$PORT run:app --timeout 120 --workers 1