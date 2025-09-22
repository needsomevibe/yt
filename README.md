# Y Project Bot

Небольшой Telegram-бот на Python (aiogram).

## Требования
- Python 3.13
- Рекомендуется использовать виртуальное окружение (`venv`).

## Установка
```bash
# Клонируем проект
git clone <ваш-репозиторий.git>
cd "y project bot"

# Создаём и активируем venv
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# .\\venv\\Scripts\\activate  # Windows PowerShell

# Устанавливаем зависимости
pip install -r requirements.txt
```

## Запуск
Перед запуском задайте переменные окружения, например токен бота:
```bash
export BOT_TOKEN=\"<ваш_telegram_bot_token>\"
```

Затем запустите:
```bash
python bot.py
```

## Структура
- `bot.py` — входная точка бота
- `venv/` — виртуальное окружение (не коммитим)

## Лицензия
MIT — см. `LICENSE`.
