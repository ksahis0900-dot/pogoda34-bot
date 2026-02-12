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
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("Погода34")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
DB_NAME = "subscribers.db" # В корневом каталоге

def get_photo_data(coords_key: str):
    CITY_PHOTOS = {
        "lat=48.708&lon=44.513": ["volgograd.jpg"], "lat=48.818&lon=44.757": ["volzhsky.jpg"],
        "lat=50.083&lon=45.4":   ["kamyshin.jpg"], "lat=50.067&lon=43.233": ["mikhaylovka.jpg"],
        "lat=50.8&lon=42.0":     ["uryupinsk.jpg"], "lat=49.773&lon=43.655": ["frolovo.jpg"],
        "lat=48.691&lon=43.526": ["kalach.jpg"], "lat=47.583&lon=43.133": ["kotelnikovo.jpg"],
        "lat=48.805&lon=44.476": ["volgograd.jpg"], "default": ["volgograd.jpg"]
    }
    filename = random.choice(CITY_PHOTOS.get(coords_key, CITY_PHOTOS["default"]))
    path = os.path.join(IMAGES_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, 'rb') as f: return BufferedInputFile(f.read(), filename=filename)
        except Exception: pass
    return None

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- БАЗА ---
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
    "lat=47.583&lon=43.133": {"name": "Котельниково", "emoji": "🚂"}
}

async def get_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp: return await resp.json() if resp.status == 200 else None

def format_w(data, name):
    if not data: return "Ошибка данных"
    t = round(data['main']['temp'])
    return f"📍 <b>{name.upper()}</b>\n🌡 {t:+d}°C, {data['weather'][0]['description']}"

# --- КЛАВЫ ---
def main_kb():
    b = InlineKeyboardBuilder()
    for k, v in CITIES.items(): b.button(text=f"{v['emoji']} {v['name']}", callback_data=f"w_{k}")
    b.adjust(2)
    b.row(InlineKeyboardButton(text="📬 Рассылка", callback_data="sub_menu"))
    return b.as_markup()

def sub_kb(is_sub, name=None):
    b = InlineKeyboardBuilder()
    if is_sub: b.button(text=f"✅ Подписка: {name}", callback_data="none"), b.button(text="❌ Отписаться", callback_data="unsub")
    else: b.button(text="🔔 Подписаться", callback_data="sub_list")
    b.row(InlineKeyboardButton(text="🔙 Меню", callback_data="start"))
    return b.as_markup()

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start(m: types.Message):
    p = get_photo_data("default")
    txt = "🌤 <b>ПОГОДА 34</b>\nВыберите город:"
    if p: await m.answer_photo(p, caption=txt, reply_markup=main_kb(), parse_mode="HTML")
    else: await m.answer(txt, reply_markup=main_kb(), parse_mode="HTML")

@dp.callback_query(F.data == "start")
async def cb_start(c: types.CallbackQuery):
    await c.message.delete()
    await start(c.message)

@dp.callback_query(F.data.startswith("w_"))
async def cb_w(c: types.CallbackQuery):
    k = c.data.split("_")[1]
    city = CITIES[k]
    data = await get_weather(*k.replace("lat=","").replace("lon=","").split("&"))
    text = format_w(data, city['name'])
    p = get_photo_data(k)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="start")]])
    await c.message.delete()
    if p: await c.message.answer_photo(p, caption=text, reply_markup=kb, parse_mode="HTML")
    else: await c.message.answer(text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data == "sub_menu")
async def cb_sm(c: types.CallbackQuery):
    s = await get_subscription(c.from_user.id)
    await c.message.delete()
    await c.message.answer("📬 <b>Меню рассылки</b>", reply_markup=sub_kb(s is not None, s[1] if s else None), parse_mode="HTML")

@dp.callback_query(F.data == "sub_list")
async def cb_sl(c: types.CallbackQuery):
    b = InlineKeyboardBuilder()
    for k, v in CITIES.items(): b.button(text=v['name'], callback_data=f"set_{k}")
    b.adjust(2).row(InlineKeyboardButton(text="🔙 Назад", callback_data="sub_menu"))
    await c.message.edit_reply_markup(reply_markup=b.as_markup())

@dp.callback_query(F.data.startswith("set_"))
async def cb_set(c: types.CallbackQuery):
    k = c.data.split("_")[1]
    await add_subscription(c.from_user.id, k, CITIES[k]['name'])
    await c.answer(f"✅ Подписано на {CITIES[k]['name']}")
    await cb_sm(c)

@dp.callback_query(F.data == "unsub")
async def cb_un(c: types.CallbackQuery):
    await remove_subscription(c.from_user.id)
    await c.answer("❌ Отписано")
    await cb_sm(c)

# --- ПЛАНИРОВЩИК ---
async def mailer():
    sent_today = False
    while True:
        h = (datetime.now(timezone.utc).hour + 3) % 24
        if h in [7, 18]:
            if not sent_today:
                logger.info(f"Start mailing for hour {h}")
                subs = await get_all_subscribers()
                for uid, k, name in subs:
                    try:
                        d = await get_weather(*k.replace("lat=","").replace("lon=","").split("&"))
                        if d: await bot.send_message(uid, f"🔔 <b>Рассылка</b>\n\n{format_w(d, name)}", parse_mode="HTML")
                    except: pass
                sent_today = True
        else: sent_today = False
        await asyncio.sleep(60)

async def main():
    await init_db()
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="ALIVE"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()
    asyncio.create_task(mailer())
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
