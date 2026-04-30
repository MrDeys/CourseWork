import pandas as pd
import numpy as np
import joblib
import os, sys
from datetime import datetime

# Подключаем БД и пути (убедись, что sys.path настроен правильно)
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, '..'))
research_dir = os.path.join(current_dir, 'models', 'research')

if backend_dir not in sys.path: sys.path.append(backend_dir)
if research_dir not in sys.path: sys.path.append(research_dir)

from database.tables import SessionLocal, Match, Prediction
from models.research.data_utils import MODELS_SAVED_DIR

# 1. ЗАГРУЗКА МОДЕЛЕЙ И СКЕЙЛЕРА
rf_dir = os.path.join(MODELS_SAVED_DIR, 'rf')
rf_out = joblib.load(os.path.join(rf_dir, 'rf_outcome.joblib'))
rf_tot = joblib.load(os.path.join(rf_dir, 'rf_total.joblib'))
rf_hg = joblib.load(os.path.join(rf_dir, 'rf_home_goals.joblib'))
rf_ag = joblib.load(os.path.join(rf_dir, 'rf_away_goals.joblib'))
scaler = joblib.load(os.path.join(MODELS_SAVED_DIR, 'shared_scaler.pkl'))

def get_recent_stats(session, team_id, current_date, window=5):
    """Вычисляет средние показатели команды за последние 5 матчей"""
    past_matches = session.query(Match).filter(
        ((Match.home_team_id == team_id) | (Match.away_team_id == team_id)),
        Match.status == 'FINISHED',
        Match.date < current_date
    ).order_by(Match.date.desc()).limit(window).all()

    if not past_matches:
        return {'xg_for': 1.0, 'xg_against': 1.0, 'ppda': 10.0, 'deep': 5.0, 
                'goals_scored': 1.0, 'goals_conceded': 1.0, 'points': 1.0, 'rest_days': 7}

    stats = {'xg_for': [], 'xg_against': [], 'ppda': [], 'deep': [], 
             'goals_scored': [], 'goals_conceded': [], 'points': []}
    
    last_match_date = past_matches[0].date
    rest_days = min(max((current_date - last_match_date).days, 3), 14)

    for m in past_matches:
        is_home = (m.home_team_id == team_id)
        stats['xg_for'].append((m.home_xg if is_home else m.away_xg) or 1.0)
        stats['xg_against'].append((m.away_xg if is_home else m.home_xg) or 1.0)
        stats['ppda'].append((m.home_ppda if is_home else m.away_ppda) or 10.0)
        stats['deep'].append((m.home_deep if is_home else m.away_deep) or 5.0)
        
        gf = m.home_goals if is_home else m.away_goals
        ga = m.away_goals if is_home else m.home_goals
        stats['goals_scored'].append(gf)
        stats['goals_conceded'].append(ga)
        stats['points'].append(3 if gf > ga else (1 if gf == ga else 0))

    avg_stats = {k: np.mean(v) for k, v in stats.items()}
    avg_stats['rest_days'] = rest_days
    return avg_stats

def get_h2h_stats(session, home_id, away_id, current_date, window=3):
    h2h_matches = session.query(Match).filter(
        (((Match.home_team_id == home_id) & (Match.away_team_id == away_id)) |
         ((Match.home_team_id == away_id) & (Match.away_team_id == home_id))),
        Match.status == 'FINISHED',
        Match.date < current_date
    ).order_by(Match.date.desc()).limit(window).all()

    if not h2h_matches: return 1.0

    pts = 0
    for m in h2h_matches:
        if m.home_team_id == home_id:
            pts += 3 if m.home_goals > m.away_goals else (1 if m.home_goals == m.away_goals else 0)
        else:
            pts += 3 if m.away_goals > m.home_goals else (1 if m.home_goals == m.away_goals else 0)
    return pts / len(h2h_matches)

