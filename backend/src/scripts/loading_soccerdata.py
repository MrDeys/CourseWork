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
    'FRA-Ligue 1': 'Ligue_1',
}

def get_seasons(full_history=False):
    """Генерирует список сезонов: либо все с 1415, либо последние 2"""
    now = datetime.now()
    start_year = now.year - 1 if now.month < 7 else now.year
    
    if full_history:
        years = range(2014, start_year + 1)
        print("📚 Режим: ЗАГРУЗКА ВСЕЙ ИСТОРИИ (с 2014 года)...")
    else:
        years = range(start_year - 1, start_year + 1)
        print(f"⚡ Режим: ОБНОВЛЕНИЕ (только сезоны {start_year-1}/{start_year} и {start_year}/{start_year+1})")
        
    return [f"{(y)%100:02d}{(y+1)%100:02d}" for y in years]

def get_or_create_league(session, name):
    obj = session.query(League).filter(League.name == name).first()
    if not obj:
        obj = League(name=name, country=name.split('_')[0])
        session.add(obj); session.flush()
    return obj

def get_or_create_team(session, name):
    obj = session.query(Team).filter(Team.name == name).first()
    if not obj:
        obj = Team(name=name)
        session.add(obj); session.flush()
    return obj

def _clean_val(val, val_type=float):
    if pd.isna(val) or val is None or val == "": return None
    try: return val_type(val)
    except: return None

def load_data():
    session = SessionLocal()
    now = datetime.now()
    
    # 1. Проверяем, пустая ли база
    is_db_empty = session.query(Match).first() is None
    target_seasons = get_seasons(full_history=is_db_empty)
    
    try:
        understat = sd.Understat(leagues=list(LEAGUES_MAPPING.keys()), seasons=target_seasons)
        
        print("📡 Скачивание данных из Understat...")
        df_schedule = understat.read_schedule().reset_index()
        df_stats = understat.read_team_match_stats().reset_index()
        
        # Склеиваем по дню, чтобы сохранить точное время
        df_schedule['day'] = pd.to_datetime(df_schedule['date']).dt.date
        df_stats['day'] = pd.to_datetime(df_stats['date']).dt.date

        df = pd.merge(df_schedule, df_stats, on=['day', 'home_team', 'away_team', 'league', 'season'], 
                      how='left', suffixes=('', '_extra'))
        
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)

        # 2. ФИЛЬТРАЦИЯ: Если база не пуста, обрабатываем только матчи в окне -14 / +30 дней
        if not is_db_empty:
            df = df[(df['date'] >= now - timedelta(days=14)) & (df['date'] <= now + timedelta(days=30))]

        if df.empty:
            print("✅ Новых или измененных матчей не найдено.")
            return

        print(f"📦 Обработка {len(df)} матчей...")
        
        # Кэшируем существующие ID и статусы
        existing_matches = {m.match_id: m.status for m in session.query(Match.match_id, Match.status).all()}

        processed, updated, created = 0, 0, 0

        for _, row in df.iterrows():
            match_date = row['date']
            h_name, a_name = str(row['home_team']), str(row['away_team'])
            
            # Стабильный UID (только день)
            uid = f"und_{match_date.strftime('%Y%m%d')}_{h_name.replace(' ','')}_{a_name.replace(' ','')}"
            
            # Пропускаем, если матч уже в базе и завершен
            if uid in existing_matches and existing_matches[uid] == "FINISHED":
                continue

            # Ищем объект (если не нашли в кэше)
            match_obj = session.query(Match).filter(Match.match_id == uid).first()
            h_g = _clean_val(row.get('home_goals'), int)

            if not match_obj:
                league_name = LEAGUES_MAPPING.get(row['league'], row['league'])
                league = get_or_create_league(session, league_name)
                h_team = get_or_create_team(session, h_name)
                a_team = get_or_create_team(session, a_name)
                
                match_obj = Match(
                    match_id=uid, league_id=league.id, 
                    home_team_id=h_team.id, away_team_id=a_team.id, 
                    date=match_date, season=str(row['season']), status="SCHEDULED"
                )
                session.add(match_obj)
                created += 1
            
            # Если матч в базе есть, обновляем время (на случай переносов)
            elif match_obj.status == "SCHEDULED":
                match_obj.date = match_date

            # Записываем результат, если он появился в API
            if h_g is not None:
                match_obj.home_goals = h_g
                match_obj.away_goals = _clean_val(row.get('away_goals'), int)
                match_obj.status = "FINISHED"
                match_obj.home_xg = _clean_val(row.get('home_xg'))
                match_obj.away_xg = _clean_val(row.get('away_xg'))
                match_obj.home_ppda = _clean_val(row.get('home_ppda'))
                match_obj.away_ppda = _clean_val(row.get('away_ppda'))
                match_obj.home_deep = _clean_val(row.get('home_deep_completions'), int)
                match_obj.away_deep = _clean_val(row.get('away_deep_completions'), int)
                updated += 1

            processed += 1
            if processed % 1000 == 0:
                session.commit()
                print(f"⌛ Обработано {processed}...")

        session.commit()
        print(f"✨ Готово! Создано: {created}, Обновлено: {updated}.")

    except Exception as e:
        print(f"❌ Ошибка в load_data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    load_data()