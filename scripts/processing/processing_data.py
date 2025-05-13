import pandas as pd
import numpy as np
import os
import re
import glob
import datetime
import ast

LEAGUES_DIR = 'leagues'
PROCESSED_DIR = 'leagues_processed'
CURRENT_SEASON = datetime.datetime.now().year

if datetime.datetime.now().month <= 6:
    CURRENT_SEASON -= 1

LEAGUES = {
    'Premier_League': 39,
    'La_Liga': 140,
    'Serie_A': 135,
    'Bundesliga': 78,
    'Ligue_1': 61,
}
LEAGUES_ID = set(LEAGUES.values())

TEAMS_DIR = 'leagues/.teams/data.csv'

HISTORY_DATA = {
    #'fixture_id': 'Fixture_ID',
    'fixture_date': 'Date',
    'league_id': 'League_ID',
    'league_season': 'Season',
    'teams_home_name': 'Home_Team',
    'teams_away_name': 'Away_Team',
    'goals_home': 'Home_Goals',
    'goals_away': 'Away_Goals',
    'score_halftime_home': 'Home_Goals_Time',
    'score_halftime_away': 'Away_Goals_Time',
    'fixture_status_short': 'Status',
    'fixture_referee': 'Referee',
}

CURRENT_DATA = {
    #'id': 'Fixture_ID',
    'utcDate': 'Date',
    'competition_id': 'League_ID',
    'homeTeam_name': 'Home_Team',
    'awayTeam_name': 'Away_Team',
    'score_fullTime_home': 'Home_Goals',
    'score_fullTime_away': 'Away_Goals',
    'score_halfTime_home': 'Home_Goals_Time',
    'score_halfTime_away': 'Away_Goals_Time',
    'status': 'Status',
    'referees': 'Referee',
}

CURRENT_FORM = 5 

def load_teams(filepath):
    """Загружает команды из CSV файла и возвращает словарь с alias и canonical_name"""
    try:
        df = pd.read_csv(filepath)
        df.dropna(subset=['alias', 'canonical_name'], inplace=True)
        teams = df.set_index('alias')['canonical_name'].to_dict()
        return teams
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
        return {}

def shorten_name(surname):
  if not surname or not isinstance(surname, str):
    return "" # Возвращаем пустую строку для None или нестроковых типов

  s_name = surname.strip().split()

  if len(s_name) == 0:
    return "" # Если имя состояло только из пробелов
  elif len(s_name) == 1:
    return s_name[0]
  else:
    first_initial = s_name[0][0].upper()
    last_name = s_name[-1]
    return f"{first_initial}. {last_name}"

def referee_name(info):
    """Извлекает имя главного судьи из строки"""
    if pd.isna(info) or not isinstance(info, str) or not info.strip():
        return np.nan
    
    info = info.strip()
    fullname = info 

    if info.startswith('[') and info.endswith(']'):
        try:
            ref_list = ast.literal_eval(info)
            if isinstance(ref_list, list) and ref_list:
                first_ref = ref_list[0]
                if isinstance(first_ref, dict) and 'name' in first_ref:
                    extracted_name = first_ref['name']
                    if isinstance(extracted_name, str) and extracted_name.strip():
                        f_name = extracted_name.strip()
                        s_name = f_name.split()

                        if len(s_name) >= 2:
                            return s_name[-1]
                        else:
                            return f_name
        except (ValueError, SyntaxError, TypeError):
            pass

    surname = fullname.split()
    if len(surname) >= 2:
        return surname[-1]
        
    return fullname

def load_data(leagues_dir, leagues, current_season, history_data, current_data):
    """Загружает данные из файлов и объединяет их в один DataSet"""
    all_dfs = []
    file_pattern = os.path.join(leagues_dir, '*', '*', 'data.csv')
    all_files = glob.glob(file_pattern)
    print(f"Обработка файлов: {len(all_files)}")
    processed_files = 0

    for f_path in all_files:
        try:
            s_name = f_path.split(os.sep)

            year_dir = s_name[-2]
            league_name_dir = s_name[-3]
            league_id = leagues.get(league_name_dir)

            year = int(year_dir)
            is_current = (year == current_season)
            type_data = "Current" if is_current else "History"
            actual_data = current_data if is_current else history_data

            df = pd.read_csv(f_path)

            keys = list(actual_data.keys())
            cols_in_file = [col for col in keys if col in df.columns]

            df = df[cols_in_file].copy()
            df.rename(columns=actual_data, inplace=True)
            df['League_ID'] = league_id

            df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.tz_localize(None)
            df.dropna(subset=['Date'], inplace=True)

            numeric_cols = ['Home_Goals', 'Away_Goals', 'Home_Goals_Time', 'Away_Goals_Time']
            for col in numeric_cols:
                if col in df.columns: 
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                else: df[col] = np.nan

            if 'Referee' in df.columns:
                df['RefereeName'] = df['Referee'].apply(referee_name)
                if 'Referee' in df.columns and 'Referee' != 'RefereeName':
                     df.drop(columns=['Referee'], inplace=True, errors='ignore')
            else:
                df['RefereeName'] = np.nan

            if not is_current:
                df.dropna(subset=['Home_Goals', 'Away_Goals'], inplace=True)

            for col in ['Home_Goals', 'Away_Goals', 'Home_Goals_Time', 'Away_Goals_Time']:
                if col in df.columns and df[col].notna().all():
                    df[col] = df[col].astype(int)

            df['Year'] = year
            df['DataSourceType'] = type_data
            all_dfs.append(df)
            processed_files += 1

        except Exception as e:
            print(f"Неожиданная ошибка при обработке файла {f_path}: {e}")

    result_df = pd.concat(all_dfs, ignore_index=True)
    return result_df

