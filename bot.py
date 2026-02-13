# Final Webhook Build v2.0
import asyncio
import logging
import os
import random
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
    BotCommand
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv
import aiohttp
import aiosqlite
from aiohttp import web

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "8527373588:AAGcjWQtX7VfMvPe4p3bBDJ-0-DUpasy-m8")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "bafd7faf0a523d40f16892a82b062065")
RENDER_URL = os.getenv("RENDER_URL", "https://pogoda34-bot.onrender.com")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{RENDER_URL}{WEBHOOK_PATH}"

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Погода34_Webhook")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
DB_PATH = os.path.join(BASE_DIR, "subscribers.db")

# --- КОНСТАНТЫ ---
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

def get_photo_file(key: str):
    fname = "volgograd.jpg"
    CITY_FILES = {k: f"{v['name'].lower()}.jpg" for k, v in CITIES.items()} # Simple mapping logic
    # Specific overrides if needed
    CITY_FILES["lat=48.708&lon=44.513"] = "volgograd.jpg"
    CITY_FILES["lat=48.818&lon=44.757"] = "volzhsky.jpg"
    # ... (all others are handled by folder check)
    fname = os.path.basename(key.replace("lat=","").replace("&lon=","_") + ".jpg") # fallback
    
    # Try literal lookup from manual mapping
    MANUAL = {"lat=48.708&lon=44.513": "volgograd.jpg", "lat=48.818&lon=44.757": "volzhsky.jpg", "lat=50.083&lon=45.4": "kamyshin.jpg",
              "lat=50.067&lon=43.233": "mikhaylovka.jpg", "lat=50.8&lon=42.0": "uryupinsk.jpg", "lat=49.773&lon=43.655": "frolovo.jpg",
              "lat=48.691&lon=43.526": "kalach.jpg", "lat=47.583&lon=43.133": "kotelnikovo.jpg", "lat=50.315&lon=44.807": "kotovo.jpg",
              "lat=48.608&lon=42.85": "surovikino.jpg", "lat=48.712&lon=44.572": "krasnoslobodsk.jpg", "lat=50.981&lon=44.767": "zhirnovsk.jpg",
              "lat=50.533&lon=42.667": "novoanninsky.jpg", "lat=50.045&lon=46.883": "pallasovka.jpg", "lat=49.058&lon=44.829": "dubovka.jpg",
              "lat=50.028&lon=45.46": "nikolaevsk.jpg", "lat=48.705&lon=45.202": "leninsk.jpg", "lat=50.137&lon=45.211": "petrov_val.jpg",
              "lat=49.583&lon=42.733": "serafimovich.jpg", "lat=48.805&lon=44.476": "volgograd.jpg"}
    
    final_name = MANUAL.get(key, "volgograd.jpg")
    path = os.path.join(IMAGES_DIR, final_name)
    if os.path.exists(path):
        with open(path, 'rb') as f: return BufferedInputFile(f.read(), filename=final_name)
    return None

# --- DATABASE ---
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS subs (uid INTEGER PRIMARY KEY, key TEXT, cityName TEXT)")
        await db.commit()

# --- AIOGRAM ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def fetch_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r: return await r.json() if r.status == 200 else None

def format_cur(d, name):
    if not d: return "⚠️ Ошибка данных"
    t = round(d['main']['temp'])
    desc = d['weather'][0]['description'].capitalize()
    return f"📍 <b>{name.upper()}</b>\n🌡 <b>{t:+d}°C</b>, {desc}\n💨 Ветер: {d['wind']['speed']} м/с\n💧 Влажность: {d['main']['humidity']}%"

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def start_handler(m: types.Message):
    kb = InlineKeyboardBuilder()
    for k, v in CITIES.items(): kb.button(text=f"{v['emoji']} {v['name']}", callback_data=f"w_{k}")
    kb.adjust(2).row(InlineKeyboardButton(text="📬 Рассылка", callback_data="sm"))
    photo = get_photo_file("lat=48.708&lon=44.513")
    txt = "🌤 <b>ПОГОДА 34</b>\nВыберите город:"
    if photo: await m.answer_photo(photo, caption=txt, reply_markup=kb.as_markup(), parse_mode="HTML")
    else: await m.answer(txt, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "home")
