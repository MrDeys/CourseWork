import soccerdata as sd
import pandas as pd
import sys, os
from datetime import timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.tables import SessionLocal, League, Team, Match

LEAGUES_MAPPING = {
    'ENG-Premier League': 'Premier_League',
    'ESP-La Liga': 'La_Liga',
    'ITA-Serie A': 'Serie_A',
    'GER-Bundesliga': 'Bundesliga',
    'FRA-Ligue 1': 'Ligue_1'
}

SEASONS = ['1415','1516', '1617', '1718', '1819', '1920', '2021', '2122', '2223', '2324', '2425', '2526']

def get_or_create_league(session, league_name):
    league = session.query(League).filter(League.name == league_name).first()
    if not league:
        league = League(name=league_name, country=league_name.split('-')[0])
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

def load_data():
    session = SessionLocal()
    
    print("1. Подключение к Understat и ClubElo...")
    understat = sd.Understat(leagues=list(LEAGUES_MAPPING.keys()), seasons=SEASONS)
    club_elo = sd.ClubElo()

    print("2. Скачивание расписания (все матчи)...")
    df_schedule = understat.read_schedule().reset_index()
    
    print("3. Скачивание статистики (сыгранные матчи)...")
    df_stats = understat.read_team_match_stats().reset_index()
    
    df = pd.merge(df_schedule, df_stats, on=['date', 'home_team', 'away_team', 'league', 'season'], how='left', suffixes=('', '_extra'))
    
    print(f"Всего матчей в базе: {len(df)}")
    
    elo_cache = {}
    matches_processed = 0

    for index, row in df.iterrows():
        try:
            match_date = pd.to_datetime(row['date'])
            home_team_name = str(row['home_team'])
            away_team_name = str(row['away_team'])
            
            league_name = LEAGUES_MAPPING.get(row['league'], row['league'])
            league = get_or_create_league(session, league_name)
            h_team = get_or_create_team(session, home_team_name)
            a_team = get_or_create_team(session, away_team_name)
            
            unique_id = f"und_{match_date.strftime('%Y%m%d')}_{h_team.id}_{a_team.id}"
            
            match = session.query(Match).filter(Match.match_id == unique_id).first()
            if not match:
                match = Match(match_id=unique_id, league_id=league.id, 
                              home_team_id=h_team.id, away_team_id=a_team.id,
                              date=match_date, season=str(row['season']),
                              status="SCHEDULED")
                session.add(match)

            h_g = row.get('home_goals')
            a_g = row.get('away_goals')
            
            if pd.notna(h_g):
                match.home_goals = int(h_g)
                match.away_goals = int(a_g)
                match.status = "FINISHED"
                
                match.home_xg = float(row['home_xg']) if pd.notna(row.get('home_xg')) else None
                match.away_xg = float(row['away_xg']) if pd.notna(row.get('away_xg')) else None
                match.home_ppda = float(row['home_ppda']) if pd.notna(row.get('home_ppda')) else None
                match.away_ppda = float(row['away_ppda']) if pd.notna(row.get('away_ppda')) else None
                
                match.home_deep = int(row['home_deep_completions']) if pd.notna(row.get('home_deep_completions')) else None
                match.away_deep = int(row['away_deep_completions']) if pd.notna(row.get('away_deep_completions')) else None
            else:
                match.status = "SCHEDULED"

            elo_date_str = (match_date - timedelta(days=1)).strftime('%Y-%m-%d')
            if elo_date_str not in elo_cache:
                try:
                    elo_df = club_elo.read_by_date(elo_date_str).reset_index()
                    elo_cache[elo_date_str] = elo_df
                except: elo_cache[elo_date_str] = None
            
            curr_elo = elo_cache[elo_date_str]
            if curr_elo is not None:
                h_elo = curr_elo[curr_elo['team'] == home_team_name]
                a_elo = curr_elo[curr_elo['team'] == away_team_name]
                if not h_elo.empty: match.home_elo = float(h_elo.iloc[0]['elo'])
                if not a_elo.empty: match.away_elo = float(a_elo.iloc[0]['elo'])

            matches_processed += 1
            if matches_processed % 100 == 0:
                session.commit()
                print(f"Обработано {matches_processed} матчей...")

        except Exception as e:
            print(f"Ошибка в строке {index}: {e}")
            session.rollback()
            continue

    session.commit()
    session.close()
    print(f"Готово! Теперь в базе {matches_processed} матчей")

if __name__ == "__main__":
    load_data()