import os
from src.app import create_app
from update import run_full_update 
import threading

app = create_app()

if __name__ == '__main__':
    update_thread = threading.Thread(target=run_full_update)
    update_thread.start()
    
    app.run(host='0.0.0.0', port=5000)