import os
import sys
import datetime

# --- ИСПРАВЛЕНИЕ ПУТЕЙ ---
# Получаем путь к папке backend (корень)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Добавляем корень в пути поиска, чтобы Python видел пакет 'src'
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- ИМПОРТЫ ИЗ ТВОЕЙ СТРУКТУРЫ ---
try:
    # Загрузка данных из src/scripts/loading_soccerdata.py
    from src.scripts.loading_soccerdata import load_data
    
    # Синхронизация ELO из src/scripts/find_team_mapping.py
    # (убедись, что функция внутри называется auto_sync_elo)
    from src.scripts.find_team_mappings import auto_sync_elo
    
    # Генератор прогнозов из src/predictor.py
    # (убедись, что класс внутри называется PredictionGenerator)
    from src.predictor import PredictionGenerator
    
    print("✅ Все модули успешно обнаружены")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Проверь наличие __init__.py в папках src и src/scripts")
    sys.exit(1)

def run_full_update():
    """Полный цикл: Сбор -> ELO -> Прогнозы"""
    print(f"\n[{datetime.datetime.now()}] 🚀 Старт автоматического обновления...")

    try:
        # 1. Загрузка данных Understat
        print("\n--- [1/3] Загрузка данных Understat ---")
        load_data()

        # 2. Рейтинг ELO
        print("\n--- [2/3] Синхронизация рейтинга ELO ---")
        auto_sync_elo()

        # 3. Генерация прогнозов
        print("\n--- [3/3] Генерация новых прогнозов (Нейросеть) ---")
        gen = PredictionGenerator()
        gen.run_generation()

        print(f"\n✅ [{datetime.datetime.now()}] Все данные обновлены!")
    except Exception as e:
        print(f"❌ Произошла ошибка во время обновления: {e}")

if __name__ == "__main__":
    run_full_update()