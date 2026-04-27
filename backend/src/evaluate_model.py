import pandas as pd
import torch
import joblib
from sklearn.metrics import classification_report, accuracy_score
import os

# Импортируй класс MultiTaskFootballNet из machine_learning.py
from machine_learning import MultiTaskFootballNet 

def evaluate():
    # 1. Загрузка данных
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'processed/ml_dataset.csv'))
    df = pd.read_csv(data_path)
    df = df.sort_values(by='date').reset_index(drop=True)

    # Те же колонки, что при обучении
    cols_to_drop = ['id', 'date', 'league_id', 'home_team_id', 'away_team_id', 
                    'target_outcome', 'target_total_2_5', 'target_home_goals', 'target_away_goals']
    feature_cols = [col for col in df.columns if col not in cols_to_drop]
    
    # 2. Подготовка X (берем только тестовую часть)
    split_index = int(len(df) * 0.8)
    X = df[feature_cols].values
    y_outcome = df['target_outcome'].values
    X_test = X[split_index:]
    y_test = y_outcome[split_index:]

    # 3. Скейлинг (используем тот же, что был при обучении!)
    scaler = joblib.load('models/scaler.pkl')
    X_test_scaled = scaler.transform(X_test)
    X_test_tensor = torch.tensor(X_test_scaled, dtype=torch.float32)

    # 4. Загрузка модели
    model = MultiTaskFootballNet(input_size=len(feature_cols))
    model.load_state_dict(torch.load('models/best_football_model.pth'))
    model.eval()

    # 5. Предсказание
    with torch.no_grad():
        pred_out, _, _, _ = model(X_test_tensor)
        _, predicted = torch.max(pred_out, 1)

    # 6. Вывод отчета
    print("\n--- ОТЧЕТ О КАЧЕСТВЕ МОДЕЛИ ---")
    print(f"Accuracy: {accuracy_score(y_test, predicted.numpy()):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, predicted.numpy(), target_names=['Win A', 'Draw', 'Win H']))

if __name__ == "__main__":
    evaluate()