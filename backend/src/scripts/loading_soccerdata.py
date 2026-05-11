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

def _clean_val(val, val_type=float):
    if pd.isna(val) or val is None or val == "": return None
    try: return val_type(val)
    except: return None

def load_data(full_scan=False):
    session = SessionLocal()
    # Для ежедневного обновления берем только текущие сезоны
    #target_seasons = ['2425', '2526'] if not full_scan else ['1415','1516','1617','1718','1819','1920','2021','2122','2223','2324','2425', '2526']
    target_seasons = ['2526'] 
    
    print(f"🚀 Загрузка данных Understat (Точное время + Дельта)...")
    
    try:
        understat = sd.Understat(leagues=list(LEAGUES_MAPPING.keys()), seasons=target_seasons)
        
        # 1. Загружаем данные
        df_schedule = understat.read_schedule().reset_index()
        df_stats = understat.read_team_match_stats().reset_index()

        # --- ИСПРАВЛЕНИЕ ДАТЫ ---
        # Создаем колонку для связи (только день), чтобы merge не затирал время
        df_schedule['join_date'] = pd.to_datetime(df_schedule['date']).dt.date
        df_stats['join_date'] = pd.to_datetime(df_stats['date']).dt.date

        # Объединяем, используя join_date как ключ, но сохраняем оригинальный 'date' из расписания
        df = pd.merge(
            df_schedule, 
            df_stats, 
            on=['join_date', 'home_team', 'away_team', 'league', 'season'], 
            how='left', 
            suffixes=('', '_stats_extra')
        )
        
        # Важно: используем точное время из расписания и убираем инфо о часовом поясе для БД
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)

        # 2. Фильтруем: если не полный скан, берем только актуальное (последние 10 дней и будущее)
        if not full_scan:
            start_threshold = datetime.now() - timedelta(days=10)
            df = df[df['date'] >= start_threshold]

        if df.empty:
            print("✅ Новых матчей для обработки не найдено.")
            return

        # 3. Кэширование для ускорения
        print(f"📦 Синхронизация с БД...")
        existing_matches = {m.match_id: m for m in session.query(Match).all()}
        all_teams = {t.name: t.id for t in session.query(Team).all()}
        all_leagues = {l.name: l.id for l in session.query(League).all()}

        processed, updated, created = 0, 0, 0

        for _, row in df.iterrows():
            h_team, a_team = str(row['home_team']), str(row['away_team'])
            match_date = row['date'] # Здесь теперь ТОЧНОЕ время (например, 18:30)
            
            # Уникальный ID на основе точной даты
            uid = f"und_{match_date.strftime('%Y%m%d%H%M')}_{h_team}_{a_team}"
            
            match_obj = existing_matches.get(uid)
            h_g = _clean_val(row.get('home_goals'), int)

            if not match_obj:
                # Создание лиги/команд если их нет
                if h_team not in all_teams:
                    new_team = Team(name=h_team); session.add(new_team); session.flush()
                    all_teams[h_team] = new_team.id
                if a_team not in all_teams:
                    new_team = Team(name=a_team); session.add(new_team); session.flush()
                    all_teams[a_team] = new_team.id
                
                l_name = LEAGUES_MAPPING.get(row['league'], row['league'])
                if l_name not in all_leagues:
                    new_league = League(name=l_name, country=l_name.split('_')[0])
                    session.add(new_league); session.flush()
                    all_leagues[l_name] = new_league.id

                # Создаем новый матч с ТОЧНЫМ ВРЕМЕНЕМ
                match_obj = Match(
                    match_id=uid, league_id=all_leagues[l_name],
                    home_team_id=all_teams[h_team], away_team_id=all_teams[a_team],
                    date=match_date, season=str(row['season']), status="SCHEDULED"
                )
                session.add(match_obj)
                existing_matches[uid] = match_obj
                created += 1

            # Обновление результата (если матч завершился)
            if h_g is not None and (match_obj.status != "FINISHED" or match_obj.home_xg is None):
                match_obj.home_goals = h_g
                match_obj.away_goals = _clean_val(row.get('away_goals'), int)
                match_obj.status = "FINISHED"
                match_obj.home_xg = _clean_val(row.get('home_xg'), float)
                match_obj.away_xg = _clean_val(row.get('away_xg'), float)
                match_obj.home_ppda = _clean_val(row.get('home_ppda'), float)
                match_obj.away_ppda = _clean_val(row.get('away_ppda'), float)
                match_obj.home_deep = _clean_val(row.get('home_deep_completions'), int)
                match_obj.away_deep = _clean_val(row.get('away_deep_completions'), int)
                updated += 1

            processed += 1
            if processed % 200 == 0:
                session.commit()

        session.commit()
        print(f"✅ Успешно! Создано: {created}, Обновлено: {updated}. Время начала матчей сохранено.")

    except Exception as e:
        print(f"❌ Ошибка в load_data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    load_data(full_scan=False)