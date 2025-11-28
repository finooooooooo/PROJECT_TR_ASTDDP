import webview
import threading
import sys
import os

# Add current directory to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

def start_server():
    app.run(port=5000, debug=False)

if __name__ == '__main__':
    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    webview.create_window('POS System', 'http://localhost:5000', width=1200, height=800)
    webview.start()
