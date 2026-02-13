import asyncio
import logging
import os
import random
from datetime import datetime, timezone

import aiohttp
import aiosqlite
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    BufferedInputFile,
    BotCommand
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "8527373588:AAGcjWQtX7VfMvPe4p3bBDJ-0-DUpasy-m8")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "bafd7faf0a523d40f16892a82b062065")
RENDER_URL = os.getenv("RENDER_URL", "https://pogoda34-bot-1pogoda34-bot.onrender.com")

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{RENDER_URL}{WEBHOOK_PATH}"

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("POGODA34_PRO")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "subscribers.db")
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# --- ПОЛНЫЙ СПИСОК ГОРОДОВ ---
CITIES = {
    "lat=48.708&lon=44.513": {"name": "Волгоград", "emoji": "🏙"}, "lat=48.818&lon=44.757": {"name": "Волжский", "emoji": "⚡️"},
    "lat=50.083&lon=45.4":   {"name": "Камышин", "emoji": "🍉"}, "lat=50.067&lon=43.233": {"name": "Михайловка", "emoji": "🚜"},
    "lat=50.8&lon=42.0":     {"name": "Урюпинск", "emoji": "🐐"}, "lat=49.773&lon=43.655": {"name": "Фролово", "emoji": "🛢"},
    "lat=48.691&lon=43.526": {"name": "Калач-на-Дону", "emoji": "⚓️"}, "lat=47.583&lon=43.133": {"name": "Котельниково", "emoji": "🚂"},
    "lat=50.315&lon=44.807": {"name": "Котово", "emoji": "🌲"}, "lat=48.608&lon=42.85":  {"name": "Суровикино", "emoji": "🌾"},
    "lat=48.712&lon=44.572": {"name": "Краснослободск", "emoji": "🚤"}, "lat=50.981&lon=44.767": {"name": "Жирновск", "emoji": "🛢"},
    "lat=50.533&lon=42.667": {"name": "Новоаннинский", "emoji": "🌻"}, "lat=50.045&lon=46.883": {"name": "Палласовка", "emoji": "🐪"},
    "lat=49.058&lon=44.829": {"name": "Дубовка", "emoji": "🌳"}, "lat=50.028&lon=45.46":  {"name": "Николаевск", "emoji": "🍉"},
    "lat=48.705&lon=45.202": {"name": "Ленинск", "emoji": "🍅"}, "lat=50.137&lon=45.211": {"name": "Петров Вал", "emoji": "🚂"},
    "lat=49.583&lon=42.733": {"name": "Серафимович", "emoji": "⛪️"}, "lat=48.805&lon=44.476": {"name": "Городище", "emoji": "🛡"},
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ФУНКЦИИ ---
def get_photo_file(key: str):
    """Находит фото для города по ключу координат"""
    MANUAL = {
        "lat=48.708&lon=44.513": "volgograd.jpg", "lat=48.818&lon=44.757": "volzhsky.jpg",
        "lat=50.083&lon=45.4": "kamyshin.jpg", "lat=50.067&lon=43.233": "mikhaylovka.jpg",
        "lat=50.8&lon=42.0": "uryupinsk.jpg", "lat=49.773&lon=43.655": "frolovo.jpg",
        "lat=48.691&lon=43.526": "kalach.jpg", "lat=47.583&lon=43.133": "kotelnikovo.jpg",
        "lat=50.315&lon=44.807": "kotovo.jpg", "lat=48.608&lon=42.85": "surovikino.jpg",
        "lat=48.712&lon=44.572": "krasnoslobodsk.jpg", "lat=50.981&lon=44.767": "zhirnovsk.jpg",
        "lat=50.533&lon=42.667": "novoanninsky.jpg", "lat=50.045&lon=46.883": "pallasovka.jpg",
        "lat=49.058&lon=44.829": "dubovka.jpg", "lat=50.028&lon=45.46": "nikolaevsk.jpg",
        "lat=48.705&lon=45.202": "leninsk.jpg", "lat=50.137&lon=45.211": "petrov_val.jpg",
        "lat=49.583&lon=42.733": "serafimovich.jpg", "lat=48.805&lon=44.476": "volgograd.jpg"
    }
    
    filename = MANUAL.get(key, "volgograd.jpg")
    path = os.path.join(IMAGES_DIR, filename)
    
    if os.path.exists(path):
        return types.FSInputFile(path)
    return None

async def fetch_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            return await r.json() if r.status == 200 else None

def format_weather(d, name):
    if not d: return "⚠️ Ошибка получения данных"
    t = round(d['main']['temp'])
    desc = d['weather'][0]['description'].capitalize()
    hum = d['main']['humidity']
    wind = d['wind']['speed']
    return (
        f"📍 <b>{name.upper()}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🌡 <b>{t:+d}°C</b> | {desc}\n"
        f"💨 Ветер: {wind} м/с\n"
        f"💧 Влажность: {hum}%\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🕒 <i>Обновлено: {datetime.now().strftime('%H:%M')}</i>"
    )

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS subs (uid INTEGER PRIMARY KEY, key TEXT, cityName TEXT)")
        await db.commit()

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def start_handler(m: types.Message):
    kb = InlineKeyboardBuilder()
    for k, v in CITIES.items():
        kb.button(text=f"{v['emoji']} {v['name']}", callback_data=f"w_{k}")
    kb.adjust(2).row(InlineKeyboardButton(text="📬 Настроить рассылку", callback_data="mailing_menu"))
    
    txt = "🌤 <b>ДОБРО ПОЖАЛОВАТЬ В POGODA 34</b>\n\nВыберите ваш город ниже:"
    photo = get_photo_file("lat=48.708&lon=44.513") # Волгоград по умолчанию
    
    if photo:
        await m.answer_photo(photo, caption=txt, reply_markup=kb.as_markup(), parse_mode="HTML")
    else:
        await m.answer(txt, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("w_"))
async def weather_cb(c: types.CallbackQuery):
    key = c.data.split("w_")[1]
    city = CITIES[key]
    await c.answer(f"Загружаю: {city['name']}")
    
    coords = key.replace("lat=","").replace("lon=","").split("&")
    data = await fetch_weather(coords[0], coords[1])
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Меню", callback_data="home")
    
    photo = get_photo_file(key)
    
    # Удаляем старое сообщение чтобы прислать новое с фото (или обновляем текст если фото нет)
    await c.message.delete()
    
    if photo:
        await c.message.answer_photo(photo, caption=format_weather(data, city['name']), reply_markup=kb.as_markup(), parse_mode="HTML")
    else:
        await c.message.answer(format_weather(data, city['name']), reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "home")
async def home_cb(c: types.CallbackQuery):
    await c.answer()
    await c.message.delete() # Удаляем чтобы не дублировать
    await start_handler(c.message)

@dp.callback_query(F.data == "mailing_menu")
async def mailing_menu_cb(c: types.CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT cityName FROM subs WHERE uid=?", (c.from_user.id,)) as cur:
            row = await cur.fetchone()
    
    kb = InlineKeyboardBuilder()
    if row:
        txt = f"📬 <b>РАССЫЛКА</b>\n\nВы подписаны на: <b>{row[0]}</b>"
        kb.button(text="❌ Отписаться", callback_data="unsub")
    else:
        txt = "📬 <b>РАССЫЛКА</b>\n\nПолучайте прогноз в 07:00 и 18:00 МСК."
        kb.button(text="🔔 Подписаться", callback_data="sub_list")
        
    kb.row(InlineKeyboardButton(text="🔙 Назад", callback_data="home"))
    
    # Пробуем редактировать, если это не фото. Если фото - удаляем и шлем текст.
    try:
        await c.message.edit_text(txt, reply_markup=kb.as_markup(), parse_mode="HTML")
    except:
        await c.message.delete()
        await c.message.answer(txt, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "sub_list")
async def sub_list_cb(c: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    for k, v in CITIES.items():
        kb.button(text=v['name'], callback_data=f"set_sub_{k}")
    kb.adjust(2).row(InlineKeyboardButton(text="🔙 Назад", callback_data="mailing_menu"))
    await c.message.edit_text("Выберите город для рассылки:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("set_sub_"))
async def set_sub_cb(c: types.CallbackQuery):
    key = c.data.split("set_sub_")[1]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO subs VALUES (?, ?, ?)", (c.from_user.id, key, CITIES[key]['name']))
        await db.commit()
    await c.answer(f"✅ Подписка: {CITIES[key]['name']}", show_alert=True)
    await mailing_menu_cb(c)

@dp.callback_query(F.data == "unsub")
async def unsub_cb(c: types.CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM subs WHERE uid=?", (c.from_user.id,))
        await db.commit()
    await c.answer("❌ Подписка отменена", show_alert=True)
    await mailing_menu_cb(c)

# --- TASKS ---
async def mailing_task():
    """Рассылка погоды подписчикам"""
    while True:
        try:
            now = datetime.now(timezone.utc)
            h = (now.hour + 3) % 24  # МСК
            if h in [7, 18] and now.minute == 0:
                async with aiosqlite.connect(DB_PATH) as db:
                    async with db.execute("SELECT uid, key, cityName FROM subs") as cur:
                        users = await cur.fetchall()
                for uid, key, name in users:
                    try:
                        coords = key.replace("lat=","").replace("lon=","").split("&")
                        data = await fetch_weather(coords[0], coords[1])
                        photo = get_photo_file(key)
                        if data:
                            if photo:
                                await bot.send_photo(uid, photo, caption=f"🔔 <b>УТРЕННЯЯ РАССЫЛКА</b>\n\n{format_weather(data, name)}", parse_mode="HTML")
                            else:
                                await bot.send_message(uid, f"🔔 <b>УТРЕННЯЯ РАССЫЛКА</b>\n\n{format_weather(data, name)}", parse_mode="HTML")
                        await asyncio.sleep(0.1) # Пауза между сообщениями
                    except: continue
                await asyncio.sleep(60) # Спим минуту чтобы не слать дважды
        except Exception as e:
            logger.error(f"Mailing error: {e}")
        await asyncio.sleep(30)

async def self_ping_task():
    """Задача для предотвращения засыпания Render"""
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(RENDER_URL) as response:
                    logger.info(f"Self-ping status: {response.status}")
        except Exception as e:
            logger.error(f"Self-ping failed: {e}")
        await asyncio.sleep(600) # Каждые 10 минут

# --- SERVER ---
async def on_startup(bot: Bot):
    await init_db()
    await bot.set_my_commands([BotCommand(command="start", description="Главное меню")])
    logger.info(f"Setting webhook: {WEBHOOK_URL}")
    await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
    asyncio.create_task(mailing_task())
    asyncio.create_task(self_ping_task())

def main():
    app = web.Application()
    async def handle_index(request):
        return web.Response(text="POGODA34 PRO is Live!", content_type="text/plain")
    app.router.add_get("/", handle_index)
    
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    dp.startup.register(on_startup)
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
