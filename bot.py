import logging
import asyncio
import time
import os
import threading
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import random
import string

API_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Установите в Render переменную ADMIN_ID
CHAT_ID = os.getenv("CHAT_ID", "")  # Установите в Render переменную CHAT_ID

if not API_TOKEN or not CHAT_ID or not ADMIN_ID:
    logging.warning(
        "BOT_TOKEN, CHAT_ID или ADMIN_ID не заданы в переменных окружения."
    )

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Вопросы и ответы
questions = [
    {
        "q": "Вопрос 1\nСколько времени дается на то, чтобы прийти в офис для оформления курьеру?",
        "options": ["1. 1 день", "2. 7 дней", "3. 14 дней"],
        "answer": 2
    },
    {
        "q": "Вопрос 2\nКакой доход у пеших курьеров правильно указывать?",
        "options": ["1. Доход зависит от заказов, 3000-4000 руб", "2. 3000 руб", "3. От 3400 руб", "4. До 3400 руб"],
        "answer": 3
    },
    {
        "q": "Вопрос 3\nМожно ли предлагать кандидату бонус?",
        "options": ["1. Только при встрече", "2. Нет, нельзя", "3. Можно, но не более 1000 руб", "4. Можно"],
        "answer": 2
    },
    {
        "q": "Вопрос 4\nКакое название объявления корректно?",
        "options": ["1. Работа Яндекс Еде", "2. Курьер Яндекс Еды", "3. Курьер - Партнер сервиса Яндекс Еда", "4. Вакансия курьера в Яндекс"],
        "answer": 3
    },
    {
        "q": "Вопрос 5\nКакое слово мы используем вместо 'Смена'?",
        "options": ["1. График", "2. Рабочий день", "3. Слот"],
        "answer": 3
    },
    {
        "q": "Вопрос 6\nМожно ли в объявлении указывать возраст и гражданство?",
        "options": ["1. Можно, но только на Авито", "2. Нет - это дискриминация", "3. Можно везде", "4. Только возраст"],
        "answer": 2
    },
    {
        "q": "Вопрос 7\nГде смотреть статусы кандидатов?",
        "options": ["1. В личном кабинете", "2. У самих курьеров", "3. В ТГ боте"],
        "answer": 1
    },
    {
        "q": "Вопрос 8\nС чего начать?",
        "options": ["1. Узнаю среди знакомых", "2. Подготовлю объявление", "3. Выберу job сайты", "4. Все варианты"],
        "answer": 4
    },
    {
        "q": "Вопрос 9\nКак получить доступ к ЛК?",
        "options": ["1. Написать куратору после теста", "2. Спросить в рабочем чате", "3. Как будет первый кандидат - написать куратору"],
        "answer": 3
    }
]

user_data = {}

async def generate_personal_link(user_name: str):
    """Создает персональную пригласительную ссылку на канал через Telegram API"""
    try:
        url = f"https://api.telegram.org/bot{API_TOKEN}/createChatInviteLink"
        data = {
            "chat_id": CHAT_ID,
            "name": f"Ссылка для {user_name}",
            "expire_date": int(time.time()) + 86400,  # 24 часа
            "member_limit": 1  # только один человек
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                result = await response.json()
                if result.get("ok"):
                    return result["result"]["invite_link"]
                else:
                    logging.error(f"Ошибка создания ссылки: {result}")
                    return f"К сожалению, не удалось создать персональную ссылку. Обратитесь к администратору."  # Fallback ссылка
                    
    except Exception as e:
        logging.error(f"Ошибка при создании персональной ссылки: {e}")
        return f"https://t.me/your_channel"  # Fallback ссылка

def get_keyboard(options):
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for i, opt in enumerate(options, 1):
        kb.inline_keyboard.append([InlineKeyboardButton(text=opt, callback_data=f"answer_{i}")])
    return kb

async def notify_admin(user_info, score, passed):
    """Отправляет уведомление администратору"""
    status = "✅ УСПЕШНО" if passed else "❌ НЕУДАЧНО"
    message = (
        f"🔔 НОВОЕ УВЕДОМЛЕНИЕ О ТЕСТЕ\n\n"
        f"👤 Пользователь: {user_info['first_name']} {user_info.get('last_name', '')}\n"
        f"🆔 ID: {user_info['id']}\n"
        f"📝 Username: @{user_info.get('username', 'не указан')}\n"
        f"📊 Результат: {status}\n"
        f"🎯 Баллов: {score}/{len(questions)}"
    )
    
    try:
        await bot.send_message(ADMIN_ID, message)
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления админу: {e}")

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_data[message.from_user.id] = {"score": 0, "q_index": 0}
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Далее", callback_data="next")]])
    await message.answer(
        "Приветствую!\n"
        "Я бот-помощник стажерам - рекрутёрам☺️\n"
        "Расскажу подробнее: - Вы будете заниматься поиском подходящих кандидатов "
        "на вакансии к партнёру сервиса Яндекс.Еда.\n"
        "Приглашать их на оформление.\n\n"
        "Почему это выгодно Вам:\n"
        "1. Доход без ограничений (размер выплат зависит только от Вас)\n"
        "2. Когда удобно (нет строгого графика)\n"
        "3. Без сложных инструментов (Достаточно смартфона или ноутбука)\n"
        "4. Занимайтесь поиском, где угодно (Работать можно из любой точки мира)\n\n"
        "Ваш путь к выплатам\n\n"
        "Нажимайте клавишу «Далее»👇🏻",
        reply_markup=kb
    )

@dp.callback_query(lambda c: c.data == "next")
async def send_video(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать просмотр", url="https://youtu.be/P9eduz6PiKY?si=2mh8gEB8raXeR_4d")],
        [InlineKeyboardButton(text="Таблица правил", url="https://docs.google.com/spreadsheets/d/1QyUGQb6XWDoYuOam03paEcvXZLd1p7v1swY9MvZJ6Aw/edit?usp=sharing")],
        [InlineKeyboardButton(text="Далее", callback_data="practical_part")]
    ])
    await callback.message.edit_text(
        "Для того чтобы ознакомиться с процессом, предлагаем к просмотру обучающий видеоролик.\n"
        "Просьба выслушать всю информацию. Кнопка для просмотра есть ниже.\n\n"
        "После просмотра, необходимо будет пройти тест на основе презентации, на закрепление знаний.\n"
        "Это займет не более 5 минут. Отнеситесь к этому ответственно, это очень важная часть сотрудничества.\n\n"
        "После просмотра, продолжим 😊",
        reply_markup=kb
    )

