import torch
import joblib
import pandas as pd
import numpy as np
import os
import json
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error

# Импорты 
from data_utils import get_prepared_data, MODELS_SAVED_DIR
from mlp_net import MultiTaskFootballNet
from lstm_net import MultiTaskLSTMNet
from gru_net import MultiTaskGRUNet

# Настройки для красивого вывода широкой таблицы в консоль
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

def load_nn_model(model_class, model_id):
    config_path = os.path.join(MODELS_SAVED_DIR, f'config_{model_id}.json')
    weights_path = os.path.join(MODELS_SAVED_DIR, f'best_{model_id}_model.pth')

    if not os.path.exists(config_path) or not os.path.exists(weights_path):
        print(f"  [!] Файлы для {model_id} не найдены.")
        return None

    with open(config_path, 'r') as f:
        cfg = json.load(f)
    
    print(f"  Загрузка {model_id}: hidden={cfg['hidden_size']}, layers={cfg.get('num_layers', 'N/A')}")

    try:
        if model_id == 'mlp':
            model = model_class(
                input_size=cfg['input_size'], 
                hidden_size=int(cfg['hidden_size']), 
                dropout_rate=cfg.get('dropout_rate', 0.5)
            )
        else:
            model = model_class(
                input_size=cfg['input_size'], 
                hidden_size=int(cfg['hidden_size']), 
                num_layers=int(cfg['num_layers']), 
                dropout_rate=cfg.get('dropout_rate', 0.3)
            )
        
        model.load_state_dict(torch.load(weights_path))
        model.eval()
        return model
    except Exception as e:
        print(f"  [X] Ошибка сборки {model_id}: {e}")
        return None

def evaluate_all():
    print("--- ЗАГРУЗКА ДАННЫХ ---")
    d = get_prepared_data()
    X_test_tensor = torch.tensor(d['X_test'], dtype=torch.float32)
    results = []

    y_out_true = d['y_out_test']
    y_tot_true = d['y_tot_test']
    y_hg_true = d['y_hg_test']
    y_ag_true = d['y_ag_test']

    # --- 1. RANDOM FOREST ---
    print("\nТестируем Random Forest...")
    rf_dir = os.path.join(MODELS_SAVED_DIR, 'rf')
    rf_out_path = os.path.join(rf_dir, 'rf_outcome.joblib')
    
    if os.path.exists(rf_out_path):
        rf_out = joblib.load(rf_out_path)
        preds_out = rf_out.predict(d['X_test'])
        
        # F1 для каждого класса (0: Away, 1: Draw, 2: Home)
        f1_classes = f1_score(y_out_true, preds_out, average=None)
        
        # Тотал
        tot_acc = np.nan
        rf_tot_path = os.path.join(rf_dir, 'rf_total.joblib')
        if os.path.exists(rf_tot_path):
            rf_tot = joblib.load(rf_tot_path)
            tot_acc = accuracy_score(y_tot_true, rf_tot.predict(d['X_test']))

        # Голы (MAE и Точный счет)
        mae = np.nan
        exact_score_acc = np.nan
        rf_hg_path = os.path.join(rf_dir, 'rf_home_goals.joblib')
        rf_ag_path = os.path.join(rf_dir, 'rf_away_goals.joblib')
        if os.path.exists(rf_hg_path) and os.path.exists(rf_ag_path):
            rf_hg = joblib.load(rf_hg_path); rf_ag = joblib.load(rf_ag_path)
            p_hg = rf_hg.predict(d['X_test'])
            p_ag = rf_ag.predict(d['X_test'])
            
            mae = (mean_absolute_error(y_hg_true, p_hg) + mean_absolute_error(y_ag_true, p_ag)) / 2
            
            # Точный счет (округляем прогнозы и сравниваем с реальностью)
            exact_match = (np.round(p_hg) == y_hg_true) & (np.round(p_ag) == y_ag_true)
            exact_score_acc = exact_match.mean()

        results.append({
            'Model': 'Random Forest',
            'Acc': accuracy_score(y_out_true, preds_out),
            'F1_Macro': f1_score(y_out_true, preds_out, average='macro'),
            'F1_Away': f1_classes[0],
            'F1_Draw': f1_classes[1],
            'F1_Home': f1_classes[2],
            'Total_Acc': tot_acc,
            'Goals_MAE': mae,
            'Exact_Score': exact_score_acc
        })

    # --- 2. НЕЙРОСЕТИ ---
    for name, m_class, m_id in [('MLP', MultiTaskFootballNet, 'mlp'), 
                                 ('LSTM', MultiTaskLSTMNet, 'lstm'), 
                                 ('GRU', MultiTaskGRUNet, 'gru')]:
        print(f"Тестируем {name}...")
        model = load_nn_model(m_class, m_id)
        if model:
            with torch.no_grad():
                p_out, p_tot, p_hg, p_ag = model(X_test_tensor)
                
                # Исход
                _, pred_out = torch.max(p_out, 1)
                pred_out = pred_out.numpy()
                f1_classes = f1_score(y_out_true, pred_out, average=None)
                
                # Тотал (p_tot - это логиты, применяем сигмоиду для вероятности)
                pred_tot_probs = torch.sigmoid(p_tot).squeeze().numpy()
                pred_tot = (pred_tot_probs > 0.5).astype(int)
                tot_acc = accuracy_score(y_tot_true, pred_tot)

                # Голы
                pred_hg = p_hg.squeeze().numpy()
                pred_ag = p_ag.squeeze().numpy()
                mae = (mean_absolute_error(y_hg_true, pred_hg) + mean_absolute_error(y_ag_true, pred_ag)) / 2
                
                # Точный счет
                exact_match = (np.round(pred_hg) == y_hg_true) & (np.round(pred_ag) == y_ag_true)
                exact_score_acc = exact_match.mean()

                results.append({
                    'Model': name,
                    'Acc': accuracy_score(y_out_true, pred_out),
                    'F1_Macro': f1_score(y_out_true, pred_out, average='macro'),
                    'F1_Away': f1_classes[0],
                    'F1_Draw': f1_classes[1],
                    'F1_Home': f1_classes[2],
                    'Total_Acc': tot_acc,
                    'Goals_MAE': mae,
                    'Exact_Score': exact_score_acc
                })

    # --- ВЫВОД ---
    if not results:
        print("Ошибка: Нет моделей для сравнения.")
        return

    res_df = pd.DataFrame(results).sort_values(by='F1_Macro', ascending=False)
    print("\n" + "="*110)
    print("ФИНАЛЬНОЕ СРАВНЕНИЕ МОДЕЛЕЙ ДЛЯ ДИПЛОМА (РАСШИРЕННОЕ)")
    print("="*110)
    print(res_df.to_string(index=False, float_format=lambda x: "{:.4f}".format(x)))
    
    save_path = os.path.join(MODELS_SAVED_DIR, 'final_report_detailed.csv')
    res_df.to_csv(save_path, index=False)
    print(f"\nДетальный отчет сохранен в: {save_path}")

if __name__ == "__main__":
    evaluate_all()