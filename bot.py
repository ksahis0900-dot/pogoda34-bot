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
    BufferedInputFile
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import aiohttp
import aiosqlite
from aiohttp import web

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("Погода34")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
DB_NAME = "subscribers.db"

# --- КОНСТАНТЫ ГОРОДОВ ---
CITIES = {
    "lat=48.708&lon=44.513": {"name": "Волгоград", "emoji": "🏙"},
    "lat=48.818&lon=44.757": {"name": "Волжский", "emoji": "⚡️"},
    "lat=50.083&lon=45.4":   {"name": "Камышин", "emoji": "🍉"},
    "lat=50.067&lon=43.233": {"name": "Михайловка", "emoji": "🚜"},
    "lat=50.8&lon=42.0":     {"name": "Урюпинск", "emoji": "🐐"},
    "lat=49.773&lon=43.655": {"name": "Фролово", "emoji": "🛢"},
    "lat=48.691&lon=43.526": {"name": "Калач-на-Дону", "emoji": "⚓️"},
    "lat=47.583&lon=43.133": {"name": "Котельниково", "emoji": "🚂"},
    "lat=50.315&lon=44.807": {"name": "Котово", "emoji": "🌲"},
    "lat=48.608&lon=42.85":  {"name": "Суровикино", "emoji": "🌾"},
    "lat=48.712&lon=44.572": {"name": "Краснослободск", "emoji": "🚤"}, 
    "lat=50.981&lon=44.767": {"name": "Жирновск", "emoji": "🛢"},
    "lat=50.533&lon=42.667": {"name": "Новоаннинский", "emoji": "🌻"},
    "lat=50.045&lon=46.883": {"name": "Палласовка", "emoji": "🐪"},
    "lat=49.058&lon=44.829": {"name": "Дубовка", "emoji": "🌳"},
    "lat=50.028&lon=45.46":  {"name": "Николаевск", "emoji": "🍉"},
    "lat=48.705&lon=45.202": {"name": "Ленинск", "emoji": "🍅"},
    "lat=50.137&lon=45.211": {"name": "Петров Вал", "emoji": "🚂"},
    "lat=49.583&lon=42.733": {"name": "Серафимович", "emoji": "⛪️"},
    "lat=48.805&lon=44.476": {"name": "Городище", "emoji": "🛡"},
}

def get_photo_file(key: str):
    """Возвращает объект BufferedInputFile для отправки фото"""
    CITY_FILES = {
        "lat=48.708&lon=44.513": "volgograd.jpg",
        "lat=48.818&lon=44.757": "volzhsky.jpg",
        "lat=50.083&lon=45.4":   "kamyshin.jpg",
        "lat=50.067&lon=43.233": "mikhaylovka.jpg",
        "lat=50.8&lon=42.0":     "uryupinsk.jpg",
        "lat=49.773&lon=43.655": "frolovo.jpg",
        "lat=48.691&lon=43.526": "kalach.jpg",
        "lat=47.583&lon=43.133": "kotelnikovo.jpg",
        "lat=50.315&lon=44.807": "kotovo.jpg",
        "lat=48.608&lon=42.85":  "surovikino.jpg",
        "lat=48.712&lon=44.572": "krasnoslobodsk.jpg",
        "lat=50.981&lon=44.767": "zhirnovsk.jpg",
        "lat=50.533&lon=42.667": "novoanninsky.jpg",
        "lat=50.045&lon=46.883": "pallasovka.jpg",
        "lat=49.058&lon=44.829": "dubovka.jpg",
        "lat=50.028&lon=45.46":  "nikolaevsk.jpg",
        "lat=48.705&lon=45.202": "leninsk.jpg",
        "lat=50.137&lon=45.211": "petrov_val.jpg",
        "lat=49.583&lon=42.733": "serafimovich.jpg",
        "lat=48.805&lon=44.476": "volgograd.jpg",
    }
    fname = CITY_FILES.get(key, "volgograd.jpg")
    path = os.path.join(IMAGES_DIR, fname)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return BufferedInputFile(f.read(), filename=fname)
    return None

