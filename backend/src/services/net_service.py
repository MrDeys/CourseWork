import os
import sys
import torch
import joblib
import json
import numpy as np
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__)) 
research_path = os.path.abspath(os.path.join(current_dir, '..', 'models', 'research'))
saved_models_path = os.path.abspath(os.path.join(current_dir, '..', 'models', 'saved'))

if research_path not in sys.path:
    sys.path.insert(0, research_path)

try:
    from mlp_net import MultiTaskFootballNet
    print("Модуль mlp_net и зависимости (data_utils) успешно загружены")
except ImportError as e:
    print(f"Ошибка импорта модели: {e}")

class InferenceService:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = []
        self._load_model()

    def _load_model(self):
        try:
            config_path = os.path.join(saved_models_path, 'config_mlp.json')
            scaler_path = os.path.join(saved_models_path, 'shared_scaler.pkl')
            model_path = os.path.join(saved_models_path, 'best_mlp_model.pth')

            if not os.path.exists(model_path):
                print(f"❌ Файл весов не найден по пути: {model_path}")
                return

            with open(config_path, 'r') as f:
                cfg = json.load(f)

            self.scaler = joblib.load(scaler_path)
            self.feature_names = self.scaler.feature_names_in_.tolist()

            self.model = MultiTaskFootballNet(
                input_size=cfg['input_size'], 
                hidden_size=cfg['hidden_size']
            )
            self.model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
            self.model.eval()
            print(f"Модель MLP успешно инициализирована")
        except Exception as e:
            print(f"Ошибка инициализации InferenceService: {e}")

    def predict(self, t1_stats, t2_stats, t1_elo, t2_elo):
        if self.model is None or self.scaler is None:
            return None

        input_data = {
            'home_elo': t1_elo, 'away_elo': t2_elo, 'elo_diff': t1_elo - t2_elo,
            'h_avg_xg_for_last_5': t1_stats['xg_for'], 'h_avg_xg_against_last_5': t1_stats['xg_against'],
            'h_avg_ppda_last_5': t1_stats['ppda'], 'h_avg_deep_last_5': t1_stats['deep'],
            'h_avg_goals_scored_last_5': t1_stats['gf'], 'h_avg_goals_conceded_last_5': t1_stats['ga'],
            'h_xg_diff_last_5': t1_stats['xg_for'] - t1_stats['xg_against'],
            'a_avg_xg_for_last_5': t2_stats['xg_for'], 'a_avg_xg_against_last_5': t2_stats['xg_against'],
            'a_avg_ppda_last_5': t2_stats['ppda'], 'a_avg_deep_last_5': t2_stats['deep'],
            'a_avg_goals_scored_last_5': t2_stats['gf'], 'a_avg_goals_conceded_last_5': t2_stats['ga'],
            'a_xg_diff_last_5': t2_stats['xg_for'] - t2_stats['xg_against'],
            'h_rest_days': 7.0, 'a_rest_days': 7.0, 'rest_days_diff': 0.0, 'h2h_home_pts': 1.5
        }

        df = pd.DataFrame(0.0, index=[0], columns=self.feature_names)
        for col, val in input_data.items():
            if col in df.columns:
                df.at[0, col] = float(val)

        X_scaled = self.scaler.transform(df)
        X_tensor = torch.tensor(X_scaled, dtype=torch.float32)

        with torch.no_grad():
            p_out, p_tot, p_hg, p_ag = self.model(X_tensor)
            
            probs = torch.softmax(p_out, dim=1).squeeze().numpy()
            idx = np.argmax(probs)
            outcomes = ['Win Away', 'Draw', 'Win Home']

            raw_hg, raw_ag = float(p_hg.item()), float(p_ag.item())
            hg = 0 if raw_hg < 0.9 else round(raw_hg)
            ag = 0 if raw_ag < 0.9 else round(raw_ag)   
            
            if outcomes[idx] == 'Win Home' and hg <= ag: hg = ag + 1
            elif outcomes[idx] == 'Win Away' and ag <= hg: ag = hg + 1
            elif outcomes[idx] == 'Draw': hg = ag = round((hg + ag) / 2)

            return {
                "prob_home": round(float(probs[2] * 100), 1),
                "prob_draw": round(float(probs[1] * 100), 1),
                "prob_away": round(float(probs[0] * 100), 1),
                "outcome": outcomes[idx],
                "exact_score": f"{int(hg)}:{int(ag)}",
                "total_over_2_5": round(float(torch.sigmoid(p_tot).item() * 100), 1)
            }