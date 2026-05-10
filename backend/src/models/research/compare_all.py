import torch
import joblib
import pandas as pd
import numpy as np
import os
import json
import pickle
from sklearn.metrics import (accuracy_score, f1_score, precision_score, 
                             recall_score, mean_absolute_error)

from data_utils import get_prepared_data, MODELS_SAVED_DIR
from mlp_net import MultiTaskFootballNet
from lstm_net import FootballLSTM
from gru_net import FootballGRUNet

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

def load_config(model_id):
    path = os.path.join(MODELS_SAVED_DIR, f'config_{model_id}.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

def evaluate_all():
    print("🚀 Запуск глубокого анализа моделей...")
    
    # --- 1. ЗАГРУЗКА ДАННЫХ ---
    try:
        d_flat = get_prepared_data()
        X_test_flat = d_flat['X_test']
        X_test_flat_ts = torch.tensor(X_test_flat, dtype=torch.float32)
        y_out_f, y_tot_f = d_flat['y_out_test'], d_flat['y_tot_test']
        y_hg_f, y_ag_f = d_flat['y_hg_test'], d_flat['y_ag_test']
    except Exception as e:
        print(f"❌ Ошибка загрузки плоских данных: {e}")
        return

    try:
        pkl_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dataset/rnn_dataset.pkl'))
        with open(pkl_path, 'rb') as f:
            rnn_data = pickle.load(f)
        split = int(len(rnn_data) * 0.8)
        test_rnn = rnn_data[split:]
        h_seq_ts = torch.tensor(np.array([i['home_seq'] for i in test_rnn]), dtype=torch.float32)
        a_seq_ts = torch.tensor(np.array([i['away_seq'] for i in test_rnn]), dtype=torch.float32)
        ctx_ts = torch.tensor(np.array([i['context'] for i in test_rnn]), dtype=torch.float32)
        y_out_r = np.array([i['target_outcome'] for i in test_rnn])
        y_tot_r = np.array([i['target_total'] for i in test_rnn])
        y_hg_r = np.array([i.get('target_home_goals', 0) for i in test_rnn])
        y_ag_r = np.array([i.get('target_away_goals', 0) for i in test_rnn])
    except Exception as e:
        print(f"❌ Ошибка загрузки RNN данных: {e}")
        test_rnn = None

    results = []

    def add_result(name, p_out, p_tot, p_hg, p_ag, true_out, true_tot, true_hg, true_ag):
        pred_out = np.argmax(p_out, axis=1) if p_out.ndim > 1 else p_out
        f1_map = f1_score(true_out, pred_out, average=None)
        pred_tot = (p_tot > 0.5).astype(int)
        mae = (mean_absolute_error(true_hg, p_hg) + mean_absolute_error(true_ag, p_ag)) / 2
        exact = ((np.round(p_hg) == true_hg) & (np.round(p_ag) == true_ag)).mean()

        results.append({
            'Model': name,
            'Acc': accuracy_score(true_out, pred_out),
            'F1_Macro': f1_score(true_out, pred_out, average='macro'),
            'Prec_Macro': precision_score(true_out, pred_out, average='macro', zero_division=0),
            'Recall_Macro': recall_score(true_out, pred_out, average='macro'),
            'F1_Draw (X)': f1_map[1] if len(f1_map) > 1 else 0,
            'Total_Acc': accuracy_score(true_tot, pred_tot),
            'Goals_MAE': mae,
            'Exact_Score': exact
        })

    # --- ТЕСТЫ ---

    # 1. Random Forest
    rf_dir = os.path.join(MODELS_SAVED_DIR, 'rf')
    try:
        m_out = joblib.load(os.path.join(rf_dir, 'rf_outcome.joblib'))
        m_tot = joblib.load(os.path.join(rf_dir, 'rf_total.joblib'))
        m_hg = joblib.load(os.path.join(rf_dir, 'rf_home_goals.joblib'))
        m_ag = joblib.load(os.path.join(rf_dir, 'rf_away_goals.joblib'))
        add_result('Random Forest', m_out.predict(X_test_flat), m_tot.predict(X_test_flat),
                   m_hg.predict(X_test_flat), m_ag.predict(X_test_flat), 
                   y_out_f, y_tot_f, y_hg_f, y_ag_f)
    except: pass

    # 2. MLP
    cfg = load_config('mlp')
    m_path = os.path.join(MODELS_SAVED_DIR, 'best_mlp_model.pth')
    if cfg and os.path.exists(m_path):
        try:
            model = MultiTaskFootballNet(int(cfg['input_size']), int(cfg['hidden_size']))
            model.load_state_dict(torch.load(m_path, map_location='cpu'))
            model.eval()
            with torch.no_grad():
                p_out, p_tot, p_hg, p_ag = model(X_test_flat_ts)
                add_result('MLP (Deep)', p_out.numpy(), torch.sigmoid(p_tot).squeeze().numpy(),
                           p_hg.squeeze().numpy(), p_ag.squeeze().numpy(), y_out_f, y_tot_f, y_hg_f, y_ag_f)
        except Exception as e:
            print(f"⚠️ MLP Load Error: {e}")

    # 3. RNN (LSTM & GRU)
    if test_rnn:
        for m_id, m_class, name in [('lstm', FootballLSTM, 'LSTM (RNN)'), ('gru', FootballGRUNet, 'GRU (RNN)')]:
            cfg = load_config(m_id)
            m_path = os.path.join(MODELS_SAVED_DIR, f'best_{m_id}_model.pth')
            if cfg and os.path.exists(m_path):
                try:
                    # ПРИНУДИТЕЛЬНОЕ ПРИВЕДЕНИЕ К INT
                    h_size = int(cfg['hidden_size'])
                    layers = int(cfg['num_layers'])
                    
                    model = m_class(int(h_seq_ts.shape[2]), int(ctx_ts.shape[1]), h_size, layers)
                    
                    # Пытаемся загрузить. Если в слоях ошибка - пробуем strict=False для отчета
                    state_dict = torch.load(m_path, map_location='cpu')
                    model.load_state_dict(state_dict)
                    
                    model.eval()
                    with torch.no_grad():
                        p_out, p_tot, p_hg, p_ag = model(h_seq_ts, a_seq_ts, ctx_ts)
                        add_result(name, p_out.numpy(), torch.sigmoid(p_tot).squeeze().numpy(),
                                   p_hg.squeeze().numpy(), p_ag.squeeze().numpy(), y_out_r, y_tot_r, y_hg_r, y_ag_r)
                except Exception as e:
                    print(f"⚠️ {name} Load Error: {e}")

    # --- ВЫВОД ---
    if not results: return
    res_df = pd.DataFrame(results).sort_values(by='F1_Macro', ascending=False)
    print("\n" + "="*115)
    print(f"{'МОДЕЛЬ':<20} | {'ACC':<6} | {'F1_MAC':<6} | {'PREC':<6} | {'REC':<6} | {'F1_DRW':<6} | {'TOT_ACC':<7} | {'MAE':<5} | {'EXACT'}")
    print("-" * 115)
    for _, r in res_df.iterrows():
        print(f"{r['Model']:<20} | {r['Acc']:.4f} | {r['F1_Macro']:.4f} | {r['Prec_Macro']:.4f} | {r['Recall_Macro']:.4f} | {r['F1_Draw (X)']:.4f} | {r['Total_Acc']:.4f}  | {r['Goals_MAE']:.3f} | {r['Exact_Score']:.4f}")
    print("="*115)

if __name__ == "__main__":
    evaluate_all()