import requests
import pandas as pd
import os
import time
from dotenv import load_dotenv
import datetime

load_dotenv()

API_KEY = os.getenv('CURRENT_API_KEY')

if not API_KEY:
    raise ValueError("Ошибка: API_KEY не найден")

URL = 'https://api.football-data.org/v4/'
DIR = 'leagues'

SEASON = datetime.datetime.now().year

if datetime.datetime.now().month <= 6:
    SEASON -= 1

LEAGUES = {
    'Premier_League': 'PL',
    'La_Liga': 'PD',
    'Serie_A': 'SA',
    'Bundesliga': 'BL1',
    'Ligue_1': 'FL1',
}

REQUEST_DELAY = 7 

HEADERS = {
    'X-Auth-Token': API_KEY
}

def fetch_api_data(endpoint, params=None):
    """Отправляет запрос к API football-data.org и возвращает JSON ответ"""
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
        if response.status_code == 403:
             print("Ошибка 403: Доступ запрещен")
        elif response.status_code == 404:
             print(f"Ошибка 404: Эндпоинт не найден")
        elif response.status_code == 429:
            print("Превышен лимит запросов")
    finally:
        time.sleep(REQUEST_DELAY)

if not os.path.exists(DIR):
    os.makedirs(DIR)

for league_name, league_id in LEAGUES.items():
    print(f"\nОбработка лиги: {league_name}")

    season_path = os.path.join(DIR, league_name, str(SEASON))
    if not os.path.exists(season_path):
        os.makedirs(season_path, exist_ok=True)

    data_file_path = os.path.join(season_path, 'data.csv')

    endpoint = f"competitions/{league_id}/matches"
    params = {
        'season': SEASON
    }

    data = fetch_api_data(endpoint, params)
    all_data = data['matches']

    if all_data:
        try:
            df = pd.json_normalize(all_data, sep='_')
            df.to_csv(data_file_path, index=False, encoding='utf-8')
            print(f"Данные сохранены в: {data_file_path}")
        except Exception as e:
            print(f"Ошибка при обработке или сохранении данных в файл {data_file_path}: {e}")
    else:
        print(f"Нет данных о матчах для сохранения ({league_name} {SEASON}).")

print(f"\nЗагрузка данных текущего сезона завершена")