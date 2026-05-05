import os
import sys
import pandas as pd
import numpy as np
import torch
import joblib
import json
from datetime import datetime

# --- ГАРАНТИРОВАННОЕ РЕШЕНИЕ ПРОБЛЕМЫ ИМПОРТОВ ---
SRC_PATH = os.path.dirname(os.path.abspath(__file__))
if SRC_PATH not in sys.path:
    sys.path.append(SRC_PATH)

RESEARCH_PATH = os.path.join(SRC_PATH, 'models', 'research')
if RESEARCH_PATH not in sys.path:
    sys.path.append(RESEARCH_PATH)

from database.tables import SessionLocal, Match, Prediction
from models.research.mlp_net import MultiTaskFootballNet
from models.research.data_utils import MODELS_SAVED_DIR

class PredictionGenerator:
    def __init__(self, model_id='mlp'):
        print(f"--- Инициализация системы прогнозирования [{model_id}] ---")
        self.model_id = model_id
        
        # 1. Загрузка конфигурации модели
        config_path = os.path.join(MODELS_SAVED_DIR, f'config_{model_id}.json')
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Конфигурация не найдена: {config_path}")
            
        with open(config_path, 'r') as f:
            self.cfg = json.load(f)
            
        # 2. Загрузка обученного скейлера
        scaler_path = os.path.join(MODELS_SAVED_DIR, 'shared_scaler.pkl')
        self.scaler = joblib.load(scaler_path)
        self.feature_names = self.scaler.feature_names_in_.tolist()
        
        # 3. Загрузка весов нейросети
        self.model = MultiTaskFootballNet(
            input_size=self.cfg['input_size'], 
            hidden_size=self.cfg['hidden_size']
        )
        weights_path = os.path.join(MODELS_SAVED_DIR, f'best_{model_id}_model.pth')
        self.model.load_state_dict(torch.load(weights_path))
        self.model.eval()
        print("✅ Модель, скейлер и конфигурация загружены успешно.")

    def get_match_features(self, session, match):
        """Собирает статистические признаки для будущего матча"""
        
        def get_team_stats(team_id, date):
            past = session.query(Match).filter(
                ((Match.home_team_id == team_id) | (Match.away_team_id == team_id)),
                Match.status == 'FINISHED', Match.date < date
            ).order_by(Match.date.desc()).limit(5).all()
            
            if not past:
                return {k: 1.0 for k in ['xg_for', 'xg_against', 'ppda', 'deep', 'goals_scored', 'goals_conceded', 'pts']} | {'rest': 7}
            
            stats = {'xg_f': [], 'xg_a': [], 'ppda': [], 'deep': [], 'gf': [], 'ga': [], 'pts': []}
            for m in past:
                is_h = m.home_team_id == team_id
                stats['xg_f'].append((m.home_xg if is_h else m.away_xg) or 1.0)
                stats['xg_a'].append((m.away_xg if is_h else m.home_xg) or 1.0)
                stats['ppda'].append((m.home_ppda if is_h else m.away_ppda) or 10.0)
                stats['deep'].append((m.home_deep if is_h else m.away_deep) or 5.0)
                gf, ga = (m.home_goals, m.away_goals) if is_h else (m.away_goals, m.home_goals)
                stats['gf'].append(gf)
                stats['ga'].append(ga)
                stats['pts'].append(3 if gf > ga else (1 if gf == ga else 0))
            
            return {
                'xg_for': np.mean(stats['xg_f']), 'xg_against': np.mean(stats['xg_a']),
                'ppda': np.mean(stats['ppda']), 'deep': np.mean(stats['deep']),
                'goals_scored': np.mean(stats['gf']), 'goals_conceded': np.mean(stats['ga']),
                'points': np.mean(stats['pts']), 'rest': min(max((date - past[0].date).days, 3), 14)
            }

        def get_h2h(home_id, away_id, date):
            matches = session.query(Match).filter(
                (((Match.home_team_id == home_id) & (Match.away_team_id == away_id)) |
                 ((Match.home_team_id == away_id) & (Match.away_team_id == home_id))),
                Match.status == 'FINISHED', Match.date < date
            ).order_by(Match.date.desc()).limit(3).all()
            if not matches: return 1.0
            pts = 0
            for m in matches:
                if m.home_team_id == home_id:
                    pts += 3 if m.home_goals > m.away_goals else (1 if m.home_goals == m.away_goals else 0)
                else:
                    pts += 3 if m.away_goals > m.home_goals else (1 if m.home_goals == m.away_goals else 0)
            return pts / len(matches)

        h_st, a_st = get_team_stats(match.home_team_id, match.date), get_team_stats(match.away_team_id, match.date)
        h2h = get_h2h(match.home_team_id, match.away_team_id, match.date)
        h_elo, a_elo = float(match.home_elo or 1500.0), float(match.away_elo or 1500.0)

        data = {
            'home_elo': h_elo, 'away_elo': a_elo, 'h_rest_days': float(h_st['rest']),
            'h_avg_xg_for_last_5': h_st['xg_for'], 'h_avg_xg_against_last_5': h_st['xg_against'],
            'h_avg_ppda_last_5': h_st['ppda'], 'h_avg_deep_last_5': h_st['deep'],
            'h_avg_goals_scored_last_5': h_st['goals_scored'], 'h_avg_goals_conceded_last_5': h_st['goals_conceded'],
            'h_avg_points_last_5': h_st['points'], 'h_xg_diff_last_5': h_st['xg_for'] - h_st['xg_against'],
            'a_rest_days': float(a_st['rest']), 'a_avg_xg_for_last_5': a_st['xg_for'],
            'a_avg_xg_against_last_5': a_st['xg_against'], 'a_avg_ppda_last_5': a_st['ppda'],
            'a_avg_deep_last_5': a_st['deep'], 'a_avg_goals_scored_last_5': a_st['goals_scored'],
            'a_avg_goals_conceded_last_5': a_st['goals_conceded'], 'a_avg_points_last_5': a_st['points'],
            'a_xg_diff_last_5': a_st['xg_for'] - a_st['xg_against'], 'elo_diff': h_elo - a_elo,
            'rest_days_diff': float(h_st['rest'] - a_st['rest']), 'h2h_home_pts': float(h2h)
        }

        # Инициализируем DataFrame нулями типа float, чтобы избежать ошибок типов
        df_single = pd.DataFrame(0.0, index=[0], columns=self.feature_names)
        for col, val in data.items():
            if col in df_single.columns: df_single.at[0, col] = float(val)
        
        # One-Hot Encoding (Месяц, Лига, День недели)
        l_col, m_col, d_col = f"league_id_{match.league_id}", f"month_{match.date.month}", f"day_of_week_{match.date.weekday()}"
        for col in [l_col, m_col, d_col]:
            if col in df_single.columns: df_single.at[0, col] = 1.0
                
        return df_single

    def run_generation(self):
        session = SessionLocal()
        scheduled_matches = session.query(Match).filter(Match.status == 'SCHEDULED').all()
        
        print(f"Генерация согласованных прогнозов для {len(scheduled_matches)} матчей...")
        
        for m in scheduled_matches:
            try:
                X_df = self.get_match_features(session, m)
                X_scaled = self.scaler.transform(X_df)
                X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
                
                with torch.no_grad():
                    p_out, p_tot, p_hg, p_ag = self.model(X_tensor)
                    
                    # 1. Вероятности исхода
                    probs = torch.softmax(p_out, dim=1).squeeze().numpy() # [Away, Draw, Home]
                    idx = np.argmax(probs)
                    outcome_str = ['Win Away', 'Draw', 'Win Home'][idx]
                    
                    # 2. Тотал
                    prob_tot = torch.sigmoid(p_tot).item()
                    
                    # 3. Голы (Сырые значения из регрессии)
                    raw_hg, raw_ag = float(p_hg.item()), float(p_ag.item())
                    hg = 0 if raw_hg < 0.9 else round(raw_hg)
                    ag = 0 if raw_ag < 0.9 else round(raw_ag)   

                    # --- ЛОГИКА СОГЛАСОВАНИЯ (RECONCILIATION) ---
                    # Приводим счет в соответствие с предсказанным исходом
                    if outcome_str == 'Win Home' and hg <= ag:
                        hg = ag + 1
                    elif outcome_str == 'Win Away' and ag <= hg:
                        ag = hg + 1
                    elif outcome_str == 'Draw' and hg != ag:
                        val = round((raw_hg + raw_ag) / 2)
                        hg, ag = val, val
                    
                    # Дополнительная проверка: если победа, то голов не может быть 0
                    if outcome_str != 'Draw' and max(hg, ag) == 0:
                        if outcome_str == 'Win Home': hg = 1
                        else: ag = 1

                # Сохранение в базу данных
                pred_record = session.query(Prediction).filter(Prediction.match_id == m.id).first()
                if not pred_record:
                    pred_record = Prediction(match_id=m.id)
                    session.add(pred_record)

                pred_record.prob_a, pred_record.prob_d, pred_record.prob_h = float(probs[0]), float(probs[1]), float(probs[2])
                pred_record.predicted_outcome = outcome_str
                pred_record.total_over_2_5_probability = float(prob_tot)
                pred_record.predicted_exact_score = f"{int(hg)}:{int(ag)}"
                pred_record.model_version = f"MLP_v1_MTL"
                pred_record.created_at = datetime.utcnow()
                
                print(f"✅ {m.home_team.name} vs {m.away_team.name} | Исход: {outcome_str:10} | Счет: {pred_record.predicted_exact_score}")

            except Exception as e:
                print(f"❌ Ошибка в матче {m.id}: {e}")

        session.commit()
        session.close()
        print("\nВсе прогнозы успешно сгенерированы и согласованы!")

if __name__ == "__main__":
    gen = PredictionGenerator()
    gen.run_generation()