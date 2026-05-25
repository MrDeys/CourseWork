ВКР по теме: "РАЗРАБОТКА ПРИЛОЖЕНИЯ ДЛЯ ИНТЕЛЛЕКТУАЛЬНОГО АНАЛИЗА И ПРОГНОЗИРОВАНИЯ СТАТИСТИЧЕСКИХ ПО-КАЗАТЕЛЕЙ ФУТБОЛЬНЫХ МАТЧЕЙ"

Запуск:
..\CourseWork> python backend/run.py

..\CourseWork\frontend>install start // если первый раз
..\CourseWork\frontend>npm start

Запуск с нуля:

pip install -r requirements.txt

..\GraduateWork> python backend/src/database/tables.py // создание таблицы в БД
..\GraduateWork> python backend/src/scripts/loading_soccerdata.py // парсинг данных с сайтов в БД
..\GraduateWork> python backend/src/scripts/find_team_mappings.py // объединение имён с разных источников
..\GraduateWork> python backend/src/scripts/fetch_logos.py // найти логотипы команд
..\GraduateWork> python backend/src/scripts/ru_team_names.py // добавить русские названия для команд
..\GraduateWork> python backend/src/processing/build_dataset.py // обработка данных для нейросети
..\GraduateWork> python backend/src/processing/build_dataset_rnn.py // обработка данных для сложных нейросетей

если надо удалить БД матчей: python backend/src/scripts/reset_matches.py

//pip -m venv venv
venv\Scripts\activate // если пайтон не работает

// Анализ и сравнение нейросетей
python backend/src/models/research/random_forest.py // обучить моделИ для рандомного леса
python backend/src/models/research/mlp_net.py // найти лучшие параметры для MLP модели
python backend/src/models/research/lstm_net.py // найти лучшие параметры для LSTM модели
python backend/src/models/research/gru_net.py // найти лучшие параметры дял GRU модели
python backend/src/models/research/compare_all.py // сравнить все модели между собой
python backend/src/predictor.py // сгенерировать прогнозы

Запуск проекта локально
python backend/run.py

cd frontend
CourseWork\frontend>npm start

Запуск проекта на сервере
docker-compose down -v // всё стереть
docker-compose up --build // начало работы

по локальной сети
в cmd, чтобы узнать ipconfig IPv4 Address

http://192.168.X.X

создать ссылку для других

ngrok http 80 // работает только с ВПН

ssh -R 80:localhost:80 serveo.net // работает!!! (но минут 10) но сначала лучше запустить докер
npx localtunnel --port 80 --subdomain my-neuro-diploma-777 // обновить данные, если устарели

приложение для андроид

cd frontend

npm install @capacitor/core @capacitor/cli @capacitor/android // установка
npx cap init // инициализация
npx cap add android // создать папку
npm run build // Собрать проект и запустить
npx cap copy // Скопировать проект в андроид приложение
npx cap open android // открыть андроид стурию и собрать APK файл

npx cap sync

ipconfig в cmd
берём IP, инструкция выше
его в API.js
Сделать npm run build и npx cap sync

пересобрать APK в Android Studio, перед этим очистить проект
клир проджект и синий слон, потом билд апк

docker-compose up -d // запуск в фоновом режиме

выключение:

docker-compose stop // пауза
docker-compose down // полная остановка

проверка работающих контейнеров:
docker ps