@dp.callback_query(lambda c: c.data == "practical_part")
async def practical_part(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Начать тест", callback_data="start_test")]])
    await callback.message.edit_text(
        "Теперь подойдем к практической части.\n"
        "После удачного тестирования, я приглашу тебя в Новостной Канал и переда контакт Куратора, по любым вопросам.\n\n"
        "Нажимай кнопку соответствующую цифре твоего ответа.\n"
        "Удачи! 🤝",
        reply_markup=kb
    )

@dp.callback_query(lambda c: c.data == "start_test")
async def start_test(callback: types.CallbackQuery):
    user_data[callback.from_user.id] = {"score": 0, "q_index": 0}
    q = questions[0]
    await callback.message.edit_text(q["q"], reply_markup=get_keyboard(q["options"]))

@dp.callback_query(lambda c: c.data.startswith("answer_"))
async def handle_answer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_data:
        return

    data = user_data[user_id]
    q_index = data["q_index"]

    if q_index < len(questions):
        q = questions[q_index]
        choice = int(callback.data.split("_")[1])

        if choice == q["answer"]:
            data["score"] += 1

        data["q_index"] += 1

        if data["q_index"] < len(questions):
            next_q = questions[data["q_index"]]
            await callback.message.edit_text(next_q["q"], reply_markup=get_keyboard(next_q["options"]))
        else:
            score = data["score"]
            passed = score >= 9
            
            # Уведомляем админа
            user_info = {
                'id': callback.from_user.id,
                'first_name': callback.from_user.first_name,
                'last_name': callback.from_user.last_name,
                'username': callback.from_user.username
            }
            await notify_admin(user_info, score, passed)
            
            if passed:
                user_name = callback.from_user.first_name or "Пользователь"
                personal_link = await generate_personal_link(user_name)
                if personal_link:
                    kb = InlineKeyboardMarkup(
                        inline_keyboard=[[InlineKeyboardButton(text="Перейти в канал", url=personal_link)]]
                    )
                    text = (
                        f"🎉 Поздравляю! Вы успешно сдали тест с {score} баллами из {len(questions)}!\n\n"
                        f"🔗 Ваша персональная ссылка на канал:\n{personal_link}\n\n"
                        "Если будут вопросы — смело обращайтесь к вашему куратору:\n"
                        "👉 @YEats_aleksei\n\n"
                        "Нажмите кнопку ниже, чтобы перейти в канал 👇"
                    )
                    await callback.message.edit_text(text, reply_markup=kb)
                else:
                    await callback.message.edit_text(
                        f"🎉 Поздравляю! Вы успешно сдали тест с {score} баллами из {len(questions)}!\n\n"
                        "К сожалению, не удалось создать персональную ссылку. Обратитесь к администратору.",
                    )
            else:
                kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Пройти снова", callback_data="start_test")]])
                await callback.message.edit_text(
                    f"❌ У Вас {score} баллов из {len(questions)}. К сожалению, есть ошибки.\n"
                    "Прочтите правила и попробуйте пройти снова 😉",
                    reply_markup=kb
                )

@dp.message()
async def handle_text(message: types.Message):
    # Обработка текстовых сообщений (если пользователь пишет вместо нажатия кнопок)
    if message.text == "/test":
        await start_test(types.CallbackQuery(id="", from_user=message.from_user, chat_instance="", message=message))

async def main():
    # Удаляем webhook перед запуском
    await bot.delete_webhook(drop_pending_updates=True)
    # В потоках нельзя ставить сигнальные хендлеры — отключаем их
    is_main_thread = threading.current_thread() is threading.main_thread()
    await dp.start_polling(
        bot,
        skip_updates=True,
        handle_signals=is_main_thread,
    )

if __name__ == "__main__":
    asyncio.run(main())
