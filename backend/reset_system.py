import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Подключаем пути
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.database.tables import Base, engine

def reset_database():
    print("⚠️  ВНИМАНИЕ: Сейчас база данных будет ПОЛНОСТЬЮ очищена!")
    confirm = input("Вы уверены? (y/n): ")
    if confirm.lower() != 'y':
        return

    # Удаляем все таблицы и создаем заново
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ База данных успешно пересоздана (пустая).")

if __name__ == "__main__":
    reset_database()