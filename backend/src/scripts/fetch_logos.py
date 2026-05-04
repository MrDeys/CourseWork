import os, sys
import requests
import time

# Подключаем БД
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.tables import SessionLocal, Team

# Заголовки, чтобы сайты не блокировали "бота"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_logo_v1_wikipedia(team_name):
    """Стратегия 1: Поиск через API Википедии (самый надежный способ)"""
    try:
        # Улучшаем поисковый запрос
        search_query = team_name if "FC" in team_name else f"{team_name} F.C."
        search_url = "https://en.wikipedia.org/w/api.php"
        
        # 1. Ищем страницу
        params = {
            "action": "query", "format": "json", "list": "search",
            "srsearch": search_query, "srlimit": 1
        }
        res = requests.get(search_url, params=params, headers=HEADERS, timeout=5).json()
        
        if res['query']['search']:
            title = res['query']['search'][0]['title']
            # 2. Получаем логотип с этой страницы
            img_params = {
                "action": "query", "format": "json", "titles": title,
                "prop": "pageimages", "pithumbsize": 300
            }
            img_res = requests.get(search_url, params=img_params, headers=HEADERS, timeout=5).json()
            pages = img_res['query']['pages']
            for p in pages:
                if 'thumbnail' in pages[p]:
                    return pages[p]['thumbnail']['source']
    except: pass
    return None

def get_logo_v2_simple(team_name):
    """Стратегия 2: Использование прямого агрегатора (на случай если Википедия молчит)"""
    # Превращаем "Manchester United" в "manchester-united" вручную
    clean_name = team_name.lower().replace(' ', '-')
    # Пытаемся постучаться в открытый репозиторий на GitHub
    url = f"https://raw.githubusercontent.com/luukid/football-logos/master/logos/{team_name.replace(' ', '%20')}.png"
    try:
        r = requests.head(url, headers=HEADERS, timeout=3)
        if r.status_code == 200:
            return url
    except: pass
    return None

def update_team_logos():
    session = SessionLocal()
    teams = session.query(Team).all()
    
    print(f"Запуск обновления логотипов для {len(teams)} команд...")
    
    found = 0
    for team in teams:
        print(f"Поиск: {team.name}...", end=" ", flush=True)
        
        # Сначала пробуем Википедию
        url = get_logo_v1_wikipedia(team.name)
        
        # Если не нашли — пробуем составить прямую ссылку
        if not url:
            url = get_logo_v2_simple(team.name)
            
        # Если совсем ничего — ставим заглушку Clearbit
        if not url:
            domain_name = team.name.lower().replace(' ', '')
            url = f"https://logo.clearbit.com/{domain_name}.com"

        if url:
            team.logo_url = url
            print(f"Найдено!")
            found += 1
        else:
            print(f"Пропуск")
            
        time.sleep(0.4) # Задержка для стабильности

    try:
        session.commit()
        print(f"\n[УСПЕХ]: Обновлено {found} логотипов.")
    except Exception as e:
        session.rollback()
        print(f"\n[ОШИБКА]: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    update_team_logos()