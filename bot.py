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
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("Погода34")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")

def get_photo_data(coords_key: str):
    CITY_PHOTOS = {
        "lat=48.708&lon=44.513": ["volgograd.jpg"],
        "lat=48.818&lon=44.757": ["volzhsky.jpg"],
        "lat=50.083&lon=45.4":   ["kamyshin.jpg"],
        "lat=50.067&lon=43.233": ["mikhaylovka.jpg"],
        "lat=50.8&lon=42.0":     ["uryupinsk.jpg"],
        "lat=49.773&lon=43.655": ["frolovo.jpg"],
        "lat=48.691&lon=43.526": ["kalach.jpg"],
        "lat=47.583&lon=43.133": ["kotelnikovo.jpg"],
        "lat=50.315&lon=44.807": ["kotovo.jpg"],
        "lat=48.608&lon=42.85":  ["surovikino.jpg"],
        "lat=48.712&lon=44.572": ["krasnoslobodsk.jpg"],
        "lat=50.981&lon=44.767": ["zhirnovsk.jpg"],
        "lat=50.533&lon=42.667": ["novoanninsky.jpg"],
        "lat=50.045&lon=46.883": ["pallasovka.jpg"],
        "lat=49.058&lon=44.829": ["dubovka.jpg"],
        "lat=50.028&lon=45.46":  ["nikolaevsk.jpg"],
        "lat=48.705&lon=45.202": ["leninsk.jpg"],
        "lat=50.137&lon=45.211": ["petrov_val.jpg"],
        "lat=49.583&lon=42.733": ["serafimovich.jpg"],
        "lat=48.805&lon=44.476": ["volgograd.jpg"],
        "default": ["volgograd.jpg"]
    }
    filenames = CITY_PHOTOS.get(coords_key, CITY_PHOTOS["default"])
    filename = random.choice(filenames)
    path = os.path.join(IMAGES_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, 'rb') as f:
                return BufferedInputFile(f.read(), filename=filename)
        except Exception: pass
    return None

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
DB_NAME = os.path.join(BASE_DIR, "subscribers.db")

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS subscriptions (user_id INTEGER PRIMARY KEY, city_key TEXT, city_name TEXT)")
        await db.commit()

async def add_subscription(user_id, city_key, city_name):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR REPLACE INTO subscriptions VALUES (?, ?, ?)", (user_id, city_key, city_name))
        await db.commit()

