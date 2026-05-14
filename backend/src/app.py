# backend/src/app.py
from flask import Flask
from flask_cors import CORS
from .api.routes import bp
from update import run_full_update 
from src.database.tables import init_db
import threading

def create_app():
    app = Flask(__name__)
    
    # Сделаем инициализацию более тихой
    with app.app_context():
        try:
            from .database.tables import init_db
            init_db()
        except Exception as e:
            # Просто пишем в лог, но не роняем сервер
            print(f"⚠️ БД пока не готова: {e}")

    from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # Разрешаем запросы и от браузера (IP), и от приложения (capacitor://)
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://192.168.3.22", 
                "http://localhost", 
                "capacitor://localhost", # <--- ОБЯЗАТЕЛЬНО ДЛЯ ПРИЛОЖЕНИЯ
                "http://localhost:3000"
            ],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Bypass-Tunnel-Reminder"]
        }
    })
    
    app.register_blueprint(bp, url_prefix='/api/matches')
    return app