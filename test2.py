import os, sys
from sqlalchemy import func
from datetime import datetime

# Подключаем пути
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.src.database.tables import SessionLocal, Team, Match

def run_audit():
    session = SessionLocal()
    print(f"\n📊 АУДИТ БАЗЫ ДАННЫХ НА {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("=" * 70)

    # 1. Проверка команд (ELO и Переводы)
    teams = session.query(Team).all()
    print(f"{'Команда (RU/EN)':<40} | {'ELO':<6} | {'Logo'}")
    print("-" * 70)
    
    for t in teams:
        # Берем последний ELO для команды
        last_match = session.query(Match).filter(
            (Match.home_team_id == t.id) | (Match.away_team_id == t.id)
        ).order_by(Match.date.desc()).first()
        
        elo = 0
        if last_match:
            elo = last_match.home_elo if last_match.home_team_id == t.id else last_match.away_elo
        
        logo_status = "✅" if t.logo_url else "❌"
        name_display = (t.name_ru or t.name)[:38]
        print(f"{name_display:<40} | {str(int(elo or 0)):<6} | {logo_status}")

    # 2. Общая статистика
    total_matches = session.query(Match).count()
    finished_matches = session.query(Match).filter(Match.status == 'FINISHED').count()
    missing_elo = session.query(Match).filter(Match.status == 'FINISHED', Match.home_elo == None).count()
    missing_ru = session.query(Team).filter((Team.name_ru == None) | (Team.name_ru == "")).count()

    print("\n" + "=" * 70)
    print(f"ОБЩАЯ СТАТИСТИКА:")
    print(f"Всего матчей в базе: {total_matches}")
    print(f"Сыгранных матчей: {finished_matches}")
    print(f"Матчей без ELO: {missing_elo} (нужно докачать!)")
    print(f"Команд без перевода: {missing_ru}")
    print("=" * 70)
    
    session.close()

if __name__ == "__main__":
    run_audit()