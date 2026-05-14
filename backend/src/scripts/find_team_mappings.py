import time
import os
import sys
from datetime import datetime, timedelta
import soccerdata as sd
from thefuzz import process 
from sqlalchemy import or_, and_

# --- НАСТРОЙКА ПУТЕЙ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(BASE_DIR, '..', '..')))
from src.database.tables import SessionLocal, Match, Team

# СЛОВАРЬ СООТВЕТСТВИЙ (Understat -> ClubElo)
FINAL_ELO_MAP = {
    "Athletic Club": "Bilbao", "Athletic": "Bilbao",
    "Atletico Madrid": "Atletico", "Real Sociedad": "Sociedad",
    "Real Betis": "Betis", "Celta Vigo": "Celta",
    "Rayo Vallecano": "Rayo", "Manchester City": "Man City",
    "Manchester United": "Man United", "Wolverhampton Wanderers": "Wolves",
    "AC Milan": "Milan", "Inter": "Inter", "Hellas Verona": "Verona",
    "Parma Calcio 1913": "Parma", "Borussia M.Gladbach": "Gladbach",
    "RasenBallsport Leipzig": "RB Leipzig", "Paris Saint Germain": "Paris SG"
}

# --- ИСПРАВЛЕНИЕ ОШИБКИ PYLANCE: ОПРЕДЕЛЯЕМ ФУНКЦИЮ ---
def find_name(team_obj, elo_names_list):
    db_name = team_obj.name.strip()
    # 1. Проверка по ручному словарю
    if db_name in FINAL_ELO_MAP:
        return FINAL_ELO_MAP[db_name]
    if team_obj.name_ru and team_obj.name_ru in FINAL_ELO_MAP:
        return FINAL_ELO_MAP[team_obj.name_ru]
    
    # 2. Нечеткий поиск (если ClubElo вернул список имен)
    if elo_names_list:
        m_name, score = process.extractOne(db_name, elo_names_list)
        if score > 85:
            return m_name
    return db_name

def auto_sync_elo():
    session = SessionLocal()
    club_elo = sd.ClubElo()
    now_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    print(f"🚀 СТАРТ СИНХРОНИЗАЦИИ ELO ({datetime.now().strftime('%H:%M:%S')})")

    try:
        # 1. ПОЛУЧАЕМ ТЕКУЩИЕ РЕЙТИНГИ (ДЛЯ БУДУЩИХ МАТЧЕЙ)
        print("📡 Загрузка актуальных рейтингов команд на сегодня...")
        current_elo_df = club_elo.read_by_date().reset_index().set_index('team')
        elo_names_list = current_elo_df.index.unique().tolist()

        # 2. ОБНОВЛЯЕМ БУДУЩИЕ МАТЧИ (на 30 дней вперед)
        # Мы всегда обновляем их, чтобы рейтинг соответствовал "текущей форме"
        future_matches = session.query(Match).filter(
            Match.date >= now_dt,
            Match.date <= now_dt + timedelta(days=30)
        ).all()

        print(f"🔄 Обновление 'текущей формы' для {len(future_matches)} будущих матчей...")
        for match in future_matches:
            h_target = find_name(match.home_team, elo_names_list)
            a_target = find_name(match.away_team, elo_names_list)
            
            if h_target in current_elo_df.index:
                match.home_elo = float(current_elo_df.loc[h_target, 'elo'])
            if a_target in current_elo_df.index:
                match.away_elo = float(current_elo_df.loc[a_target, 'elo'])
        
        session.commit()

        # 3. ЗАПОЛНЯЕМ ИСТОРИЮ (только пустые матчи в прошлом)
        # Берем порцию в 200 штук, чтобы не забанили
        missing_history = session.query(Match).filter(
            Match.date < now_dt,
            or_(Match.home_elo == None, Match.home_elo == 0)
        ).order_by(Match.date.desc()).limit(200).all() # 

        if not missing_history:
            print("✅ История рейтингов полностью заполнена.")
        else:
            print(f"📦 Обработка {len(missing_history)} исторических матчей...")
            elo_cache = {}
            for match in missing_history:
                # Для истории берем рейтинг на день матча
                hist_date_str = (match.date - timedelta(days=1)).strftime('%Y-%m-%d')
                
                if hist_date_str not in elo_cache:
                    time.sleep(3) # Защита от бана
                    try:
                        df = club_elo.read_by_date(hist_date_str)
                        elo_cache[hist_date_str] = df.reset_index().set_index('team')
                    except:
                        elo_cache[hist_date_str] = None
                        continue

                day_data = elo_cache.get(hist_date_str)
                if day_data is not None:
                    h_target = find_name(match.home_team, elo_names_list)
                    a_target = find_name(match.away_team, elo_names_list)
                    
                    match.home_elo = float(day_data.loc[h_target, 'elo']) if h_target in day_data.index else 1500.0
                    match.away_elo = float(day_data.loc[a_target, 'elo']) if a_target in day_data.index else 1500.0

            session.commit()

    except Exception as e:
        print(f"❌ Ошибка в auto_sync_elo: {e}")
        session.rollback()
    finally:
        session.close()
        print("✨ Синхронизация завершена.")

if __name__ == "__main__":
    auto_sync_elo()