import os, sys, time
import requests
from bs4 import BeautifulSoup
import urllib.parse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.tables import SessionLocal, Team

HEADERS = {
    'User-Agent': 'FootballDataThesisProject/1.0 (your@email.com)'
}

def get_wikipedia_logo(team_name):
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(team_name + ' football club')}&utf8=&format=json"
        search_res = requests.get(search_url, headers=HEADERS, timeout=5).json()
        
        if not search_res['query']['search']:
            return None
            
        page_title = search_res['query']['search'][0]['title']
        
        page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page_title)}"
        html_res = requests.get(page_url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(html_res.text, 'html.parser')
        
        infobox = soup.find('table', {'class': 'infobox'})
        if infobox:
            img_tag = infobox.find('img')
            if img_tag and 'src' in img_tag.attrs:
                img_url = img_tag['src']
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                
                if '/thumb/' in img_url:
                    img_url = img_url.replace('/thumb/', '/')
                    img_url = img_url.rsplit('/', 1)[0]
                
                return img_url
    except Exception:
        pass
    
    return None

def update_team_logos():
    session = SessionLocal()
    
    teams_to_update = session.query(Team).filter(
        (Team.logo_url == None) | (Team.logo_url == "")
    ).all()
    
    if not teams_to_update:
        print("Все логотипы уже загружены. Пропускаю...")
        session.close()
        return

    print(f"Запуск догрузки логотипов для {len(teams_to_update)} команд...")
    
    found = 0
    for team in teams_to_update:
        print(f"Ищем: {team.name:30}", end="", flush=True)
        
        url = get_wikipedia_logo(team.name)
        
        if url:
            team.logo_url = url
            found += 1
            print(f"[НАЙДЕНО]")
        else:
            print("[НЕ НАЙДЕНО]")
            
        time.sleep(0.5)

        if found % 10 == 0:
            session.commit()

    session.commit()
    session.close()
    print(f"Обновление завершено. Успешно добавлено {found} новых логотипов.")

if __name__ == "__main__":
    update_team_logos()