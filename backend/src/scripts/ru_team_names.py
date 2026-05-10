import os, sys, time
from dotenv import load_dotenv
from deep_translator import GoogleTranslator

# Подключаем твою базу
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.tables import SessionLocal, Team

# Словарь для "трудных" случаев, которые переводчик может перевести смешно
# Например, Crystal Palace может стать "Хрустальным дворцом"
MANUAL_MAPPING = {
    "Crystal Palace": "Кристал Пэлас",
    "Aston Villa": "Астон Вилла",
    "Real Madrid": "Реал Мадрид",
    "Manchester United": "Манчестер Юнайтед",
    "Manchester City": "Манчестер Сити",
    "Bayern Munich": "Бавария",
    "Bayer Leverkusen": "Байер",
    "Borussia Dortmund": "Боруссия Д",
    "Paris Saint Germain": "ПСЖ",
    "Lille": "Лилль",
    "Nice": "Ницца"
}

def translate_teams():
    session = SessionLocal()
    translator = GoogleTranslator(source='en', target='ru')
    
    # Берем команды, у которых еще нет русского названия
    teams = session.query(Team).filter((Team.name_ru == None) | (Team.name_ru == "")).all()
    
    if not teams:
        print("Все команды уже переведены!")
        return

    print(f"Начинаем перевод {len(teams)} команд...")

    for team in teams:
        try:
            # Если команда есть в ручном словаре - берем оттуда
            if team.name in MANUAL_MAPPING:
                team.name_ru = MANUAL_MAPPING[team.name]
            else:
                # Иначе переводим через Google
                translated = translator.translate(team.name)
                # Убираем лишние слова типа "футбольный клуб", если они прилипли
                team.name_ru = translated.replace("ФК ", "").replace(" футбольный клуб", "")
            
            print(f"EN: {team.name:25} -> RU: {team.name_ru}")
            
            # Небольшая пауза, чтобы Google не забанил за спам
            time.sleep(0.5)

        except Exception as e:
            print(f"Ошибка при переводе {team.name}: {e}")
            continue

    try:
        session.commit()
        print("\n✅ Все переводы успешно сохранены в БД!")
    except Exception as e:
        session.rollback()
        print(f"Ошибка сохранения: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    translate_teams()