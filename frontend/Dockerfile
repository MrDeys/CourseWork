# === ЭТАП 1: Сборка (Build) ===
FROM node:18-alpine as build

WORKDIR /app

# Копируем package.json и ставим зависимости
COPY package*.json ./
RUN npm install

# Копируем весь код фронтенда
COPY . .

# Принудительно даем права и собираем проект
RUN chmod +x node_modules/.bin/craco
RUN npm run build


# === ЭТАП 2: Раздача (Serve) ===
FROM nginx:stable-alpine

# Копируем наш конфиг Nginx (для лечения 404)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем готовый билд из первого этапа в папку Nginx
COPY --from=build /app/build /usr/share/nginx/html

# Открываем 80 порт
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]