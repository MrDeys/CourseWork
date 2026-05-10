import os
import sys
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.src.database.tables import SessionLocal, Match, Team

def check_recent_matches():
    session = SessionLocal()
    
    # 1. Проверяем самые свежие матчи в базе (вообще любые)
    latest = session.query(Match).order_by(Match.date.desc()).limit(5).all()
    print("--- 5 САМЫХ НОВЫХ МАТЧЕЙ В БАЗЕ ---")
    for m in latest:
        print(f"{m.date} | {m.status} | {m.home_team.name} vs {m.away_team.name}")
    
    # 2. Имитируем запрос бэкенда (последние 10 дней)
    start_date = datetime.utcnow() - timedelta(days=10)
    print(f"\n--- ИЩЕМ МАТЧИ ПОСЛЕ: {start_date.strftime('%Y-%m-%d')} ---")
    
    matches_10d = session.query(Match).filter(Match.date >= start_date).order_by(Match.date.asc()).all()
    print(f"Найдено: {len(matches_10d)} матчей.")
    
    if matches_10d:
        print("Первые 5 из них:")
        for m in matches_10d[:5]:
            print(f"{m.date} | {m.status} | {m.home_team.name} vs {m.away_team.name}")

    session.close()

if __name__ == "__main__":
    check_recent_matches()