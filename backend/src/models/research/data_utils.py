import pandas as pd
import os
import joblib
from sklearn.preprocessing import StandardScaler
import json

MODELS_SAVED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../models/saved'))

def get_prepared_data(data_path=None):
    if data_path is None:
        data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dataset/ml_dataset.csv'))
    
    df = pd.read_csv(data_path).sort_values(by='date').reset_index(drop=True)

    cols_to_drop = ['id', 'date', 'league_id', 'home_team_id', 'away_team_id', 
                    'target_outcome', 'target_total_2_5', 'target_home_goals', 'target_away_goals']
    # ... предыдущий код ...
    feature_cols = [col for col in df.columns if col not in cols_to_drop]

    # ВАЖНО: Мы сохраняем X как DataFrame, а не как .values
    X_df = df[feature_cols]
    y_out = df['target_outcome'].values
    y_tot = df['target_total_2_5'].values
    y_hg = df['target_home_goals'].values
    y_ag = df['target_away_goals'].values

    split_idx = int(len(df) * 0.8)
    
    # Делим DataFrame
    X_train_df = X_df.iloc[:split_idx]
    X_test_df = X_df.iloc[split_idx:]
    
    scaler = StandardScaler()
    # Скейлер обучается на DataFrame и автоматически запоминает feature_names_in_
    X_train_scaled = scaler.fit_transform(X_train_df)
    X_test_scaled = scaler.transform(X_test_df)

    save_dir = os.path.join(MODELS_SAVED_DIR, 'shared_scaler.pkl')
    os.makedirs(os.path.dirname(save_dir), exist_ok=True)
    joblib.dump(scaler, save_dir)

    data = {
        'X_train': X_train_scaled, 'X_test': X_test_scaled,
        'y_out_train': y_out[:split_idx], 'y_out_test': y_out[split_idx:],
        'y_tot_train': y_tot[:split_idx], 'y_tot_test': y_tot[split_idx:],
        'y_hg_train': y_hg[:split_idx], 'y_hg_test': y_hg[split_idx:],
        'y_ag_train': y_ag[:split_idx], 'y_ag_test': y_ag[split_idx:],
        'feature_names': feature_cols
    }
    return data

def save_config(best_params, d, name_id):
    config = {
        'hidden_size': int(best_params.get('hidden_size', 64)),
        'num_layers': int(best_params.get('num_layers', 1)),
        'dropout_rate': float(best_params.get('dropout', 0.3)),
        'input_size': d['X_train'].shape[1] 
    }

    config_path = os.path.join(MODELS_SAVED_DIR, f'config_{name_id}.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

    print(f"Конфигурация модели сохранена")
    