async def home_cb(c: types.CallbackQuery):
    await c.answer()
    await c.message.delete()
    await start_handler(c.message)

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
    await c.message.delete()
    if photo: await c.message.answer_photo(photo, caption=format_cur(data, city['name']), reply_markup=kb.as_markup(), parse_mode="HTML")
    else: await c.message.answer(format_cur(data, city['name']), reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "sm")
async def sub_menu_cb(c: types.CallbackQuery):
    await c.answer()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT cityName FROM subs WHERE uid=?", (c.from_user.id,)) as cur: row = await cur.fetchone()
    kb = InlineKeyboardBuilder()
    if row:
        txt = f"📬 <b>РАССЫЛКА</b>\nВы подписаны на: {row[0]}"
        kb.button(text="❌ Отписаться", callback_data="unsub")
    else:
        txt = "📬 <b>РАССЫЛКА</b>\nПодписаться на 07:00 и 18:00 МСК?"
        kb.button(text="🔔 Подписаться", callback_data="sl")
    kb.row(InlineKeyboardButton(text="🔙 Назад", callback_data="home"))
    await c.message.delete()
    await c.message.answer(txt, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "sl")
async def sub_list_cb(c: types.CallbackQuery):
    await c.answer()
    kb = InlineKeyboardBuilder()
    for k, v in CITIES.items(): kb.button(text=v['name'], callback_data=f"ss_{k}")
    kb.adjust(2).row(InlineKeyboardButton(text="🔙 Назад", callback_data="sm"))
    await c.message.edit_reply_markup(reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("ss_"))
async def set_sub_cb(c: types.CallbackQuery):
    key = c.data.split("ss_")[1]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO subs VALUES (?, ?, ?)", (c.from_user.id, key, CITIES[key]['name']))
        await db.commit()
    await c.answer(f"✅ Подписка на {CITIES[key]['name']}!", show_alert=True)
    await sub_menu_cb(c)

@dp.callback_query(F.data == "unsub")
async def unsub_cb(c: types.CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM subs WHERE uid=?", (c.from_user.id,))
        await db.commit()
    await c.answer("❌ Подписка отменена", show_alert=True)
    await sub_menu_cb(c)

# --- ПЛАНИРОВЩИК ---
async def mailing_task():
    sent_hours = set()
    while True:
        h = (datetime.now(timezone.utc).hour + 3) % 24
        if h in [7, 18] and h not in sent_hours:
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT uid, key, cityName FROM subs") as cur: users = await cur.fetchall()
            for uid, key, name in users:
                try:
                    coords = key.replace("lat=","").replace("lon=","").split("&")
                    data = await fetch_weather(coords[0], coords[1])
                    if data: await bot.send_message(uid, f"🔔 <b>РАССЫЛКА</b>\n\n{format_cur(data, name)}", parse_mode="HTML")
                    await asyncio.sleep(0.05)
                except: pass
            sent_hours.add(h)
        if h not in [7, 18]: sent_hours.clear()
        await asyncio.sleep(60)

# --- WEB SERVER ---
async def on_startup(bot: Bot):
    await init_db()
    # Установка меню бота
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота / Главное меню")
    ])
    # Установка Вебхука
    logger.info(f"Setting webhook: {WEBHOOK_URL}")
    await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
    # Запуск рассылки (event loop уже работает здесь)
    asyncio.create_task(mailing_task())
    logger.info("Mailing task started")

def main():
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    
    app.router.add_get("/", lambda r: web.Response(text="Bot is running!"))
    
    dp.startup.register(on_startup)
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting bot on port {port}")
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
