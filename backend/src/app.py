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
            from .database.tables import init_db
            init_db()
        except Exception as e:
            print(f"БД пока не готова: {e}")

    from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://192.168.3.22", 
                "http://localhost", 
                "capacitor://localhost", 
                "http://localhost:3000"
            ],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Bypass-Tunnel-Reminder"]
        }
    })
    
    app.register_blueprint(bp, url_prefix='/api/matches')
    return app