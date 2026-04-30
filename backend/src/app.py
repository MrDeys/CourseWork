# backend/src/app.py
from flask import Flask
from flask_cors import CORS
from .api.routes import bp

def create_app():
    app = Flask(__name__)

    # Разрешаем запросы с React-фронтенда
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Регистрируем наши маршруты
    app.register_blueprint(bp, url_prefix='/api/matches')

    return app