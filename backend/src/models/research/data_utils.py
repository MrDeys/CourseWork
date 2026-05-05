import os
import pandas as pd
import numpy as np
import joblib
import json
from sklearn.preprocessing import StandardScaler

# Настройка путей относительно расположения этого файла
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Папка, где будут лежать обученные веса, скейлер и конфиги
MODELS_SAVED_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '../saved'))
# Путь к сгенерированному датасету
DATASET_PATH = os.path.abspath(os.path.join(CURRENT_DIR, '../../dataset/ml_dataset.csv'))

def get_prepared_data(data_path=None):
    """
    Загружает датасет, выполняет хронологическое разделение на выборки,
    нормализует признаки и сохраняет скейлер.
    """
    if data_path is None:
        data_path = DATASET_PATH
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Датасет не найден по пути: {data_path}. Сначала запустите build_ml_dataset.py")

    # 1. Загрузка и хронологическая сортировка
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    # Сортировка по дате КРИТИЧЕСКИ ВАЖНА для исключения утечки данных (Data Leakage)
    df = df.sort_values(by='date').reset_index(drop=True)

    # 2. Определение колонок: Признаки (X) и Цели (y)
    # Эти колонки мы исключаем из входных данных модели
    cols_to_drop = [
        'date', 
        'target_outcome', 
        'target_total_2_5', 
        'target_home_goals', 
        'target_away_goals'
    ]
    
    # Все остальные колонки (включая созданные через One-Hot Encoding) становятся признаками
    feature_cols = [col for col in df.columns if col not in cols_to_drop]

    X_df = df[feature_cols]
    
    # Целевые переменные для разных задач (Outcome, Total, Goals)
    y_out = df['target_outcome'].values
    y_tot = df['target_total_2_5'].values
    y_hg = df['target_home_goals'].values
    y_ag = df['target_away_goals'].values

    # 3. Разделение на выборки (Time-Series Split: 80% обучение, 20% тест)
    split_idx = int(len(df) * 0.8)
    
    X_train_df = X_df.iloc[:split_idx]
    X_test_df = X_df.iloc[split_idx:]
    
    # 4. Нормализация (Scaling)
    # ВАЖНО: Скейлер обучается (fit) только на тренировочной выборке!
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_df)
    X_test_scaled = scaler.transform(X_test_df)

    # 5. Сохранение скейлера для использования в скриптах генерации прогнозов
    os.makedirs(MODELS_SAVED_DIR, exist_ok=True)
    scaler_save_path = os.path.join(MODELS_SAVED_DIR, 'shared_scaler.pkl')
    joblib.dump(scaler, scaler_save_path)

    # Формируем итоговый словарь данных
    data = {
        'X_train': X_train_scaled,
        'X_test': X_test_scaled,
        'y_out_train': y_out[:split_idx],
        'y_out_test': y_out[split_idx:],
        'y_tot_train': y_tot[:split_idx],
        'y_tot_test': y_tot[split_idx:],
        'y_hg_train': y_hg[:split_idx],
        'y_hg_test': y_hg[split_idx:],
        'y_ag_train': y_ag[:split_idx],
        'y_ag_test': y_ag[split_idx:],
        'feature_names': feature_cols
    }
    
    print(f"📊 Данные подготовлены. Признаков: {len(feature_cols)}. Обучение: {split_idx} строк, Тест: {len(df)-split_idx}")
    return data

def save_config(params, d, name_id):
    """
    Сохраняет конфигурацию архитектуры модели (размер входа, скрытых слоев и т.д.)
    в JSON-файл. Это необходимо для корректной сборки нейросети при инференсе.
    """
    config = {
        'input_size': int(d['X_train'].shape[1]),
        'hidden_size': int(params.get('hidden_size', 64)),
        'num_layers': int(params.get('num_layers', 1)),
        'dropout_rate': float(params.get('dropout', 0.3)),
        'lr': float(params.get('lr', 0.001))
    }

    config_path = os.path.join(MODELS_SAVED_DIR, f'config_{name_id}.json')
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

    print(f"⚙️ Конфигурация для '{name_id}' сохранена в: {config_path}")

if __name__ == "__main__":
    # Тестовый запуск для проверки путей
    try:
        data = get_prepared_data()
        print("✅ Тестовая загрузка данных прошла успешно.")
    except Exception as e:
        print(f"❌ Ошибка при загрузке данных: {e}")