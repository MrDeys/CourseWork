import time
from datetime import timedelta
import pandas as pd
import soccerdata as sd
from thefuzz import process # Библиотека для нечеткого сравнения
import os, sys

# Подключаем твою базу
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.tables import SessionLocal, Match, Team

def auto_sync_elo():
    session = SessionLocal()
    club_elo = sd.ClubElo()
    
    print("--- ШАГ 1: АВТОМАТИЧЕСКОЕ СОПОСТАВЛЕНИЕ ИМЕН КОМАНД ---")
    
    # 1. Берем все команды из твоей базы (Understat)
    db_teams = [t.name for t in session.query(Team).all()]
    if not db_teams:
        print("Команды в базе не найдены. Сначала запусти основной парсер.")
        return

    # 2. Получаем актуальный список имен из ClubElo (за текущую дату)
    print("Загружаем глобальный список имен из ClubElo...")
    try:
        current_elo_df = club_elo.read_by_date()
        elo_names_list = current_elo_df.index.get_level_values('team').unique().tolist()
    except Exception as e:
        print(f"Не удалось получить список имен ClubElo: {e}")
        return

    # Создаем словарь соответствий: { 'Understat Name': 'ClubElo Name' }
    team_mapping = {}
    for team in db_teams:
        # Ищем лучшее совпадение. scorer=process.fuzz.token_sort_ratio отлично справляется с перестановками слов
        match, score = process.extractOne(team, elo_names_list)
        if score > 60: # Если сходство более 60%, считаем что это одна команда
            team_mapping[team] = match
        else:
            team_mapping[team] = team # Если не нашли, оставляем как есть

    print(f"Сопоставление завершено. Найдено {len(team_mapping)} пар.")

    print("\n--- ШАГ 2: ОБНОВЛЕНИЕ ПРОПУЩЕННЫХ ДАННЫХ ELO ---")
    
    # Находим матчи, где Elo равен NULL
    missing_matches = session.query(Match).filter(
        (Match.home_elo == None) | (Match.away_elo == None)
    ).order_by(Match.date.asc()).all()

    if not missing_matches:
        print("Пропусков Elo не обнаружено!")
        return

    print(f"Найдено {len(missing_matches)} матчей для обновления. Начинаем...")
    
    elo_cache = {}
    processed_count = 0

    for match in missing_matches:
        try:
            elo_date_str = (match.date - timedelta(days=1)).strftime('%Y-%m-%d')
            
            if elo_date_str not in elo_cache:
                #print(f"[{processed_count}/{len(missing_matches)}] Запрос ClubElo на {elo_date_str}...")
                time.sleep(1.3) # Задержка для защиты от бана
                try:
                    day_elo_df = club_elo.read_by_date(elo_date_str)
                    elo_cache[elo_date_str] = day_elo_df.reset_index().set_index('team')
                except Exception as e:
                    print(f"Ошибка загрузки даты {elo_date_str}. Возможно, бан. Делаем паузу...")
                    time.sleep(10)
                    elo_cache[elo_date_str] = None
                    continue

            day_data = elo_cache.get(elo_date_str)
            if day_data is not None:
                # Берем имена из БД и превращаем их в имена ClubElo через наш словарь
                h_elo_name = team_mapping.get(match.home_team.name)
                a_elo_name = team_mapping.get(match.away_team.name)

                if h_elo_name in day_data.index:
                    match.home_elo = float(day_data.loc[h_elo_name, 'elo'])
                if a_elo_name in day_data.index:
                    match.away_elo = float(day_data.loc[a_elo_name, 'elo'])

            processed_count += 1
            
            # Сохраняем прогресс каждые 50 матчей
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