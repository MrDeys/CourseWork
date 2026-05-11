# Этап 1: Сборка
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Собираем билд
RUN npm run build

# Этап 2: Раздача статики через Nginx
FROM nginx:stable-alpine
COPY --from=build /app/build /usr/share/nginx/html
# Добавь эту строку:
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]