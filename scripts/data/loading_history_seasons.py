import requests
import json
import pandas as pd
import os
import time
from dotenv import load_dotenv
import datetime

load_dotenv()

API_KEY = os.getenv('HISTORY_API_KEY')

if not API_KEY:
    raise ValueError("Ошибка: API_KEY не найден")


URL = 'https://v3.football.api-sports.io/'
DIR = 'leagues'

LEAGUES = {
    'Premier_League': 39,
    'La_Liga': 140,
    'Serie_A': 135,
    'Bundesliga': 78,
    'Ligue_1': 61,
}

SEASON = datetime.datetime.now().year

if datetime.datetime.now().month <= 6:
    SEASON -= 1

SEASONS = list(range(SEASON - 3, SEASON))

DELAY = 6

HEADERS = {
    'x-apisports-key': API_KEY 
}

def fetch_api_data(endpoint, params):
    """Отправляет запрос к API и возвращает JSON ответ"""
    request = URL + endpoint
    try:    
        response = requests.get(request, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        return data

    except requests.exceptions.Timeout:
        print("Ошибка: превышено время ожидания ответа от сервера")
        return None
    except requests.exceptions.HTTPError as http_err:
        print(f"Ошибка HTTP: {http_err}")
        if response.status_code in [401, 403]:
             print(f"Ошибка авторизации ({response.status_code}) неверный API ключ")
        elif response.status_code == 404:
            print(f"Ошибка 404: Эндпоинт не найден")
        elif response.status_code == 429:
            print("Превышен лимит запросов")
        return None
    finally:
        time.sleep(DELAY)


if not os.path.exists(DIR):
    os.makedirs(DIR)

for league_name, league_id in LEAGUES.items():
    print(f"\nОбработка лиги: {league_name}")
    league_path = os.path.join(DIR, league_name)
    if not os.path.exists(league_path):
        os.makedirs(league_path)

    for season in SEASONS:
        print(f"Сезон: {season}")
        season_path = os.path.join(league_path, str(season))
        data_file_path = os.path.join(season_path, 'data.csv')

        if os.path.exists(data_file_path):
            continue

        if not os.path.exists(season_path):
             os.makedirs(season_path)
             print(f"Создана папка: {season_path}")

        endpoint = 'fixtures'
        all_data = []
        current_page = 1
        total_pages = 1

        while current_page <= total_pages:
            params = {
                    'league': league_id,
                    'season': season,
            }
            if current_page > 1:
                params['page'] = current_page
            
            data = fetch_api_data(endpoint, params)

            data_page = data.get('response')
            all_data.extend(data_page)
            total_pages = data.get('paging', {}).get('total', 1)
            current_page += 1

        if all_data:
            try:
                df = pd.json_normalize(all_data, sep='_')
                df.to_csv(data_file_path, index=False, encoding='utf-8')
                print(f"Данные сохранены в: {data_file_path}")
            except Exception as e:
                 print(f"Ошибка при обработке или сохранении данных в файл {data_file_path}: {e}")
        else:
            print(f"Нет данных о матчах для сохранения ({league_name} {season})")

print("\nЗагрузка исторических данных завершена")