# --- БАЗА ДАННЫХ ---
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS subs (uid INTEGER PRIMARY KEY, key TEXT, cityName TEXT)")
        await db.commit()

# --- КЛИЕНТЫ ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ФУНКЦИИ API ---
async def fetch_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            return await r.json() if r.status == 200 else None

async def fetch_forecast(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            return await r.json() if r.status == 200 else None

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_emoji(wid):
    if 200 <= wid <= 232: return "⛈"
    if 300 <= wid <= 321: return "🌧"
    if 500 <= wid <= 531: return "☔️"
    if 600 <= wid <= 622: return "❄️"
    if 701 <= wid <= 781: return "🌫"
    if wid == 800: return "☀️"
    if wid == 801: return "🌤"
    if wid == 802: return "⛅️"
    if 803 <= wid <= 804: return "☁️"
    return "🌡"

def format_cur(d, name):
    if not d: return "⚠️ Ошибка данных погоды"
    t = round(d['main']['temp'])
    fl = round(d['main']['feels_like'])
    desc = d['weather'][0]['description'].capitalize()
    emoji = get_emoji(d['weather'][0]['id'])
    return (
        f"📍 <b>{name.upper()}</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"<b>{emoji} {desc}</b>\n\n"
        f"🌡 Температура: {t:+d}°C\n"
        f"🤔 Ощущается: {fl:+d}°C\n"
        f"💨 Ветер: {d['wind']['speed']} м/с\n"
        f"💧 Влажность: {d['main']['humidity']}%\n"
        f"➖➖➖➖➖➖➖➖➖➖"
    )

def format_for(d, name):
    if not d: return "⚠️ Ошибка данных прогноза"
    msg = f"🗓 <b>ПРОГНОЗ НА 5 ДНЕЙ: {name.upper()}</b>\n➖➖➖➖➖➖➖➖➖➖\n"
    days = {}
    for item in d['list']:
        dt = datetime.fromtimestamp(item['dt'], tz=timezone.utc).strftime("%d.%m")
        if dt not in days: days[dt] = item
    for dt, val in list(days.items())[:5]:
        t = round(val['main']['temp'])
        desc = val['weather'][0]['description']
        msg += f"\n<b>{dt}</b>: {t:+d}°C, {desc}"
    return msg

# --- КЛАВИАТУРЫ ---
def get_main_kb():
    kb = InlineKeyboardBuilder()
    for k, v in CITIES.items():
        kb.button(text=f"{v['emoji']} {v['name']}", callback_data=f"weather_{k}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text="📬 Рассылка", callback_data="sub_menu"))
    return kb.as_markup()

def get_back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад в меню", callback_data="home")]])

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start_handler(m: types.Message):
    logger.info(f"User {m.from_user.id} started the bot")
    txt = "🌤 <b>ПОГОДА 34</b>\nВолгоградская область\n\nВыберите город из списка ниже:"
    photo = get_photo_file("lat=48.708&lon=44.513") # Волгоград на старт
    if photo:
        await m.answer_photo(photo, caption=txt, reply_markup=get_main_kb(), parse_mode="HTML")
    else:
        await m.answer(txt, reply_markup=get_main_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "home")
async def home_cb(c: types.CallbackQuery):
    await c.answer()
    await c.message.delete()
    await start_handler(c.message)

@dp.callback_query(F.data.startswith("weather_"))
async def weather_cb(c: types.CallbackQuery):
    await c.answer("Получаю данные...")
    key = c.data.split("weather_")[1]
    city = CITIES[key]
    coords = key.replace("lat=","").replace("lon=","").split("&")
    data = await fetch_weather(coords[0], coords[1])
    
    text = format_cur(data, city['name'])
    photo = get_photo_file(key)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 Прогноз на 5 дней", callback_data=f"forecast_{key}")
    kb.button(text="🔙 Меню", callback_data="home")
    kb.adjust(1)
    
    await c.message.delete()
    if photo:
        await c.message.answer_photo(photo, caption=text, reply_markup=kb.as_markup(), parse_mode="HTML")
    else:
        await c.message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("forecast_"))
async def forecast_cb(c: types.CallbackQuery):
    await c.answer("Загружаю прогноз...")
    key = c.data.split("forecast_")[1]
    city = CITIES[key]
    coords = key.replace("lat=","").replace("lon=","").split("&")
    data = await fetch_forecast(coords[0], coords[1])
    
    text = format_for(data, city['name'])
    photo = get_photo_file(key)
    
    await c.message.delete()
    if photo:
        await c.message.answer_photo(photo, caption=text, reply_markup=get_back_kb(), parse_mode="HTML")
    else:
        await c.message.answer(text, reply_markup=get_back_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "sub_menu")
async def sub_menu_cb(c: types.CallbackQuery):
    await c.answer()
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT cityName FROM subs WHERE uid=?", (c.from_user.id,)) as cur:
            row = await cur.fetchone()
    
    kb = InlineKeyboardBuilder()
    if row:
        txt = f"📬 <b>РАССЫЛКА</b>\n\nВы подписаны на: <b>{row[0]}</b>\nВремя: 07:00 и 18:00 МСК"
        kb.button(text="❌ Отписаться", callback_data="unsub")
    else:
        txt = "📬 <b>РАССЫЛКА</b>\n\nПодпишитесь на уведомления о погоде дважды в день (утром и вечером)."
        kb.button(text="🔔 Подписаться", callback_data="sub_list")
    
    kb.row(InlineKeyboardButton(text="🔙 Назад", callback_data="home"))
    await c.message.delete()
    await c.message.answer(txt, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "sub_list")
async def sub_list_cb(c: types.CallbackQuery):
    await c.answer()
    kb = InlineKeyboardBuilder()
    for k, v in CITIES.items():
        kb.button(text=v['name'], callback_data=f"setsub_{k}")
    kb.adjust(2).row(InlineKeyboardButton(text="🔙 Отмена", callback_data="sub_menu"))
    await c.message.edit_reply_markup(reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("setsub_"))
async def set_sub_cb(c: types.CallbackQuery):
    key = c.data.split("setsub_")[1]
    city_name = CITIES[key]['name']
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO subs VALUES (?, ?, ?)", (c.from_user.id, key, city_name))
        await db.commit()
    await c.answer(f"✅ Подписка на {city_name} оформлена!", show_alert=True)
    await sub_menu_cb(c)

@dp.callback_query(F.data == "unsub")
async def unsub_cb(c: types.CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM subs WHERE uid=?", (c.from_user.id,))
        await db.commit()
    await c.answer("❌ Подписка отменена", show_alert=True)
    await sub_menu_cb(c)

# --- ПЛАНИРОВЩИК РАССЫЛКИ ---
async def mailing_task():
    sent_hours = set()
    while True:
        now = datetime.now(timezone.utc)
        msk_hour = (now.hour + 3) % 24
        
        if msk_hour in [7, 18] and msk_hour not in sent_hours:
            logger.info(f"Starting scheduled mailing for hour {msk_hour}")
            async with aiosqlite.connect(DB_NAME) as db:
                async with db.execute("SELECT uid, key, cityName FROM subs") as cur:
                    users = await cur.fetchall()
            
            for uid, key, name in users:
                try:
                    coords = key.replace("lat=","").replace("lon=","").split("&")
                    data = await fetch_weather(coords[0], coords[1])
                    if data:
                        photo = get_photo_file(key)
                        msg = f"🔔 <b>ЕЖЕДНЕВНАЯ РАССЫЛКА</b>\n\n{format_cur(data, name)}"
                        if photo: await bot.send_photo(uid, photo, caption=msg, parse_mode="HTML")
                        else: await bot.send_message(uid, msg, parse_mode="HTML")
                    await asyncio.sleep(0.05) # Защита от спам-фильтра
                except Exception as e:
                    logger.error(f"Error sending to {uid}: {e}")
            
            sent_hours.add(msk_hour)
        
        if msk_hour not in [7, 18]:
            sent_hours.clear()
            
        await asyncio.sleep(30)

# --- СЕРВЕР ---
async def main():
    await init_db()
    
    # Web server for health checks
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot is running!"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    
    asyncio.create_task(mailing_task())
    
    logger.info("🚀 Бот запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