def team_names(df, mapping):
    """Применяет сопоставление имен команд"""
    df['Home_Team'] = df['Home_Team'].replace(mapping)
    df['Away_Team'] = df['Away_Team'].replace(mapping)
    return df

def create_main_variables(df):
    """Создает основные переменные: Исход, Тотал, Точный счет"""
    mask = df['Home_Goals'].notna() & df['Away_Goals'].notna()
    
    df['Outcome'] = pd.Series(dtype='object')
    df.loc[mask & (df['Home_Goals'] > df['Away_Goals']), 'Outcome'] = 'H'
    df.loc[mask & (df['Home_Goals'] == df['Away_Goals']), 'Outcome'] = 'D'
    df.loc[mask & (df['Home_Goals'] < df['Away_Goals']), 'Outcome'] = 'A'

    df['Total_Goals'] = np.nan
    df.loc[mask, 'Total_Goals'] = df.loc[mask, 'Home_Goals'] + df.loc[mask, 'Away_Goals']

    df['Exact_Score'] = pd.Series(dtype='object')
    df.loc[mask, 'Exact_Score'] = df.loc[mask, 'Home_Goals'].astype(int).astype(str) + '-' + df.loc[mask, 'Away_Goals'].astype(int).astype(str)
    return df

def calculate_current_form_team(df, form=5):
    """Рассчитывает признаки на основе последних результатов матчей."""
    if 'League_ID' not in df.columns: return df
    df = df.sort_values(by=['League_ID', 'Date']).reset_index(drop=True)

    if 'Fixture_ID' in df.columns and not df['Fixture_ID'].isnull().all() and df['Fixture_ID'].unique():
        match_id = 'Fixture_ID'
    else:
        df['temp_match_id'] = df.index
        match_id = 'temp_match_id'

    df_home = df[[match_id, 'League_ID', 'Date', 'Home_Team', 'Away_Team', 'Home_Goals', 'Away_Goals']].rename(
        columns={'Home_Team': 'Team', 'Away_Team': 'Opponent',
                 'Home_Goals': 'Goals_Scored', 'Away_Goals': 'Goals_Conceded'}
    )
    df_home['Location'] = 'Home'
    df_away = df[[match_id, 'League_ID', 'Date', 'Away_Team', 'Home_Team', 'Away_Goals', 'Home_Goals']].rename(
        columns={'Away_Team': 'Team', 'Home_Team': 'Opponent',
                 'Away_Goals': 'Goals_Scored', 'Home_Goals': 'Goals_Conceded'}
    )
    df_away['Location'] = 'Away'

    df_long = pd.concat([df_home, df_away], ignore_index=True)
    df_long.sort_values(by=['League_ID', 'Team', 'Date'], inplace=True)

    df_long['Points'] = np.nan
    mask_result = df_long['Goals_Scored'].notna() & df_long['Goals_Conceded'].notna()
    df_long.loc[mask_result & (df_long['Goals_Scored'] > df_long['Goals_Conceded']), 'Points'] = 3
    df_long.loc[mask_result & (df_long['Goals_Scored'] == df_long['Goals_Conceded']), 'Points'] = 1
    df_long.loc[mask_result & (df_long['Goals_Scored'] < df_long['Goals_Conceded']), 'Points'] = 0

    stats_cols = ['Goals_Scored', 'Goals_Conceded', 'Points']
    grouped = df_long.groupby(['League_ID', 'Team'])

    def avg_form(series, window):
        return series.shift(1).rolling(window=window, min_periods=1).mean()

    for col in stats_cols:
        df_long[f'Avg_{col}_Last{form}'] = grouped[col].transform(avg_form, window=form)

    for col in stats_cols:
        df_long[f'Avg_{col}_Home_Last{form}'] = np.nan
        df_long[f'Avg_{col}_Away_Last{form}'] = np.nan

        home_mask = df_long['Location'] == 'Home'
        df_long.loc[home_mask, f'Avg_{col}_Home_Last{form}'] = grouped[col].transform(
            lambda x: avg_form(x[home_mask.loc[x.index]], window=form)
        )
        away_mask = df_long['Location'] == 'Away'
        df_long.loc[away_mask, f'Avg_{col}_Away_Last{form}'] = grouped[col].transform(
             lambda x: avg_form(x[away_mask.loc[x.index]], window=form)
        )

        df_long[f'Avg_{col}_Home_Last{form}'] = grouped[f'Avg_{col}_Home_Last{form}'].ffill()
        df_long[f'Avg_{col}_Away_Last{form}'] = grouped[f'Avg_{col}_Away_Last{form}'].ffill()
        df_long[f'Avg_{col}_Home_Last{form}'] = grouped[f'Avg_{col}_Home_Last{form}'].bfill()
        df_long[f'Avg_{col}_Away_Last{form}'] = grouped[f'Avg_{col}_Away_Last{form}'].bfill()

    special_cols = [col for col in df_long.columns if col.startswith('Avg_')]
    df_long[special_cols] = df_long[special_cols].fillna(0)

    all_special_cols = [col for col in df_long.columns if col.startswith('Avg_')]
    special = df_long[[match_id, 'Team', 'Location'] + all_special_cols]

    special_home = special[special['Location'] == 'Home'].drop(columns='Location').set_index(match_id).add_suffix('_Home')
    special_away = special[special['Location'] == 'Away'].drop(columns='Location').set_index(match_id).add_suffix('_Away')

    df = df.merge(special_home, left_on=match_id, right_index=True, how='left')
    df = df.merge(special_away, left_on=match_id, right_index=True, how='left')

    cols_merge = [col for col in df.columns if '_Home' in col or '_Away' in col]
    df[cols_merge] = df[cols_merge].fillna(0)

    if match_id == 'temp_match_id': df.drop(columns=['temp_match_id'], inplace=True, errors='ignore')

    for col in stats_cols: 
        home_col = f'Avg_{col}_Last{form}_Home'
        away_col = f'Avg_{col}_Last{form}_Away'
        if home_col in df.columns and away_col in df.columns:
            df[f'Diff_Avg_{col}_Last{form}'] = df[home_col] - df[away_col]

        home_col_venue = f'Avg_{col}_Home_Last{form}_Home'
        away_col_venue = f'Avg_{col}_Away_Last{form}_Away'
        if home_col_venue in df.columns and away_col_venue in df.columns:
            df[f'Diff_Avg_{col}_Venue_Last{form}'] = df[home_col_venue] - df[away_col_venue]

    diff_cols = [col for col in df.columns if col.startswith('Diff_')]
    df[diff_cols] = df[diff_cols].fillna(0)

    return df

