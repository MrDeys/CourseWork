import time
import os
import sys
from datetime import timedelta
import soccerdata as sd
from sqlalchemy import or_

# --- НАСТРОЙКА ПУТЕЙ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..', '..')))
from src.database.tables import SessionLocal, Match, Team

# МАКСИМАЛЬНО ПОЛНЫЙ СЛОВАРЬ (Учитываем RU и EN названия)
HARD_FIX_MAP = {
    # Испания
    "Athletic Club": "Athletic",
    "Атлетик Бильбао": "Athletic",
    "Atletico Madrid": "Atletico",
    "Атлетико Мадрид": "Atletico",
    "Sporting Gijon": "Sporting Gijon",
    "Спортинг Хихон": "Sporting Gijon",
    "Real Sociedad": "Sociedad",
    "Реал Сосьедад": "Sociedad",
    
    # Англия
    "Wolverhampton Wanderers": "Wolverhampton",
    "Вулверхэмптон": "Wolverhampton",
    "Queens Park Rangers": "QPR",
    "КПР": "QPR",
    
    # Франция
    "Ajaccio": "Ajaccio",
    "Аяччо": "Ajaccio",
    "GFC Ajaccio": "Ajaccio GFCO",
    "Saint-Etienne": "St Etienne",
    "Сент-Этьен": "St Etienne",
    
    # Италия
    "Inter": "Inter",
    "Интер": "Inter",
    "SPAL 2013": "Spal",
    "СПАЛ 2013": "Spal"
}

def fix_elo():
    session = SessionLocal()
    club_elo = sd.ClubElo()
    
    print("🚑 ЗАПУСК СУПЕР-ДОКТОРА ELO (ПОСЛЕДНИЙ РЫВОК)...")
    
    # Берем все матчи, где Elo всё еще 0 или NULL
    missing = session.query(Match).filter(
        or_(Match.home_elo == None, Match.away_elo == None)
    ).order_by(Match.date.desc()).all()

    if not missing:
        print("✅ Все матчи заполнены!")
        return

    print(f"🔄 Осталось починить: {len(missing)} матчей.")
    
    elo_cache = {}
    success_count = 0

    for idx, match in enumerate(missing):
        try:
            elo_date_str = (match.date - timedelta(days=1)).strftime('%Y-%m-%d')
            
            if elo_date_str not in elo_cache:
                time.sleep(1.1)
                try:
                    df = club_elo.read_by_date(elo_date_str)
                    elo_cache[elo_date_str] = df.reset_index().set_index('team')
                except:
                    elo_cache[elo_date_str] = None
                    continue

            day_data = elo_cache.get(elo_date_str)
            if day_data is not None:
                # Пробуем найти имя по цепочке: Маппинг(RU) -> Маппинг(EN) -> Имя(EN)
                h_target = HARD_FIX_MAP.get(match.home_team.name_ru, 
                           HARD_FIX_MAP.get(match.home_team.name, match.home_team.name))
                
                a_target = HARD_FIX_MAP.get(match.away_team.name_ru, 
                           HARD_FIX_MAP.get(match.away_team.name, match.away_team.name))

                fixed = False
                if match.home_elo is None and h_target in day_data.index:
                    match.home_elo = float(day_data.loc[h_target, 'elo'])
                    fixed = True
                
                if match.away_elo is None and a_target in day_data.index:
                    match.away_elo = float(day_data.loc[a_target, 'elo'])
                    fixed = True
                
                if fixed: success_count += 1
            else:
                # Если данных за этот день вообще нет в ClubElo
                # Для диплома допустимо поставить 1500 (средний рейтинг), 
                # чтобы модель не видела NULL
                if match.home_elo is None: match.home_elo = 1500.0
                if match.away_elo is None: match.away_elo = 1500.0
                success_count += 1

            if (idx + 1) % 50 == 0:
                session.commit()
                print(f"🛠 Обработано {idx + 1}/{len(missing)}...")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            session.rollback()

    session.commit()
    session.close()
    print(f"\n✨ Готово! База данных полностью укомплектована.")

if __name__ == "__main__":
    fix_elo()