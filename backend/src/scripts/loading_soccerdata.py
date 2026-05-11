import pandas as pd
import numpy as np
import sys, os, time
from datetime import datetime, timedelta
import soccerdata as sd  # Используем стандартный импорт для версии 1.3.5

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
    
    # ИСПРАВЛЕНИЕ: Добавляем сезон 2425, так как 2526 может быть еще пуст
    target_seasons = ['2425', '2526'] 
    
    print(f"🚀 Загрузка данных Understat (Версия 1.3.5, Сезоны: {target_seasons})...")
    
    try:
        # Принудительно отключаем кэш через переменную окружения
        os.environ["SOCCERDATA_NOCACHE"] = "True"

        # В версии 1.3.5 инициализация делается так:
        understat = sd.Understat(leagues=list(LEAGUES_MAPPING.keys()), seasons=target_seasons)
        
        print("📡 Чтение расписания...")
        df_schedule = understat.read_schedule().reset_index()
        
        print("📡 Чтение статистики...")
        df_stats = understat.read_team_match_stats().reset_index()

        # Создаем колонку для связи (только день), чтобы merge не затирал время
        df_schedule['join_date'] = pd.to_datetime(df_schedule['date']).dt.date
        df_stats['join_date'] = pd.to_datetime(df_stats['date']).dt.date

        # Объединяем
        df = pd.merge(
            df_schedule, 
            df_stats, 
            on=['join_date', 'home_team', 'away_team', 'league', 'season'], 
            how='left', 
            suffixes=('', '_stats_extra')
        )
        
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)

        # Фильтруем: берем последние 30 дней и будущее
        if not full_scan:
            start_threshold = datetime.now() - timedelta(days=30)
            df = df[df['date'] >= start_threshold]

        if df.empty:
            print("✅ Новых матчей в этом окне дат не найдено.")
            return

        print(f"📦 Синхронизация {len(df)} записей с БД...")
        existing_matches = {m.match_id: m for m in session.query(Match).all()}
        all_teams = {t.name: t.id for t in session.query(Team).all()}
        all_leagues = {l.name: l.id for l in session.query(League).all()}

        processed, updated, created = 0, 0, 0

        for _, row in df.iterrows():
            h_team, a_team = str(row['home_team']), str(row['away_team'])
            match_date = row['date']
            
            uid = f"und_{match_date.strftime('%Y%m%d%H%M')}_{h_team}_{a_team}"
            match_obj = existing_matches.get(uid)
            h_g = _clean_val(row.get('home_goals'), int)

            if not match_obj:
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

                match_obj = Match(
                    match_id=uid, league_id=all_leagues[l_name],
                    home_team_id=all_teams[h_team], away_team_id=all_teams[a_team],
                    date=match_date, season=str(row['season']), status="SCHEDULED"
                )
                session.add(match_obj)
                existing_matches[uid] = match_obj
                created += 1

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
            if processed % 100 == 0: session.commit()

        session.commit()
        print(f"✅ Готово! Создано: {created}, Обновлено: {updated}.")

    except Exception as e:
        print(f"❌ Ошибка в load_data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    load_data(full_scan=False)