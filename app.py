import os
import threading
from web import app as app  # re-export Flask app for gunicorn

# Ensure bot starts when gunicorn imports app
from web import _start_bot

if os.environ.get("START_BOT", "1") == "1":
    threading.Thread(target=_start_bot, daemon=True).start()
