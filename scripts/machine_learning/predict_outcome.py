import pandas as pd 
import numpy as np 
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import os
import joblib

LEAGUES = [
    'Premier_League',
    'La_liga', 
    'Serie_A',
    'Bundesliga', 
    'Ligue_1'
]

path_models = "models"
path_predicts = "predictions"
os.makedirs(f"{path_models}", exist_ok=True) 
os.makedirs(f"{path_predicts}", exist_ok=True)

def process_league(league_name):
    print(f"\nОбработка лиги: {league_name}")

    df_original = pd.read_csv(f'leagues_processed/{league_name}.csv')
    df_original['Date'] = pd.to_datetime(df_original['Date'])
    df_original['Outcome_str'] = df_original['Outcome']

    df_copy = df_original.copy()

    encoder_oc = LabelEncoder()
    encoder_oc.fit(df_copy['Outcome'].dropna())
    oc_classes = encoder_oc.classes_ 

    oc_map = {i: cls_name for i, cls_name in enumerate(oc_classes)}

    df_copy['Outcome_Encoded'] = df_copy['Outcome'].apply(lambda x: encoder_oc.transform([x])[0] if pd.notna(x) else np.nan)

    cols_drop = [
        'League_ID', 'Home_Goals', 'Away_Goals', 'Home_Goals_Time', 'Away_Goals_Time', 
        'Outcome',
        'Total_Goals', 'Exact_Score', 'Team_Home', 'Team_Away'
    ]
    df_processed = df_copy.drop(columns=cols_drop, errors='ignore')

    special_cols = ['Home_Team', 'Away_Team', 'RefereeName']

    encoders_cols = {}
    for col in special_cols:
        if col in df_processed.columns:
            le = LabelEncoder()
            df_processed[col] = le.fit_transform(df_processed[col].astype(str))
            encoders_cols[col] = le

    cols = [col for col in df_processed.columns if col not in ['Date', 'Outcome_str', 'Outcome_Encoded']]

    df_processed = df_processed.sort_values(by='Date').reset_index(drop=True)
    df_orig_future = df_original.sort_values(by='Date').reset_index(drop=True)

    train_mask = (df_processed['Date'] <= pd.to_datetime('2024-05-30')) & (df_processed['Outcome_Encoded'].notna())
    mask_predict_processed = (df_processed['Date'] >= pd.to_datetime('2025-05-01')) & (df_processed['Date'] <= pd.to_datetime('2025-05-31'))
    mask_predict_orig = (df_orig_future['Date'] >= pd.to_datetime('2025-05-01')) & (df_orig_future['Date'] <= pd.to_datetime('2025-05-31'))

    train_df = df_processed[train_mask].copy()

    df_predict_processed = df_processed[mask_predict_processed].copy()

    X_train = train_df[cols].copy()
    y_train = train_df['Outcome_Encoded'].astype(int)

    X_cols = X_train.copy()
    
    X_predict = df_predict_processed[cols].copy() if not df_predict_processed.empty else pd.DataFrame(columns=cols)

    scaler = StandardScaler()
    scaler.fit(X_cols)

    model = RandomForestClassifier(n_estimators=100, random_state=5, n_jobs=-1)
    model.fit(X_train, y_train)

    path_model = f'{path_models}/model_{league_name}.joblib'
    joblib.dump(model, path_model)
    path_encoders_cols = f'{path_models}/encoder_cols_{league_name}.joblib' 
    joblib.dump(encoders_cols, path_encoders_cols)
    path_encoders_oc = f'{path_models}/encoder_oc_{league_name}.joblib'
    joblib.dump(encoder_oc, path_encoders_oc)
    path_scaler = f'{path_models}/scaler_{league_name}.joblib'
    joblib.dump(scaler, path_scaler)

    X_predict_model = X_predict.copy()

    encoded_predicts = model.predict(X_predict_model)
    proba_predict = model.predict_proba(X_predict_model)

    predicts_str = [oc_map.get(p, 'Unknown') for p in encoded_predicts.astype(int)]

    predicts_df = df_original[mask_predict_orig].copy()

    predicts_df['Predicted_Outcome'] = predicts_str

    proba_cols = [f'Prob_{cls}' for cls in oc_classes]
    predicts_df[proba_cols] = proba_predict

    res_cols = ['Date', 'Season', 'Home_Team', 'Away_Team', 'Predicted_Outcome'] + proba_cols + ['Outcome_str']
    res_cols = [col for col in res_cols if col in predicts_df.columns]
    predicts_df = predicts_df[res_cols]
    path_predicts_df = f"{path_predicts}/predict_{league_name}.csv" 
    predicts_df.to_csv(path_predicts_df, index=False, float_format='%.2f')
    print(f"Лига: {league_name} обработана")

for league in LEAGUES:
    process_league(league)

print("\nВыполнены прогнозы для всех лиг")