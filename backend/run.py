import threading
from src.app import create_app
from update import run_full_update # Наш новый скрипт

app = create_app()

if __name__ == '__main__':
    # Запускаем обновление в фоновом потоке. 
    # Сайт откроется сразу, а данные обновятся через пару минут в фоне.
    update_thread = threading.Thread(target=run_full_update)
    update_thread.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)