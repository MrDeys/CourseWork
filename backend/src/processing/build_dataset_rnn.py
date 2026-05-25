import pandas as pd
import numpy as np
import pickle
import os, sys

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
    df = df.dropna().reset_index(drop=True)
    return df

def build_rnn_dataset(seq_length=5):
    df = get_raw_data()
    print(f"Загружено {len(df)} завершенных матчей.")

    all_teams = pd.concat([df['home_team_id'], df['away_team_id']]).unique()
    team_histories = {team: [] for team in all_teams}

    dataset = []

    for index, row in df.iterrows():
        home_id = row['home_team_id']
        away_id = row['away_team_id']

        h_hist = team_histories[home_id][-seq_length:]
        a_hist = team_histories[away_id][-seq_length:]

        if len(h_hist) == seq_length and len(a_hist) == seq_length:
            
            target_outcome = 1 
            if row['home_goals'] > row['away_goals']: target_outcome = 2 
            elif row['home_goals'] < row['away_goals']: target_outcome = 0 
            
            target_total_2_5 = 1 if (row['home_goals'] + row['away_goals']) > 2 else 0

            context_features = [
                row['home_elo'] or 1500.0,
                row['away_elo'] or 1500.0,
                row['home_elo'] - row['away_elo']
            ]

            dataset.append({
                'date': row['date'],
                'home_seq': np.array(h_hist, dtype=np.float32), 
                'away_seq': np.array(a_hist, dtype=np.float32), 
                'context': np.array(context_features, dtype=np.float32),
                'target_outcome': target_outcome,
                'target_total': target_total_2_5,
                'target_home_goals': float(row['home_goals']),
                'target_away_goals': float(row['away_goals'])
            })

        h_pts = 3 if row['home_goals'] > row['away_goals'] else (1 if row['home_goals'] == row['away_goals'] else 0)
        a_pts = 3 if row['away_goals'] > row['home_goals'] else (1 if row['home_goals'] == row['away_goals'] else 0)

        team_histories[home_id].append([
            1.0, 
            row['home_goals'], row['away_goals'], 
            row['home_xg'], row['away_xg'],      
            row['home_ppda'], row['home_deep'],  
            row['away_elo'] or 1500.0,           
            h_pts                               
        ])

        team_histories[away_id].append([
            0.0, 
            row['away_goals'], row['home_goals'],
            row['away_xg'], row['home_xg'],       
            row['away_ppda'], row['away_deep'],  
            row['home_elo'] or 1500.0,           
            a_pts                                 
        ])

    save_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../dataset/rnn_dataset.pkl'))
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    with open(save_path, 'wb') as f:
        pickle.dump(dataset, f)

    print(f"Датасет для LSTM/GRU готов!")
    print(f"Собрано {len(dataset)} матчей с историей длиной {seq_length}.")
    print(f"Файл сохранен: {save_path}")

    print("\nПример структуры данных для входа в PyTorch:")
    print(f"home_seq shape: {dataset[-1]['home_seq'].shape} (Матчей, Признаков)")
    print(f"away_seq shape: {dataset[-1]['away_seq'].shape} (Матчей, Признаков)")
    print(f"context shape: {dataset[-1]['context'].shape}")

if __name__ == "__main__":
    build_rnn_dataset(seq_length=5)