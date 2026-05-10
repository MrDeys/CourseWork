import soccerdata as sd
import pandas as pd

def inspect_names():
    club_elo = sd.ClubElo()
    # Возьмем дату, когда все эти команды точно были в высших лигах (например, начало 2017 года)
    date_to_check = "2017-01-15"
    print(f"📡 Запрашиваем данные ClubElo за {date_to_check}...")
    
    try:
        df = club_elo.read_by_date(date_to_check).reset_index()
        all_names = df['team'].unique().tolist()
        
        print("\n🔍 РЕЗУЛЬТАТЫ ПОИСКА:")
        
        print("\n1. Поиск для 'Атлетик Бильбао' (Athletic Club):")
        for n in all_names:
            if "athletic" in n.lower() or "bilbao" in n.lower():
                print(f" -> '{n}'")

        print("\n2. Поиск для 'Вулверхэмптон' (Wolverhampton):")
        for n in all_names:
            if "wolver" in n.lower() or "wolves" in n.lower():
                print(f" -> '{n}'")

        print("\n3. Поиск для 'Спортинг Хихон' (Sporting Gijon):")
        for n in all_names:
            if "sporting" in n.lower() or "gijon" in n.lower() or "gijón" in n.lower():
                print(f" -> '{n}'")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    inspect_names()