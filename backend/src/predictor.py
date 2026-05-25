import os
import sys
import json
import joblib
import torch
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from sqlalchemy import or_

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

RESEARCH_PATH = os.path.join(BASE_DIR, 'models', 'research')
if RESEARCH_PATH not in sys.path:
    sys.path.append(RESEARCH_PATH)

from src.database.tables import SessionLocal, Match, Prediction
try:
    from models.research.mlp_net import MultiTaskFootballNet
except ImportError:
    from src.models.research.mlp_net import MultiTaskFootballNet

class PredictionGenerator:
    def __init__(self, model_id='mlp'):
        print(f"Инициализация PredictionGenerator [{model_id}]...")
        self.model_id = model_id
        
        self.saved_dir = os.path.join(BASE_DIR, 'models', 'saved')
        config_path = os.path.join(self.saved_dir, f'config_{model_id}.json')
        scaler_path = os.path.join(self.saved_dir, 'shared_scaler.pkl')
        weights_path = os.path.join(self.saved_dir, f'best_{model_id}_model.pth')

        with open(config_path, 'r') as f:
            self.cfg = json.load(f)

        self.scaler = joblib.load(scaler_path)
        self.feature_names = self.scaler.feature_names_in_.tolist()

        self.model = MultiTaskFootballNet(
            input_size=self.cfg['input_size'], 
            hidden_size=self.cfg['hidden_size']
        )
        self.model.load_state_dict(torch.load(weights_path, map_location=torch.device('cpu')))
        self.model.eval()
        print("Нейросеть и скейлер успешно загружены.")

    def get_team_stats(self, session, team_id, date):
        past = session.query(Match).filter(
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
            Match.status == 'FINISHED',
            Match.date < date
        ).order_by(Match.date.desc()).limit(5).all()

        if not past:
            return {k: 1.0 for k in ['xg_for', 'xg_against', 'ppda', 'deep', 'gf', 'ga', 'pts']} | {'rest': 7}

        stats = {'xg_f': [], 'xg_a': [], 'ppda': [], 'deep': [], 'gf': [], 'ga': [], 'pts': []}
        for m in past:
            is_h = m.home_team_id == team_id
            stats['xg_f'].append(float(m.home_xg if is_h else m.away_xg or 1.0))
            stats['xg_a'].append(float(m.away_xg if is_h else m.home_xg or 1.0))
            stats['ppda'].append(float(m.home_ppda if is_h else m.away_ppda or 10.0))
            stats['deep'].append(int(m.home_deep if is_h else m.away_deep or 5))
            gf, ga = (m.home_goals, m.away_goals) if is_h else (m.away_goals, m.home_goals)
            stats['gf'].append(gf)
            stats['ga'].append(ga)
            stats['pts'].append(3 if gf > ga else (1 if gf == ga else 0))

        return {
            'xg_for': np.mean(stats['xg_f']), 'xg_against': np.mean(stats['xg_a']),
            'ppda': np.mean(stats['ppda']), 'deep': np.mean(stats['deep']),
            'gf': np.mean(stats['gf']), 'ga': np.mean(stats['ga']),
            'pts': np.mean(stats['pts']), 'rest': min(max((date - past[0].date).days, 3), 14)
        }

    def prepare_features(self, session, match):
        h_st = self.get_team_stats(session, match.home_team_id, match.date)
        a_st = self.get_team_stats(session, match.away_team_id, match.date)
        
        h_elo = float(match.home_elo or 1500.0)
        a_elo = float(match.away_elo or 1500.0)

        data = {
            'home_elo': h_elo, 'away_elo': a_elo, 'elo_diff': h_elo - a_elo,
            'h_avg_xg_for_last_5': h_st['xg_for'], 'h_avg_xg_against_last_5': h_st['xg_against'],
            'h_avg_ppda_last_5': h_st['ppda'], 'h_avg_deep_last_5': h_st['deep'],
            'h_avg_goals_scored_last_5': h_st['gf'], 'h_avg_goals_conceded_last_5': h_st['ga'],
            'h_avg_points_last_5': h_st['pts'], 'h_xg_diff_last_5': h_st['xg_for'] - h_st['xg_against'],
            'a_avg_xg_for_last_5': a_st['xg_for'], 'a_avg_xg_against_last_5': a_st['xg_against'],
            'a_avg_ppda_last_5': a_st['ppda'], 'a_avg_deep_last_5': a_st['deep'],
            'a_avg_goals_scored_last_5': a_st['gf'], 'a_avg_goals_conceded_last_5': a_st['ga'],
            'a_avg_points_last_5': a_st['pts'], 'a_xg_diff_last_5': a_st['xg_for'] - a_st['xg_against'],
            'h_rest_days': float(h_st['rest']), 'a_rest_days': float(a_st['rest']),
            'rest_days_diff': float(h_st['rest'] - a_st['rest']), 'h2h_home_pts': 1.0 # Заглушка, если нет H2H
        }

        df = pd.DataFrame(0.0, index=[0], columns=self.feature_names)
        for col, val in data.items():
            if col in df.columns: df.at[0, col] = float(val)
        
        l_col, m_col = f"league_id_{match.league_id}", f"month_{match.date.month}"
        if l_col in df.columns: df.at[0, l_col] = 1.0
        if m_col in df.columns: df.at[0, m_col] = 1.0
                
        return df

    def run_generation(self):
        session = SessionLocal()
        current_version = "MLP_v1_MTL"
        
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        start_date = now - timedelta(days=10)
        end_date = now + timedelta(days=30)

        target_matches = session.query(Match).filter(
            Match.date >= start_date,
            Match.date <= end_date
        ).all()
        
        print(f"Обработка прогнозов для {len(target_matches)} матчей (окно: {start_date.date()} - {end_date.date()})")
        
        updated_count = 0
        created_count = 0

        for m in target_matches:
            try:
                X_df = self.prepare_features(session, m)
                X_scaled = self.scaler.transform(X_df)
                X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
                
                with torch.no_grad():
                    p_out, p_tot, p_hg, p_ag = self.model(X_tensor)
                    
                    probs = torch.softmax(p_out, dim=1).squeeze().numpy()
                    idx = np.argmax(probs)
                    outcomes = ['Win Away', 'Draw', 'Win Home']
                    outcome_str = outcomes[idx]
                    
                    prob_tot = float(torch.sigmoid(p_tot).item())
                    raw_hg, raw_ag = float(p_hg.item()), float(p_ag.item())
                    hg, ag = round(raw_hg), round(raw_ag)

                    # Пост-обработка
                    if outcome_str == 'Win Home' and hg <= ag: hg = ag + 1
                    elif outcome_str == 'Win Away' and ag <= hg: ag = hg + 1
                    elif outcome_str == 'Draw': hg = ag = round((raw_hg + raw_ag) / 2)
                    
                    if outcome_str != 'Draw' and max(hg, ag) == 0:
                        if outcome_str == 'Win Home': hg = 1
                        else: ag = 1

                pred = session.query(Prediction).filter(
                    Prediction.match_id == m.id, 
                    Prediction.model_version == current_version
                ).first()

                if pred:
                    pred.prob_a = float(probs[0])
                    pred.prob_d = float(probs[1])
                    pred.prob_h = float(probs[2])
                    pred.predicted_outcome = outcome_str
                    pred.total_over_2_5_probability = prob_tot
                    pred.predicted_exact_score = f"{int(hg)}:{int(ag)}"
                    pred.created_at = datetime.now(timezone.utc)
                    updated_count += 1
                else:
                    pred = Prediction(
                        match_id=m.id, 
                        model_version=current_version,
                        prob_a=float(probs[0]), prob_d=float(probs[1]), prob_h=float(probs[2]),
                        predicted_outcome=outcome_str,
                        total_over_2_5_probability=prob_tot,
                        predicted_exact_score=f"{int(hg)}:{int(ag)}",
                        created_at=datetime.now(timezone.utc)
                    )
                    session.add(pred)
                    created_count += 1

                session.commit()

            except Exception as e:
                print(f"Ошибка в матче {m.id}: {e}")
                session.rollback()

        session.close()
        print(f"Готово! Обновлено: {updated_count}, Создано для архива/будущего: {created_count}.")

if __name__ == "__main__":
    gen = PredictionGenerator()
    gen.run_generation()