def correct_filename(name):
    """Удаляет или заменяет недопустимые символы в имени файла."""
    name = re.sub(r'[^\w\-]+', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name


if __name__ == "__main__":
    print("Обработка данных...")

    teams = load_teams(TEAMS_DIR)

    result_df = load_data(
        LEAGUES_DIR,
        LEAGUES,
        CURRENT_SEASON,
        HISTORY_DATA, 
        CURRENT_DATA  
    )

    result_df.dropna(subset=['League_ID'], inplace=True)
    result_df['League_ID'] = result_df['League_ID'].astype(int)

    result_df = result_df[result_df['League_ID'].isin(LEAGUES_ID)].copy()

    result_df = team_names(result_df, teams)

    result_df = result_df.sort_values(by='Date').reset_index(drop=True)
    result_df.drop_duplicates(inplace=True)
    key_cols = ['Date', 'Home_Team', 'Away_Team', 'League_ID']
    key_cols = [col for col in key_cols if col in result_df.columns]
    if len(key_cols) == 4:
        result_df.drop_duplicates(subset=key_cols, keep='last', inplace=True)

    result_df = create_main_variables(result_df)

    result_df = calculate_current_form_team(result_df, form=CURRENT_FORM)

    cols_drop = ['HomeTeamID_API', 'AwayTeamID_API', 'OddsMsg', 'Time', 'LeagueName', 'Status', 'Year', 'DataSourceType', 'Fixture_ID', 'Referee']
    cols_existing = [col for col in cols_drop if col in result_df.columns]
    result_df.drop(columns=cols_existing, inplace=True, errors='ignore')
    result_df['Month'] = result_df['Date'].dt.month
    result_df['DayOfWeek'] = result_df['Date'].dt.dayofweek

    print("\nИтоговая структура данных")
    result_df.info(verbose=True, show_counts=True)

    print(f"\nСохранение данных по лигам")
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    unique_league_ids = sorted(result_df['League_ID'].unique())

    result_df.loc[result_df['Season'].isnull(), 'Season'] = CURRENT_SEASON

    for league_id in unique_league_ids:
        league_df = result_df[result_df['League_ID'] == league_id].copy()
        if league_df.empty: continue

        league_folder = None
        for dirname, lid in LEAGUES.items():
            if lid == league_id:
                league_folder = dirname
                break

        new_name = correct_filename(league_folder)

        final_filename = f"{new_name}.csv"
        final_path = os.path.join(PROCESSED_DIR, final_filename)

        try:
            league_df.to_csv(final_path, index=False)
            print(f"Лига {league_folder} сохраненa")
        except Exception as e:
            print(f"Ошибка при сохранении файла для лиги ID {league_id}: {e}")

    print("\nОбработка и сохранение данных по лигам завершены")