async def remove_subscription(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_subscription(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT city_key, city_name FROM subscriptions WHERE user_id = ?", (user_id,)) as c:
            return await c.fetchone()

async def get_all_subscribers():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, city_key, city_name FROM subscriptions") as c:
            return await c.fetchall()

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
    "lat=50.028&lon=45.46":  {"name": "Николаевск", "emoji": "🍉"},
    "lat=50.981&lon=44.767": {"name": "Жирновск", "emoji": "🛢"},
    "lat=50.045&lon=46.883": {"name": "Палласовка", "emoji": "🐪"},
    "lat=48.705&lon=45.202": {"name": "Ленинск", "emoji": "🍅"},
    "lat=49.058&lon=44.829": {"name": "Дубовка", "emoji": "🌳"},
    "lat=50.137&lon=45.211": {"name": "Петров Вал", "emoji": "🚂"},
    "lat=50.533&lon=42.667": {"name": "Новоаннинский", "emoji": "🌻"},
    "lat=49.583&lon=42.733": {"name": "Серафимович", "emoji": "⛪️"},
    "lat=48.805&lon=44.476": {"name": "Городище", "emoji": "🛡"},
    "lat=48.712&lon=44.572": {"name": "Краснослободск", "emoji": "🚤"}, 
}

# --- ПОГОДА API ---
async def get_weather_data(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json() if resp.status == 200 else None

async def get_forecast_data(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json() if resp.status == 200 else None

def format_weather(data, city_name):
    if not data: return "⚠️ Ошибка данных"
    t = round(data['main']['temp'])
    desc = data['weather'][0]['description'].capitalize()
    return f"📍 <b>{city_name.upper()}</b>\n🌡 {t:+d}°C, {desc}"

# --- КЛАВИАТУРЫ ---
def main_kb():
    builder = InlineKeyboardBuilder()
    for k, v in CITIES.items():
        builder.button(text=f"{v['emoji']} {v['name']}", callback_data=f"w_{k}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="📬 Рассылка", callback_data="sub_menu"))
    return builder.as_markup()

def sub_menu_kb(is_subbed, city_name=None):
    builder = InlineKeyboardBuilder()
    if is_subbed:
        builder.button(text=f"✅ Подписка: {city_name}", callback_data="ignore")
        builder.button(text="❌ Отписаться", callback_data="unsub_exec")
    else:
        builder.button(text="🔔 Подписаться", callback_data="sub_pick")
    builder.button(text="🔙 Назад", callback_data="back_home")
    builder.adjust(1)
    return builder.as_markup()

def sub_pick_kb():
    builder = InlineKeyboardBuilder()
    for k, v in CITIES.items():
        builder.button(text=v['name'], callback_data=f"sset_{k}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="sub_menu"))
    return builder.as_markup()

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    photo = get_photo_data("default")
    txt = "🌤 <b>ПОГОДА 34</b>\nВыбери город:"
    if photo: await message.answer_photo(photo, caption=txt, reply_markup=main_kb(), parse_mode="HTML")
    else: await message.answer(txt, reply_markup=main_kb(), parse_mode="HTML")

@dp.message(Command("check_me"))
async def cmd_check(message: types.Message):
    sub = await get_subscription(message.from_user.id)
    if sub: await message.answer(f"✅ Ты в базе! Город: {sub[1]}")
    else: await message.answer("❌ Тебя нет в базе. Подпишись через меню 'Рассылка'.")

@dp.message(Command("test_mail"))
async def cmd_test_mail(message: types.Message):
    sub = await get_subscription(message.from_user.id)
    if not sub:
        return await message.answer("Сначала подпишись через меню!")
    
    await message.answer("🧪 Пробую отправить тестовую рассылку...")
    lat_lon = sub[0].replace("lat=","").replace("lon=","").split("&")
    data = await get_weather_data(lat_lon[0], lat_lon[1])
    if data:
        photo = get_photo_data(sub[0])
        msg = f"🧪 <b>ТЕСТ РАССЫЛКИ</b>\n\n{format_weather(data, sub[1])}"
        if photo: await bot.send_photo(message.from_user.id, photo, caption=msg, parse_mode="HTML")
        else: await message.answer(msg, parse_mode="HTML")

@dp.callback_query(F.data == "back_home")
async def cb_back(callback: types.CallbackQuery):
    await callback.message.delete()
    await cmd_start(callback.message)
    await callback.answer()

@dp.callback_query(F.data.startswith("w_"))
async def cb_weather(callback: types.CallbackQuery):
    key = callback.data.split("w_")[1]
    city = CITIES.get(key)
    lat_lon = key.replace("lat=","").replace("lon=","").split("&")
    data = await get_weather_data(lat_lon[0], lat_lon[1])
    msg = format_weather(data, city['name'])
    photo = get_photo_data(key)
    await callback.message.delete()
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Меню", callback_data="back_home")
    if photo: await callback.message.answer_photo(photo, caption=msg, reply_markup=kb.as_markup(), parse_mode="HTML")
    else: await callback.message.answer(msg, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "sub_menu")
async def cb_sub_menu(callback: types.CallbackQuery):
    sub = await get_subscription(callback.from_user.id)
    txt = "📬 <b>Рассылка</b>\n\nПрогноз приходит в 07:00 и 18:00 МСК."
    await callback.message.delete()
    await callback.message.answer(txt, reply_markup=sub_menu_kb(sub is not None, sub[1] if sub else None), parse_mode="HTML")

@dp.callback_query(F.data == "sub_pick")
async def cb_sub_pick(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=sub_pick_kb())

@dp.callback_query(F.data.startswith("sset_"))
async def cb_sub_set(callback: types.CallbackQuery):
    key = callback.data.split("sset_")[1]
    await add_subscription(callback.from_user.id, key, CITIES[key]['name'])
    await callback.answer(f"✅ Подписка на {CITIES[key]['name']}!", show_alert=True)
    await cb_sub_menu(callback)

@dp.callback_query(F.data == "unsub_exec")
async def cb_unsub(callback: types.CallbackQuery):
    await remove_subscription(callback.from_user.id)
    await callback.answer("❌ Отписались", show_alert=True)
    await cb_sub_menu(callback)

# --- ПЛАНИРОВЩИК ---
last_sent_hour = -1

async def scheduler():
    global last_sent_hour
    while True:
        now = datetime.now(timezone.utc)
        h = (now.hour + 3) % 24 # MSK
        
        if (h == 7 or h == 18) and h != last_sent_hour:
            logger.info(f"Triggering scheduled mailing for hour {h}")
            subs = await get_all_subscribers()
            for uid, key, name in subs:
                try:
                    lat_lon = key.replace("lat=","").replace("lon=","").split("&")
                    data = await get_weather_data(lat_lon[0], lat_lon[1])
                    if data:
                        photo = get_photo_data(key)
                        msg = f"🔔 <b>Рассылка</b>\n\n{format_weather(data, name)}"
                        if photo: await bot.send_photo(uid, photo, caption=msg, parse_mode="HTML")
                        else: await bot.send_message(uid, msg, parse_mode="HTML")
                except: pass
            last_sent_hour = h
        
        if h not in [7, 18]:
            last_sent_hour = -1 # Сброс для следующего дня
            
        await asyncio.sleep(60)

async def main():
    await init_db()
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="OK"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()
    asyncio.create_task(scheduler())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
