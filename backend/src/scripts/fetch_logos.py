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
        search_res = requests.get(search_url, headers=HEADERS).json()
        
        if not search_res['query']['search']:
            return None
            
        page_title = search_res['query']['search'][0]['title']
        
        page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page_title)}"
        html_res = requests.get(page_url, headers=HEADERS)
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
    
    teams = session.query(Team).all()
    
    print(f"Запуск ПРИНУДИТЕЛЬНОГО скачивания логотипов для {len(teams)} команд...")
    
    found = 0
    for team in teams:
        print(f"Ищем: {team.name:30}", end="", flush=True)
        
        url = get_wikipedia_logo(team.name)
        
        if url:
            team.logo_url = url
            found += 1
            print(f"[НАЙДЕНО] {url[:50]}...")
        else:
            team.logo_url = None 
            print("[НЕ НАЙДЕНО]")
            
        time.sleep(1)

    session.commit()
    session.close()
    print(f"Обновление завершено. Успешно обновлено {found} из {len(teams)}.")

if __name__ == "__main__":
    update_team_logos()