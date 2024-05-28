from dotenv import load_dotenv
import os
import time
import webbrowser
from threading import Timer

load_dotenv()

def open_browser():
    time.sleep(1)  # Give the server a second to start
    webbrowser.open_new("http://localhost:5000")

if __name__ == '__main__':
    Timer(1, open_browser).start()
    os.system("flask run --host=0.0.0.0")
