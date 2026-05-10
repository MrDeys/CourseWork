# backend/src/app.py
from flask import Flask
from flask_cors import CORS
from .api.routes import bp
from update import run_full_update 

def create_app():
    app = Flask(__name__)

    # Разрешаем запросы с React-фронтенда
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Регистрируем наши маршруты
    app.register_blueprint(bp, url_prefix='/api/matches')

    # Запускаем обновление в фоновом потоке, чтобы сайт открылся сразу
    # threading.Thread(target=run_full_update).start()

    return app