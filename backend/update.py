import os
import sys
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from src.database.tables import init_db
    from src.scripts.loading_soccerdata import load_data
    from src.scripts.find_team_mappings import auto_sync_elo
    from src.predictor import PredictionGenerator
    from src.scripts.fetch_logos import get_wikipedia_logo, update_team_logos
    from src.scripts.ru_team_names import translate_teams
    
    print("Все модули успешно обнаружены")
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Проверь наличие __init__.py в папках src и src/scripts")
    sys.exit(1)

def run_full_update():
    print(f"\n[{datetime.datetime.now()}] Старт автоматического обновления...")
    
    # 0. Таблицы
    init_db()

    # 1. Базовая загрузка (Understat)
    try:
        print("\n--- [1/5] Загрузка данных Understat ---")
        load_data()
    except Exception as e: print(f"Ошибка в load_data: {e}")

    # 2. Перевод (Очень важно для красоты!)
    try:
        print("\n--- [2/5] Локализация команд ---")
        translate_teams()
    except Exception as e: print(f"Ошибка в переводе: {e}")

    # 3. Логотипы (Критично для UI!)
    try:
        print("\n--- [3/5] Загрузка эмблем ---")
        update_team_logos()
    except Exception as e: print(f"Ошибка в логотипах: {e}")

    # 4. ELO (Ограничим поиск, чтобы не ловить бан)
    try:
        print("\n--- [4/5] Синхронизация ELO ---")
        auto_sync_elo()
    except Exception as e: print(f"Ошибка в ELO (ClubElo может быть недоступен): {e}")

    # 5. Прогнозы
    try:
        print("\n--- [5/5] Генерация прогнозов ---")
        gen = PredictionGenerator()
        gen.run_generation()
    except Exception as e: print(f"Ошибка в прогнозах: {e}")

    print(f"\nОбновление завершено (с учетом возможных пропусков).")

if __name__ == "__main__":
    run_full_update()