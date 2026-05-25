import os, sys, time
from deep_translator import GoogleTranslator

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.tables import SessionLocal, Team

MANUAL_MAPPING = {
    "crystal palace": "Кристал Пэлас",
    "aston villa": "Астон Вилла",
    "real madrid": "Реал Мадрид",
    "manchester united": "Манчестер Юнайтед",
    "manchester city": "Манчестер Сити",
    "bayern munich": "Бавария",
    "bayer leverkusen": "Байер",
    "borussia dortmund": "Боруссия Д",
    "paris saint germain": "ПСЖ",
    "lille": "Лилль",
    "nice": "Ницца",
    "lens": "Ланс",
    "athletic club": "Атлетик Бильбао",
    "torino": "Торино",
    "napoli": "Наполи",
    "genoa": "Дженоа",
    "union berlin": "Унион Берлин",
    "cremonese": "Кремонезе",
    "st etienne": "Сент-Этьен"
}

def translate_teams():
    session = SessionLocal()
    translator = GoogleTranslator(source='en', target='ru')
    
    teams = session.query(Team).filter((Team.name_ru == None) | (Team.name_ru == "")).all()
    
    if not teams:
        print("Все команды уже переведены!")
        return

    print(f"Начинаем перевод {len(teams)} команд...")

    for team in teams:
        try:
            raw_name = team.name.strip()
            search_name = raw_name.lower()

            if search_name in MANUAL_MAPPING:
                team.name_ru = MANUAL_MAPPING[search_name]
                print(f"[MANUAL] {raw_name:25} -> {team.name_ru}")
            else:
                translated = translator.translate(raw_name)
                team.name_ru = translated.replace("ФК ", "").replace(" футбольный клуб", "").replace(" Football Club", "")
                print(f"[GOOGLE] {raw_name:25} -> {team.name_ru}")
            
            time.sleep(0.4)

        except Exception as e:
            print(f"Ошибка на команде {team.name}: {e}")
            continue

    session.commit()
    session.close()
    print("\nПеревод завершен!")

if __name__ == "__main__":
    translate_teams()