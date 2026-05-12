import os
from src.app import create_app
from update import run_full_update 
import threading

app = create_app()

if __name__ == '__main__':
    # Запускаем обновление в фоне при старте локально
    update_thread = threading.Thread(target=run_full_update)
    update_thread.start()
    
    # Порт 5000 для локального Docker
    app.run(host='0.0.0.0', port=5000)