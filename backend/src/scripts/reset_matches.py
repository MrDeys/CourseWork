import os
import sys
# Настройка путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..', '..')))

from src.database.tables import SessionLocal, Match, Prediction

def reset_db():
    session = SessionLocal()
    print("🧹 Полная очистка матчей и прогнозов...")
    try:
        # Удаляем прогнозы и матчи (CASCADE не нужен в SQLAlchemy, если удалять по порядку)
        session.query(Prediction).delete()
        session.query(Match).delete()
        session.commit()
        print("✅ База матчей очищена. Таблицы команд и лиг сохранены.")
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    reset_db()