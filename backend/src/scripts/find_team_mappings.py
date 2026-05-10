import time
import os, sys
from datetime import datetime, timedelta
import soccerdata as sd
from thefuzz import process 
from sqlalchemy import or_

# --- НАСТРОЙКА ПУТЕЙ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..', '..')))
from src.database.tables import SessionLocal, Match, Team

MANUAL_ELO_MAP = {
    "Paris Saint Germain": "Paris SG",
    "Athletic Club": "Athletic Bilbao",
    "Saint-Etienne": "St Etienne",
    "Manchester United": "Man United",
    "Manchester City": "Man City",
    "Atletico Madrid": "Atlético Madrid",
    "Milan": "AC Milan",
    "Inter": "Inter Milan",
    "Borussia Dortmund": "Dortmund",
    "Borussia M.Gladbach": "M'gladbach",
    "Real Sociedad": "R Sociedad",
    "RasenBallsport Leipzig": "RB Leipzig",
    "FC Cologne": "FC Köln",
    "Almeria": "Almería",
    "Deportivo La Coruna": "Dep. La Coruna",
    "Mainz 05": "Mainz",
    "Hannover 96": "Hannover",
    "Nuernberg": "Nürnberg",
    "Greuther Fuerth": "Fürth",
    "West Bromwich Albion": "West Brom",
    "Parma Calcio 1913": "Parma",
    "Sporting Gijon": "Sporting Gijón",
}

def auto_sync_elo():
    session = SessionLocal()
    club_elo = sd.ClubElo()
    
    print("--- ШАГ 1: ПОЛНАЯ ИНИЦИАЛИЗАЦИЯ ИМЕН ---")
    db_teams = session.query(Team).all()
    
    try:
        current_elo_df = club_elo.read_by_date(datetime.utcnow().strftime('%Y-%m-%d'))
        elo_names_list = current_elo_df.index.get_level_values('team').unique().tolist()
    except Exception as e:
        print(f"❌ Ошибка ClubElo: {e}")
        return

    team_mapping = {}
    for team in db_teams:
        if team.name in MANUAL_ELO_MAP:
            team_mapping[team.name] = MANUAL_ELO_MAP[team.name]
        else:
            match, score = process.extractOne(team.name, elo_names_list)
            team_mapping[team.name] = match if score > 85 else team.name

    print("--- ШАГ 2: ЗАПОЛНЕНИЕ ВСЕЙ ИСТОРИИ (БЕЗ ОГРАНИЧЕНИЙ) ---")
    # Убираем все фильтры по датам, чтобы заполнить вообще всё
    missing_matches = session.query(Match).filter(
        or_(Match.home_elo == None, Match.away_elo == None)
    ).order_by(Match.date.asc()).all()

    total = len(missing_matches)
    print(f"🔥 В базе {total} матчей без Elo. Начинаем долгий процесс...")
    
    elo_cache = {}
    processed_count = 0

    for match in missing_matches:
        try:
            elo_date_str = (match.date - timedelta(days=1)).strftime('%Y-%m-%d')
            
            if elo_date_str not in elo_cache:
                time.sleep(1.0) # Минимальная пауза
                try:
                    day_elo_df = club_elo.read_by_date(elo_date_str)
                    elo_cache[elo_date_str] = day_elo_df.reset_index().set_index('team')
                except:
                    elo_cache[elo_date_str] = None
                    continue

            day_data = elo_cache.get(elo_date_str)
            if day_data is not None:
                h_elo_name = team_mapping.get(match.home_team.name)
                a_elo_name = team_mapping.get(match.away_team.name)

                if h_elo_name in day_data.index: match.home_elo = float(day_data.loc[h_elo_name, 'elo'])
                if a_elo_name in day_data.index: match.away_elo = float(day_data.loc[a_elo_name, 'elo'])

            processed_count += 1
            if processed_count % 50 == 0:
                session.commit()
                print(f"✅ Прогресс: {processed_count} / {total} | Дата: {elo_date_str}")

        except Exception as e:
            print(f"❌ Ошибка в матче {match.id}: {e}")
            session.rollback()

    session.commit()
    session.close()
    print("\n✨ ВСЯ история ELO заполнена!")

if __name__ == "__main__":
    auto_sync_elo()