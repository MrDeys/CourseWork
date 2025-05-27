import pandas as pd
import os
import datetime

def current_year() -> int:
    now = datetime.datetime.now()
    year = now.year
    if now.month <= 7:
        year -= 1
    return year

def load_all_data(leagues_dir: str, predicts_dir: str) -> pd.DataFrame:
    all_matches = []
    all_predicts = []

    project_dir = os.getcwd()
    current_season = str(current_year())

    full_leagues_dir = os.path.join(project_dir, leagues_dir)

    for league_name in os.listdir(full_leagues_dir):
        league_dir = os.path.join(full_leagues_dir, league_name)
            
        current_season_dir = os.path.join(league_dir, current_season)
        match_dir = os.path.join(current_season_dir, 'data.csv')

        if os.path.exists(match_dir):
            try:
                df_match = pd.read_csv(match_dir, parse_dates=['utcDate'])

                df_match['utcDate'] = df_match['utcDate'].dt.tz_convert(None)
                all_matches.append(df_match)
            except Exception as e:
                print(f"Ошибка при чтении или обработке файла данных матчей {match_dir}: {e}")

    df_data = pd.concat(all_matches, ignore_index=True)
    df_data['merge_date'] = df_data['utcDate'].dt.date

    full_predicts_dir = os.path.join(project_dir, predicts_dir)

    for prebict_name in os.listdir(full_predicts_dir):
        predict_dir = os.path.join(full_predicts_dir, prebict_name)
        try:
            df_predict = pd.read_csv(predict_dir, parse_dates=['Date'])
            df_predict['merge_date'] = df_predict['Date'].dt.date
                    
            df_predict_processed = df_predict.rename(columns={
                'Home_Team': 'homeTeam_name',
                'Away_Team': 'awayTeam_name',
                })[['merge_date', 'homeTeam_name', 'awayTeam_name', 
                    'Predicted_Outcome', 'Prob_A', 'Prob_D', 'Prob_H']]
            all_predicts.append(df_predict_processed)
        except Exception as e:
            print(f"Ошибка при чтении файла прогнозов {prebict_name}: {e}")

    df_all_predictions = pd.concat(all_predicts, ignore_index=True)

    result_df = pd.merge(
        df_data,                 
        df_all_predictions,     
        on=['merge_date', 'homeTeam_name', 'awayTeam_name'],
        how='left'            
    )
    result_df = result_df.drop(columns=['merge_date'])

    prob_cols = ['Prob_A', 'Prob_D', 'Prob_H']
    for col in prob_cols:
         if col not in result_df.columns:
             result_df[col] = pd.NA
         result_df[col] = pd.to_numeric(result_df[col], errors='coerce')

    if 'Predicted_Outcome' not in result_df.columns:
         result_df['Predicted_Outcome'] = pd.NA
    return result_df