import time
from datetime import timedelta
import pandas as pd
import soccerdata as sd
from thefuzz import process 
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.tables import SessionLocal, Match, Team

def auto_sync_elo():
    session = SessionLocal()
    club_elo = sd.ClubElo()
    
    db_teams = [t.name for t in session.query(Team).all()]
    if not db_teams:
        print("Команды в базе не найдены. Сначала запусти основной парсер.")
        return

    print("Загружаем глобальный список имен из ClubElo...")
    try:
        current_elo_df = club_elo.read_by_date()
        elo_names_list = current_elo_df.index.get_level_values('team').unique().tolist()
    except Exception as e:
        print(f"Не удалось получить список имен ClubElo: {e}")
        return

    team_mapping = {}
    for team in db_teams:
        match, score = process.extractOne(team, elo_names_list)
        if score > 85: 
            team_mapping[team] = match
        else:
            team_mapping[team] = team 

    print(f"Сопоставление завершено. Найдено {len(team_mapping)} пар.")

    missing_matches = session.query(Match).filter(
        (Match.home_elo == None) | (Match.away_elo == None)
    ).order_by(Match.date.asc()).all()

    if not missing_matches:
        print("Пропусков Elo не обнаружено!")
        return

    print(f"Найдено {len(missing_matches)} матчей для обновления.")
    
    elo_cache = {}
    processed_count = 0

    for match in missing_matches:
        try:
            elo_date_str = (match.date - timedelta(days=1)).strftime('%Y-%m-%d')
            
            if elo_date_str not in elo_cache:
                time.sleep(1.3)
                try:
                    day_elo_df = club_elo.read_by_date(elo_date_str)
                    elo_cache[elo_date_str] = day_elo_df.reset_index().set_index('team')
                except Exception as e:
                    print(f"Ошибка загрузки даты {elo_date_str}. Возможно, бан.")
                    time.sleep(10)
                    elo_cache[elo_date_str] = None
                    continue

            day_data = elo_cache.get(elo_date_str)
            if day_data is not None:
                h_elo_name = team_mapping.get(match.home_team.name)
                a_elo_name = team_mapping.get(match.away_team.name)

                if h_elo_name in day_data.index:
                    match.home_elo = float(day_data.loc[h_elo_name, 'elo'])
                if a_elo_name in day_data.index:
                    match.away_elo = float(day_data.loc[a_elo_name, 'elo'])

            processed_count += 1
            
            if processed_count % 50 == 0:
                session.commit()
                print(f"--- Прогресс сохранен ({processed_count} матчей) ---")

        except Exception as e:
            print(f"Критическая ошибка на матче {match.id}: {e}")
            session.rollback()
            continue

    session.commit()
    session.close()
    print("\nСинхронизация полностью завершена!")

if __name__ == "__main__":
    auto_sync_elo()