import time
import os
import sys
import json
from datetime import datetime, timedelta
import soccerdata as sd
from thefuzz import process 
from sqlalchemy import or_, and_

# --- НАСТРОЙКА ПУТЕЙ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..', '..')))
from src.database.tables import SessionLocal, Match, Team

# ОБЪЕДИНЕННЫЙ МАКСИМАЛЬНЫЙ СЛОВАРЬ (Understat/RU -> ClubElo)
FINAL_ELO_MAP = {
    # Италия
    "Интер": "Inter", "Inter": "Inter",
    "Милан": "Milan", "AC Milan": "Milan",
    "Наполи": "Napoli", "Napoli": "Napoli",
    "Ювентус": "Juventus",
    "Парма": "Parma", "Parma Calcio 1913": "Parma",
    "СПАЛ 2013": "Spal", "SPAL 2013": "Spal",
    
    # Германия
    "Боруссия М.Гладбах": "Gladbach", "Borussia M.Gladbach": "Gladbach",
    "РБ Лейпциг": "RB Leipzig", "RasenBallsport Leipzig": "RB Leipzig",
    "Кельн": "Koeln", "FC Cologne": "Koeln",
    "Айнтрахт Франкфурт": "Frankfurt", "Eintracht Frankfurt": "Frankfurt",
    "Майнц 05": "Mainz", "Mainz 05": "Mainz",
    "Нюрнберг": "Nuernberg", "Nuernberg": "Nuernberg",
    "Гройтер Фюрт": "Fuerth", "Greuther Fuerth": "Fuerth",
    "Хольштайн Киль": "Holstein", "Holstein Kiel": "Holstein",
    "Санкт-Паули": "St Pauli", "St. Pauli": "St Pauli",
    
    # Испания
    "Атлетик Бильбао": "Athletic", "Athletic Club": "Athletic",
    "Атлетико Мадрид": "Atletico", "Atletico Madrid": "Atletico",
    "Реал Сосьедад": "Sociedad", "Real Sociedad": "Sociedad",
    "Депортиво": "Depor", "Deportivo La Coruna": "Depor",
    "Спортинг Хихон": "Sporting Gijon", "Sporting Gijon": "Sporting Gijon",
    "Альмерия": "Almeria", "Almeria": "Almeria",
    "Сельта Виго": "Celta", "Celta Vigo": "Celta",
    
    # Англия
    "Вулверхэмптон": "Wolves", "Wolverhampton Wanderers": "Wolves",
    "КПР": "QPR", "Queens Park Rangers": "QPR",
    "Вест Бромвич Альбион": "West Brom", "West Bromwich Albion": "West Brom",
    "Манчестер Сити": "Man City", "Manchester City": "Man City",
    "Манчестер Юнайтед": "Man United", "Manchester United": "Man United",
    
    # Франция
    "ПСЖ": "Paris SG", "Paris Saint Germain": "Paris SG",
    "Ланс": "Lens", "Lens": "Lens",
    "Сент-Этьен": "St Etienne", "Saint-Etienne": "St Etienne",
    "Эвиан Тонон Гайяр": "Evian", "Evian Thonon Gaillard": "Evian",
    "Аяччо": "Ajaccio", "Ajaccio": "Ajaccio",
    "ГФК Аяччо": "Ajaccio GFCO", "GFC Ajaccio": "Ajaccio GFCO"
}

def auto_sync_elo():
    session = SessionLocal()
    club_elo = sd.ClubElo()
    
    print("🚀 СТАРТ ПОЛНОЙ СИНХРОНИЗАЦИИ ELO...")
    
    # 1. Получаем список всех имен в ClubElo на сегодня для нечеткого поиска
    try:
        current_elo_df = club_elo.read_by_date()
        elo_names_list = current_elo_df.index.get_level_values('team').unique().tolist()
    except Exception as e:
        print(f"❌ Ошибка доступа к API ClubElo: {e}")
        return

    limit_date = datetime.now() - timedelta(days=30)
    # 2. Находим все матчи, где Elo равен NULL или 0
    missing_matches = session.query(Match).filter(
        or_(Match.home_elo == None, Match.away_elo == None, Match.home_elo == 0, Match.away_elo == 0), Match.date >= limit_date
    ).order_by(Match.date.desc()).limit(200).all()

    if not missing_matches:
        print("✅ База данных уже полностью заполнена рейтингами Elo.")
        return

    print(f"📦 Найдено {len(missing_matches)} матчей для обработки.")
    
    elo_cache = {}
    processed = 0
    success = 0

    for match in missing_matches:
        try:
            # Дата рейтинга — за день до матча
            elo_date_str = (match.date - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Кэширование запросов к API, чтобы не качать одну дату дважды
            if elo_date_str not in elo_cache:
                time.sleep(1.1) # Защита от бана
                try:
                    df = club_elo.read_by_date(elo_date_str)
                    elo_cache[elo_date_str] = df.reset_index().set_index('team')
                except:
                    elo_cache[elo_date_str] = None
                    continue

            day_data = elo_cache.get(elo_date_str)
            
            # Функция поиска имени в ClubElo
            def find_name(team_obj):
                # 1. Сначала ищем в словаре (по RU названию)
                if team_obj.name_ru in FINAL_ELO_MAP:
                    return FINAL_ELO_MAP[team_obj.name_ru]
                # 2. Ищем в словаре (по EN названию)
                if team_obj.name in FINAL_ELO_MAP:
                    return FINAL_ELO_MAP[team_obj.name]
                # 3. Нечеткий поиск (только если сходство > 85%)
                match_name, score = process.extractOne(team_obj.name, elo_names_list)
                if score > 85:
                    return match_name
                return team_obj.name

            if day_data is not None:
                h_target = find_name(match.home_team)
                a_target = find_name(match.away_team)

                fixed = False
                # Записываем Elo Хозяев
                if h_target in day_data.index:
                    match.home_elo = float(day_data.loc[h_target, 'elo'])
                    fixed = True
                # Записываем Elo Гостей
                if a_target in day_data.index:
                    match.away_elo = float(day_data.loc[a_target, 'elo'])
                    fixed = True
                
                if fixed: success += 1
            else:
                # Если данных в ClubElo нет совсем (старые лиги), ставим 1500 (Baseline)
                if match.home_elo is None or match.home_elo == 0: match.home_elo = 1500.0
                if match.away_elo is None or match.away_elo == 0: match.away_elo = 1500.0
                success += 1

            processed += 1
            if processed % 100 == 0:
                session.commit()
                print(f"🛠 Обработано {processed}/{len(missing_matches)}... (Успешно: {success})")

        except Exception as e:
            print(f"❌ Ошибка на матче {match.id}: {e}")
            session.rollback()

    session.commit()
    session.close()
    print(f"\n✨ ГОТОВО! База данных полностью укомплектована рейтингами Elo.")

if __name__ == "__main__":
    auto_sync_elo()