def generate_predictions_rf():
    session = SessionLocal()
    
    # 2. ПОЛУЧАЕМ ПОРЯДОК ПРИЗНАКОВ (Как в ML Dataset)
    try:
        expected_features = scaler.feature_names_in_.tolist()
    except AttributeError:
        print("Ошибка: Скейлер не содержит имен признаков. Обучите модель заново.")
        return

    scheduled_matches = session.query(Match).filter(Match.status == 'SCHEDULED').all()
    print(f"Обработка {len(scheduled_matches)} матчей с помощью Random Forest...")

    for m in scheduled_matches:
        try:
            h_st = get_recent_stats(session, m.home_team_id, m.date)
            a_st = get_recent_stats(session, m.away_team_id, m.date)
            h2h = get_h2h_stats(session, m.home_team_id, m.away_team_id, m.date)

            h_elo = m.home_elo or 1500.0
            a_elo = m.away_elo or 1500.0

            feat_dict = {
                'home_elo': h_elo, 'away_elo': a_elo,
                'h_rest_days': h_st['rest_days'],
                'h_avg_xg_for_last_5': h_st['xg_for'], 'h_avg_xg_against_last_5': h_st['xg_against'],
                'h_avg_ppda_last_5': h_st['ppda'], 'h_avg_deep_last_5': h_st['deep'],
                'h_avg_goals_scored_last_5': h_st['goals_scored'], 'h_avg_goals_conceded_last_5': h_st['goals_conceded'],
                'h_avg_points_last_5': h_st['points'], 'h_xg_diff_last_5': h_st['xg_for'] - h_st['xg_against'],
                'a_rest_days': a_st['rest_days'],
                'a_avg_xg_for_last_5': a_st['xg_for'], 'a_avg_xg_against_last_5': a_st['xg_against'],
                'a_avg_ppda_last_5': a_st['ppda'], 'a_avg_deep_last_5': a_st['deep'],
                'a_avg_goals_scored_last_5': a_st['goals_scored'], 'a_avg_goals_conceded_last_5': a_st['goals_conceded'],
                'a_avg_points_last_5': a_st['points'], 'a_xg_diff_last_5': a_st['xg_for'] - a_st['xg_against'],
                'elo_diff': h_elo - a_elo, 'rest_days_diff': h_st['rest_days'] - a_st['rest_days'],
                'h2h_home_pts': h2h, 'day_of_week': m.date.weekday(), 'month': m.date.month
            }

            feature_vector = [feat_dict[col] for col in expected_features]
            X_df = pd.DataFrame([feature_vector], columns=expected_features)

            X_scaled = scaler.transform(X_df)

            # 3. ИНФЕРЕНС (ТОЛЬКО RANDOM FOREST)
            probs = rf_out.predict_proba(X_scaled)[0] # [П2, Х, П1]
            prob_tot = rf_tot.predict_proba(X_scaled)[0][1] if rf_tot.classes_.shape[0] > 1 else 0.5
            pred_hg = max(0, round(float(rf_hg.predict(X_scaled)[0])))
            pred_ag = max(0, round(float(rf_ag.predict(X_scaled)[0])))

            # 4. СОХРАНЕНИЕ
            pred_record = session.query(Prediction).filter(Prediction.match_id == m.id).first()
            if not pred_record:
                pred_record = Prediction(match_id=m.id)
                session.add(pred_record)

            pred_record.prob_a = float(probs[0])
            pred_record.prob_d = float(probs[1])
            pred_record.prob_h = float(probs[2])
            
            idx = np.argmax(probs)
            out_str = ['Win Away', 'Draw', 'Win Home'][idx]
            
            pred_record.predicted_outcome = out_str
            pred_record.total_over_2_5_probability = float(prob_tot)
            pred_record.predicted_exact_score = f"{pred_hg}:{pred_ag}"
            pred_record.model_version = 'RandomForest_1.0'
            pred_record.created_at = datetime.utcnow()

            print(f"OK: {m.home_team.name} {pred_hg}:{pred_ag} {m.away_team.name} | Тотал > 2.5: {prob_tot*100:.1f}%")

        except Exception as e:
            print(f"Ошибка в матче {m.id}: {e}")

    session.commit()
    session.close()
    print("\nПрогнозы от Случайного леса успешно сохранены в БД!")

if __name__ == "__main__":
    generate_predictions_rf()