import pandas as pd
import os, sys
from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.tables import SessionLocal, Match, engine

def get_raw_data() -> pd.DataFrame:
    query = """
        SELECT id, date, league_id, home_team_id, away_team_id, 
               home_goals, away_goals, home_xg, away_xg, 
               home_ppda, away_ppda, home_deep, away_deep,
               home_elo, away_elo
        FROM matches
        WHERE status = 'FINISHED'
        ORDER BY date ASC
    """
    df = pd.read_sql(query, engine)
    df['date'] = pd.to_datetime(df['date'])
    return df

def calculate_h2h(row, df_all, window=3):
    past_matches = df_all[
        (df_all['date'] < row['date']) &
        (((df_all['home_team_id'] == row['home_team_id']) & (df_all['away_team_id'] == row['away_team_id'])) |
         ((df_all['home_team_id'] == row['away_team_id']) & (df_all['away_team_id'] == row['home_team_id'])))
    ].tail(window)

    if len(past_matches) == 0:
        return 1.0 

    pts = 0
    for _, m in past_matches.iterrows():
        if m['home_team_id'] == row['home_team_id']:
            if m['home_goals'] > m['away_goals']: pts += 3
            elif m['home_goals'] == m['away_goals']: pts += 1
        else:
            if m['away_goals'] > m['home_goals']: pts += 3
            elif m['home_goals'] == m['away_goals']: pts += 1
            
    return pts / len(past_matches) 

def calculate_team_features(df: pd.DataFrame, window=5) -> pd.DataFrame:
    home_df = df[['date', 'home_team_id', 'home_goals', 'away_goals', 'home_xg', 'away_xg', 'home_ppda', 'home_deep']].copy()
    home_df.columns = ['date', 'team_id', 'goals_scored', 'goals_conceded', 'xg_for', 'xg_against', 'ppda', 'deep']
    home_df['is_home'] = 1

    away_df = df[['date', 'away_team_id', 'away_goals', 'home_goals', 'away_xg', 'home_xg', 'away_ppda', 'away_deep']].copy()
    away_df.columns = ['date', 'team_id', 'goals_scored', 'goals_conceded', 'xg_for', 'xg_against', 'ppda', 'deep']
    away_df['is_home'] = 0

    teams_history = pd.concat([home_df, away_df]).sort_values(by=['team_id', 'date'])

    teams_history['points'] = 0
    teams_history.loc[teams_history['goals_scored'] > teams_history['goals_conceded'], 'points'] = 3
    teams_history.loc[teams_history['goals_scored'] == teams_history['goals_conceded'], 'points'] = 1

    grouped = teams_history.groupby('team_id')
    
    teams_history['rest_days'] = grouped['date'].diff().dt.days
    teams_history['rest_days'] = teams_history['rest_days'].fillna(7) 
    teams_history['rest_days'] = teams_history['rest_days'].clip(upper=14)
    
    features = ['xg_for', 'xg_against', 'ppda', 'deep', 'goals_scored', 'goals_conceded', 'points']
    for col in features:
        teams_history[f'avg_{col}_last_{window}'] = grouped[col].transform(lambda x: x.rolling(window, min_periods=1).mean().shift(1))

    teams_history[f'xg_diff_last_{window}'] = teams_history[f'avg_xg_for_last_{window}'] - teams_history[f'avg_xg_against_last_{window}']

    return teams_history

def build_ml_dataset():
    df = get_raw_data()
    
    print("Вычисляем форму команд...")
    teams_history = calculate_team_features(df, window=5)

    feature_cols = ['date', 'team_id', 'rest_days', 'avg_xg_for_last_5', 'avg_xg_against_last_5', 
                    'avg_ppda_last_5', 'avg_deep_last_5', 'avg_goals_scored_last_5', 
                    'avg_goals_conceded_last_5', 'avg_points_last_5', 'xg_diff_last_5']

    df = pd.merge(df, teams_history[feature_cols], left_on=['date', 'home_team_id'], right_on=['date', 'team_id'], how='left')
    df = df.rename(columns={col: f'h_{col}' for col in feature_cols if col not in ['date', 'team_id']})
    df = df.drop('team_id', axis=1)

    df = pd.merge(df, teams_history[feature_cols], left_on=['date', 'away_team_id'], right_on=['date', 'team_id'], how='left')
    df = df.rename(columns={col: f'a_{col}' for col in feature_cols if col not in ['date', 'team_id']})
    df = df.drop('team_id', axis=1)

    df['home_elo'] = df['home_elo'].fillna(1500)
    df['away_elo'] = df['away_elo'].fillna(1500)
    df['elo_diff'] = df['home_elo'] - df['away_elo']
    df['rest_days_diff'] = df['h_rest_days'] - df['a_rest_days']

    print("Вычисляем статистику личных встреч (H2H)...")
    df['h2h_home_pts'] = df.apply(lambda row: calculate_h2h(row, df, window=3), axis=1)

    # Добавляем временные фичи
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month

    # Удаляем NaN (первые туры сезона, где еще нет истории)
    df = df.dropna()

    # --- ФОРМИРОВАНИЕ ТАРГЕТОВ (Целевых переменных) ---
    df['target_outcome'] = 1 
    df.loc[df['home_goals'] > df['away_goals'], 'target_outcome'] = 2
    df.loc[df['home_goals'] < df['away_goals'], 'target_outcome'] = 0

    df['target_total_2_5'] = ((df['home_goals'] + df['away_goals']) > 2).astype(int)
    df['target_home_goals'] = df['home_goals']
    df['target_away_goals'] = df['away_goals']

    # --- ОЧИСТКА И ONE-HOT ENCODING ---
    # 1. Удаляем сырые данные матча и ID команд
    columns_to_drop = ['id', 'home_team_id', 'away_team_id', 'home_goals', 'away_goals', 
                       'home_xg', 'away_xg', 'home_ppda', 'away_ppda', 'home_deep', 'away_deep']
    df = df.drop(columns=columns_to_drop)

    # 2. One-Hot Encoding для категориальных признаков (Лига, День недели, Месяц)
    # drop_first=True спасает от дамми-ловушки (мультиколлинеарности)
    df = pd.get_dummies(df, columns=['league_id', 'month', 'day_of_week'], drop_first=True)

    # 3. Сортировка по дате КРИТИЧЕСКИ ВАЖНА для Time-Series Split
    df = df.sort_values(by='date').reset_index(drop=True)

    # Сохранение (оставляем колонку date, она понадобится скрипту обучения для сплита, а потом мы ее удалим)
    save_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../dataset/ml_dataset.csv'))
    
    # Создаем директорию, если её нет
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    df.to_csv(save_path, index=False)
    
    print(f"✅ Датасет готов!")
    print(f"Количество строк: {len(df)}")
    print(f"Количество признаков (с учетом One-Hot): {len(df.columns)}")
    return df

if __name__ == "__main__":
    build_ml_dataset()