# backend/src/app.py
from flask import Flask
from flask_cors import CORS
from .api.routes import bp
from update import run_full_update 
from src.database.tables import init_db
import threading

def create_app():
    app = Flask(__name__)

    with app.app_context():
        try:
            print("🔧 Инициализация базы данных...")
            init_db()
            print("✅ Таблицы проверены/созданы")
        except Exception as e:
            print(f"❌ Ошибка инициализации БД: {e}")

    # Разрешаем запросы с React-фронтенда
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Регистрируем наши маршруты
    app.register_blueprint(bp, url_prefix='/api/matches')

    # Запускаем обновление в фоновом потоке, чтобы сайт открылся сразу
    #threading.Thread(target=run_full_update).start()

    return app