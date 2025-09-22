import os
import threading
from flask import Flask

# Start aiogram bot in a background thread on startup
from bot import main as bot_main

app = Flask(__name__)

@app.get("/")
def health():
    return {"status": "ok"}

def _start_bot():
    import asyncio
    asyncio.run(bot_main())

if __name__ == "__main__":
    threading.Thread(target=_start_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
