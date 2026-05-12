import soccerdata as sd
import pandas as pd
import numpy as np
import sys, os, time
from datetime import datetime, timedelta

# Авто-определение путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..', '..')))

from src.database.tables import SessionLocal, League, Team, Match

LEAGUES_MAPPING = {
    'ENG-Premier League': 'Premier_League', 
    'ESP-La Liga': 'La_Liga',
    'ITA-Serie A': 'Serie_A', 
    'GER-Bundesliga': 'Bundesliga', 
    'FRA-Ligue 1': 'Ligue_1'
}

# Используем правильные ID сезонов для SoccerData
SEASONS = ['1415','1516','1617','1718','1819','1920','2021','2122','2223','2324','2425', '2526'] 

MANUAL_ELO_MAP = {
    "Paris Saint Germain": "Paris SG", "Athletic Club": "Athletic Bilbao",
    "Manchester United": "Man United", "Manchester City": "Man City",
    "Atletico Madrid": "Atlético Madrid", "Milan": "AC Milan", "Inter": "Inter Milan",
    "Borussia Dortmund": "Dortmund", "RasenBallsport Leipzig": "RB Leipzig",
}

def get_or_create_league(session, league_name):
    league = session.query(League).filter(League.name == league_name).first()
    if not league:
        league = League(name=league_name, country=league_name.split('_')[0])
        session.add(league)
        session.commit()
        session.refresh(league)
    return league

def get_or_create_team(session, team_name):
    team = session.query(Team).filter(Team.name == team_name).first()
    if not team:
        team = Team(name=team_name)
        session.add(team)
        session.commit()
        session.refresh(team)
    return team

def _clean_val(val, val_type=float):
    if pd.isna(val) or val is None or val == "": return None
    try: return val_type(val)
    except: return None

def load_data():
    session = SessionLocal()
    print("🚀 Умная загрузка данных (Дельта-обновление)...")
    
    now = datetime.now()
    elo_start_date = now - timedelta(days=10)
    elo_end_date = now + timedelta(days=30)

    try:
        understat = sd.Understat(leagues=list(LEAGUES_MAPPING.keys()), seasons=SEASONS)
        club_elo = sd.ClubElo()

        print("📡 Чтение расписания Understat...")
        df_schedule = understat.read_schedule().reset_index()
        print("📡 Чтение статистики команд...")
        df_stats = understat.read_team_match_stats().reset_index()
        
        df = pd.merge(df_schedule, df_stats, on=['date', 'home_team', 'away_team', 'league', 'season'], how='left', suffixes=('', '_extra'))
        
        elo_cache = {}
        processed = 0
        updated = 0

        for _, row in df.iterrows():
            match_date = pd.to_datetime(row['date']).replace(tzinfo=None)
            h_team_name = str(row['home_team'])
            a_team_name = str(row['away_team'])
            
            uid = f"und_{match_date.strftime('%Y%m%d')}_{h_team_name}_{a_team_name}"
            match = session.query(Match).filter(Match.match_id == uid).first()
            
            h_g = _clean_val(row.get('home_goals'), int)

            # Пропускаем, если матч уже полностью обработан (есть счет и xG)
            if match and match.status == "FINISHED" and match.home_xg is not None:
                continue

            if not match:
                league_name = LEAGUES_MAPPING.get(row['league'], row['league'])
                league = get_or_create_league(session, league_name)
                h_team_obj = get_or_create_team(session, h_team_name)
                a_team_obj = get_or_create_team(session, a_team_name)
                
                match = Match(match_id=uid, league_id=league.id, home_team_id=h_team_obj.id, away_team_id=a_team_obj.id, 
                              date=match_date, season=str(row['season']), status="SCHEDULED")
                session.add(match)
                session.flush() # Фиксируем в сессии, чтобы ID заполнились

            # Обновляем результат
            if h_g is not None:
                match.home_goals = h_g
                match.away_goals = _clean_val(row.get('away_goals'), int)
                match.status = "FINISHED"
                match.home_xg = _clean_val(row.get('home_xg'), float)
                match.away_xg = _clean_val(row.get('away_xg'), float)
                match.home_ppda = _clean_val(row.get('home_ppda'), float)
                match.away_ppda = _clean_val(row.get('away_ppda'), float)
                match.home_deep = _clean_val(row.get('home_deep_completions'), int)
                match.away_deep = _clean_val(row.get('away_deep_completions'), int)
                updated += 1

            # Обновление ELO (только в окне дат)
            if elo_start_date <= match_date <= elo_end_date:
                elo_date_str = (match_date - timedelta(days=1)).strftime('%Y-%m-%d')
                if elo_date_str not in elo_cache:
                    try:
                        time.sleep(1)
                        elo_cache[elo_date_str] = club_elo.read_by_date(elo_date_str).reset_index().set_index('team')
                    except: elo_cache[elo_date_str] = None
                
                curr_elo_df = elo_cache[elo_date_str]
                if curr_elo_df is not None:
                    h_elo_name = MANUAL_ELO_MAP.get(h_team_name, h_team_name)
                    a_elo_name = MANUAL_ELO_MAP.get(a_team_name, a_team_name)
                    
                    if h_elo_name in curr_elo_df.index: 
                        match.home_elo = float(curr_elo_df.loc[h_elo_name, 'elo'])
                    if a_elo_name in curr_elo_df.index: 
                        match.away_elo = float(curr_elo_df.loc[a_elo_name, 'elo'])

            processed += 1
            if processed % 100 == 0:
                session.commit()

        session.commit()
        print(f"✅ Успех! Проверено: {processed}, Обновлено результатов: {updated}.")
    except Exception as e:
        print(f"❌ Ошибка в load_data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    load_data()