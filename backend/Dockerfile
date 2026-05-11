FROM python:3.11-slim

# 1. Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Сначала ставим основные тяжелые библиотеки
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# 3. Решаем проблему с TLS библиотекой для soccerdata
# Мы создаем папку и качаем файл ТУДА, где библиотека его ищет в Linux
#RUN mkdir -p /root/.local/share/tls_requests/bin/
#RUN curl -L https://github.com/bogdanfinn/tls-client/releases/download/v1.13.1/tls-client-xgo-1.13.1-linux-amd64.so -o /root/.local/share/tls_requests/bin/tls-client-xgo-1.13.1-linux-amd64.so
# Даем права на выполнение этого файла
RUN chmod +x /root/.local/share/tls_requests/bin/tls-client-xgo-1.13.1-linux-amd64.so

# 4. Копируем код
COPY . .

ENV PYTHONPATH=/app
ENV PORT=10000

# Запускаем сервер
CMD python -m gunicorn --bind 0.0.0.0:$PORT run:app --timeout 120 --workers 1