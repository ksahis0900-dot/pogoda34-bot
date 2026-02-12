import asyncio
import logging
import os
import random

# Определяем абсолютный путь к папке с картинками (для совместимости)
# (Удалено лишнее, используем просто относительные пути)

from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
    URLInputFile
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import aiohttp
import aiosqlite
from dateutil import parser
from aiohttp import web

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# --- ЛОГИКА ДЛЯ ФОТО ---
import os

# Определяем путь к папке с картинками относительно bot.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# Диагностика при старте
print(f"--- DIAGNOSTIC: Checking photos ---")
print(f"Looking for images in: {IMAGES_DIR}")
if os.path.exists(IMAGES_DIR):
    files = os.listdir(IMAGES_DIR)
    print(f"Found {len(files)} files: {files}")
else:
    print(f"CRITICAL: images directory NOT FOUND at {IMAGES_DIR}")

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

def get_random_photo(coords_key: str):
    filenames = CITY_PHOTOS.get(coords_key, CITY_PHOTOS["default"])
    filename = random.choice(filenames)
    photo_path = os.path.join(IMAGES_DIR, filename)
    
    if os.path.exists(photo_path):
        return photo_path
    
    # Резервный вариант
    default_path = os.path.join(IMAGES_DIR, "volgograd.jpg")
    return default_path if os.path.exists(default_path) else None

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("Погода34")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База данных для подписок
DB_NAME = "subscribers.db"

# -------------------------------------------------------------------
#  БАЗА ДАННЫХ
# -------------------------------------------------------------------

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                city_key TEXT NOT NULL,
                city_name TEXT NOT NULL
            )
        """)
        await db.commit()

async def add_subscription(user_id: int, city_key: str, city_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO subscriptions (user_id, city_key, city_name) VALUES (?, ?, ?)",
            (user_id, city_key, city_name)
        )
        await db.commit()

async def remove_subscription(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_subscription(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT city_key, city_name FROM subscriptions WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def get_all_subscribers():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, city_key, city_name FROM subscriptions") as cursor:
            return await cursor.fetchall()

# -------------------------------------------------------------------
#  КОНСТАНТЫ И СПИСКИ
# -------------------------------------------------------------------

CITIES = {
    "lat=48.708&lon=44.513": {"name": "Волгоград", "emoji": "🏙"},
    "lat=48.818&lon=44.757": {"name": "Волжский", "emoji": "⚡️"},
    "lat=50.083&lon=45.4":   {"name": "Камышин", "emoji": "🍉"},
    "lat=50.067&lon=43.233": {"name": "Михайловка", "emoji": "🚜"},
    "lat=50.8&lon=42.0":     {"name": "Урюпинск", "emoji": "🐐"},
    "lat=49.773&lon=43.655": {"name": "Фролово", "emoji": "🛢"},
    "lat=48.691&lon=43.526": {"name": "Калач-на-Дону", "emoji": "⚓️"},
    "lat=47.583&lon=43.133": {"name": "Котельниково", "emoji": "🚂"}, # NEW
    "lat=50.315&lon=44.807": {"name": "Котово", "emoji": "🌲"},
    "lat=48.608&lon=42.85":  {"name": "Суровикино", "emoji": "🌾"},
    
    # Новые города
    "lat=50.028&lon=45.46":  {"name": "Николаевск", "emoji": "🍉"},
    "lat=50.981&lon=44.767": {"name": "Жирновск", "emoji": "🛢"},
    "lat=50.045&lon=46.883": {"name": "Палласовка", "emoji": "🐪"},
    "lat=48.705&lon=45.202": {"name": "Ленинск", "emoji": "🍅"},
    "lat=49.058&lon=44.829": {"name": "Дубовка", "emoji": "🌳"},
    "lat=50.137&lon=45.211": {"name": "Петров Вал", "emoji": "🚂"},
    "lat=50.533&lon=42.667": {"name": "Новоаннинский", "emoji": "🌻"}, # NEW
    "lat=49.583&lon=42.733": {"name": "Серафимович", "emoji": "⛪️"}, # NEW
    "lat=48.805&lon=44.476": {"name": "Городище", "emoji": "🛡"},
    "lat=48.712&lon=44.572": {"name": "Краснослободск", "emoji": "🚤"}, 
}

# -------------------------------------------------------------------
#  ПОЛУЧЕНИЕ ПОГОДЫ (OpenWeatherMap)
# -------------------------------------------------------------------

async def get_weather_data(lat: str, lon: str):
    """Текущая погода"""
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

async def get_forecast_data(lat: str, lon: str):
    """Прогноз на 5 дней (3-часовой)"""
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

# -------------------------------------------------------------------
#  ФОРМАТИРОВАНИЕ СООБЩЕНИЙ
# -------------------------------------------------------------------

def get_weather_emoji(weather_id):
    """Крупные иконки погоды"""
    if 200 <= weather_id <= 232: return "⛈ ГРОЗА"
    if 300 <= weather_id <= 321: return "🌧 МОРОСЬ"
    if 500 <= weather_id <= 531: return "☔️ ДОЖДЬ"
    if 600 <= weather_id <= 622: return "❄️ СНЕГ"
    if 701 <= weather_id <= 781: return "🌫 ТУМАН"
    if weather_id == 800:        return "☀️ ЯСНО"
    if weather_id == 801:        return "🌤 ОБЛАЧНО"
    if weather_id == 802:        return "⛅️ ОБЛАЧНО"
    if 803 <= weather_id <= 804: return "☁️ ПАСМУРНО"
    return "🌡"

def wind_direction(deg):
    dirs = ['С', 'СВ', 'В', 'ЮВ', 'Ю', 'ЮЗ', 'З', 'СЗ']
    ix = round(deg / 45)
    return dirs[ix % 8]

def wind_desc(speed):
    if speed < 0.5: return "Штиль"
    if speed < 5.5: return "Слабый ветер"
    if speed < 10.7: return "Умеренный"
    if speed < 17.1: return "Крепкий"
    return "ШТОРМ!"

def format_time_ago():
    now = datetime.now(timezone.utc)
    hour = (now.hour + 3) % 24
    minute = now.minute
    return f"{hour:02d}:{minute:02d}"

def get_temp_bar(temp):
    """Визуальная шкала температуры"""
    min_t, max_t = -30, 40
    clamped = max(min(temp, max_t), min_t)
    percent = (clamped - min_t) / (max_t - min_t)
    filled = int(percent * 10)
    empty = 10 - filled
    
    if temp < -10: icon = "🥶" 
    elif temp < 0: icon = "❄️"
    elif temp < 15: icon = "🍃"
    elif temp < 25: icon = "☀️"
    else: icon = "🔥" 

    return f"{icon} {'█' * filled}{'░' * empty}"

def format_weather(data, city_name):
    if not data:
        return "⚠️ Не удалось получить данные."

    temp = round(data['main']['temp'])
    feels = round(data['main']['feels_like'])
    hum = data['main']['humidity']
    pres = data['main']['pressure']
    ws = round(data['wind']['speed'], 1)
    wd = data['wind'].get('deg', 0)
    w = data['weather'][0]
    wid = w['id']
    desc = w['description'].capitalize()
    
    vis = data.get('visibility', 10000)
    vis_km = round(vis / 1000, 1)

    sunrise = datetime.fromtimestamp(data['sys']['sunrise'], tz=timezone.utc)
    sunset = datetime.fromtimestamp(data['sys']['sunset'], tz=timezone.utc)
    # Correct timezone to MSK (+3 hours) manually for simple display
    sunrise_msk = (sunrise.hour + 3) % 24
    sunset_msk = (sunset.hour + 3) % 24

    we = get_weather_emoji(wid)
    bar = get_temp_bar(temp)

    # Красивая верстка сообщения
    msg = (
        f"📍 <b>{city_name.upper()}</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n\n"
        
        f"<b>{we} {desc}</b>\n\n"
        
        f"🌡 <b>Температура</b>\n"
        f"├ Куртка: {temp:+d}°C\n"
        f"├ Ощущается: {feels:+d}°C\n"
        f"└ {bar}\n\n"
        
        f"💨 <b>Ветер:</b> {ws} м/с ({wind_direction(wd)})\n"
        f"💧 <b>Влажность:</b> {hum}%\n"
        f"👁 <b>Видимость:</b> {vis_km} км\n"
        f"📉 <b>Давление:</b> {pres} гПа\n\n"
        
        f"🌅 {sunrise_msk:02d}:{sunrise.minute:02d}  |  🌇 {sunset_msk:02d}:{sunset.minute:02d}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"🕒 Обновлено: {format_time_ago()} МСК"
    )
    return msg

def format_forecast_msg(forecast_data, city_name):
    if not forecast_data:
        return "⚠️ Не удалось получить прогноз."

    # Группируем по дням
    daily = {}
    for item in forecast_data['list']:
        dt = item['dt']
        date_obj = datetime.fromtimestamp(dt, tz=timezone.utc)
        day_str = date_obj.strftime('%d.%m')
        
        if day_str not in daily:
            daily[day_str] = []
        daily[day_str].append(item)

    msg = (
        f"🗓 <b>ПРОГНОЗ НА 5 ДНЕЙ</b>\n"
        f"📍 <b>{city_name.upper()}</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
    )

    count = 0
    # Берем первые 5 дней
    for day, items in list(daily.items())[:5]:
        mid_item = items[len(items)//2]
        
        temps = [x['main']['temp'] for x in items]
        t_max = round(max(temps))
        t_min = round(min(temps))
        
        w_codes = [x['weather'][0]['id'] for x in items]
        common_code = max(set(w_codes), key=w_codes.count)
        
        emoji = get_weather_emoji(common_code).split(" ")[0] # Только иконка
        desc = items[0]['weather'][0]['description']
        
        date_obj = datetime.fromtimestamp(items[0]['dt'], tz=timezone.utc)
        weekday = date_obj.strftime('%a')
        weekdays_ru = {
            "Mon": "Пн", "Tue": "Вт", "Wed": "Ср", "Thu": "Чт", 
            "Fri": "Пт", "Sat": "Сб", "Sun": "Вс"
        }
        wd_ru = weekdays_ru.get(weekday, weekday)

        msg += f"\n<b>{day} ({wd_ru})</b>  {emoji} {desc.capitalize()}\n"
        msg += f"🌡 {t_max:+d}°  ...  {t_min:+d}°\n"
        
        rain_prob = max([x.get('pop', 0) for x in items]) * 100
        if rain_prob > 20:
             msg += f"💧 Осадки: {int(rain_prob)}%\n"
        
        msg += f"〰〰〰〰〰〰〰〰\n"
        count += 1

    return msg

# -------------------------------------------------------------------
#  КЛАВИАТУРЫ
# -------------------------------------------------------------------

def city_keyboard():
    items = list(CITIES.items())
    buttons = []
    
    # По 2 города в ряд
    row = []
    for key, val in items:
        btn = InlineKeyboardButton(text=f"{val['emoji']} {val['name']}", callback_data=f"w_{key}")
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="📬 Настройка рассылки", callback_data="sub_menu")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def sub_keyboard(user_id, is_subbed=False, sub_city_name=None):
    buttons = []
    
    if is_subbed:
        buttons.append([InlineKeyboardButton(text=f"✅ Вы подписаны на: {sub_city_name}", callback_data="ignore")])
        buttons.append([InlineKeyboardButton(text="❌ Отписаться", callback_data="sub_unsub")])
    else:
        buttons.append([InlineKeyboardButton(text="🔔 Подписаться на город", callback_data="sub_pick")])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_home")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def sub_city_pick_keyboard():
    items = list(CITIES.items())
    buttons = []
    for key, val in items:
        buttons.append([
            InlineKeyboardButton(text=f"{val['name']}", callback_data=f"sub_set_{key}")
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="sub_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def forecast_kb(coords_key):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Прогноз на 5 дней", callback_data=f"f_{coords_key}")],
        [InlineKeyboardButton(text="🔙 Меню", callback_data="back_home")]
    ])

def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В меню", callback_data="back_home")]
    ])

# -------------------------------------------------------------------
#  ХЕНДЛЕРЫ
# -------------------------------------------------------------------

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Берем фото Волгограда для старта
    photo_url = get_random_photo("lat=48.708&lon=44.513")
    
    txt = (
        f"🌤 <b>ПОГОДА 34</b>\n"
        f"Волгоградская область\n\n"
        f"Точный прогноз погоды для твоего города.\n"
        f"Красивые виды, детальные данные и никаких лишних советов.\n\n"
        f"📍 <b>Выбери город из списка:</b>"
    )
    
    try:
        photo_url = get_random_photo("lat=48.708&lon=44.513") # Volgograd
        if photo_url:
            await message.answer_photo(
                photo=FSInputFile(photo_url),
                caption=txt,
                reply_markup=city_keyboard(),
                parse_mode="HTML"
            )
        else:
            await message.answer(txt, reply_markup=city_keyboard(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error sending start photo: {e}")
        await message.answer(txt, reply_markup=city_keyboard(), parse_mode="HTML")

# DEBUG COMMANDS
@dp.message(Command("list_files"))
async def cmd_list_files(message: types.Message):
    try:
        report = [f"BASE_DIR: {BASE_DIR}", f"IMAGES_DIR: {IMAGES_DIR}", f"Exists: {os.path.exists(IMAGES_DIR)}"]
        if os.path.exists(IMAGES_DIR):
            files = os.listdir(IMAGES_DIR)
            report.append(f"Files ({len(files)}): {', '.join(files[:20])}")
        
        await message.answer("\n".join(report))
    except Exception as e:
        await message.answer(f"Error: {e}")

@dp.message(Command("debug_photo"))
async def cmd_debug_photo(message: types.Message):
    test_file = "volgograd.jpg"
    paths_to_try = [
        os.path.join(IMAGES_DIR, test_file),
        os.path.join(os.getcwd(), "images", test_file),
        os.path.join(os.path.dirname(__file__), "images", test_file),
        f"images/{test_file}"
    ]
    
    results = []
    for p in paths_to_try:
        exists = os.path.exists(p)
        results.append(f"Path: {p}\nExists: {exists}")
        if exists:
            try:
                await message.answer_photo(FSInputFile(p), caption=f"Success: {p}")
            except Exception as e:
                results.append(f"Send Error: {e}")
    
    await message.answer("\n\n".join(results))

# Callbacks
@dp.callback_query(F.data == "back_home")
async def cb_home(callback: types.CallbackQuery):
    await callback.message.delete()
    await cmd_start(callback.message)

@dp.callback_query(F.data == "ignore")
async def cb_ignore(callback: types.CallbackQuery):
    await callback.answer()

@dp.callback_query(F.data.startswith("w_"))
async def cb_weather(callback: types.CallbackQuery):
    coords_key = callback.data.split("w_")[1]
    city_data = CITIES.get(coords_key)
    
    if not city_data:
        await callback.answer("Город не найден", show_alert=True)
        return

    lat_lon = coords_key.replace("lat=", "").replace("lon=", "").split("&")
    lat, lon = lat_lon[0], lat_lon[1]

    data = await get_weather_data(lat, lon)
    msg = format_weather(data, city_data['name'])
    
    photo_url = get_random_photo(coords_key)
    kb = forecast_kb(coords_key)

    try:
        await callback.message.delete()
    except:
        pass

    try:
        await callback.message.answer_photo(
            photo=FSInputFile(photo_url),
            caption=msg,
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to send photo for {city_data['name']}: {e}")
        # Fallback to text
        await callback.message.answer(
            text=msg,
            reply_markup=kb,
            parse_mode="HTML"
        )
    await callback.answer()

@dp.callback_query(F.data.startswith("f_"))
async def cb_forecast(callback: types.CallbackQuery):
    coords_key = callback.data.split("f_")[1]
    city_data = CITIES.get(coords_key)

    lat_lon = coords_key.replace("lat=", "").replace("lon=", "").split("&")
    lat, lon = lat_lon[0], lat_lon[1]

    data = await get_forecast_data(lat, lon)
    msg = format_forecast_msg(data, city_data['name'])
    
    photo_url = get_random_photo(coords_key)
    
    try:
        await callback.message.delete()
    except:
        pass
    
    try:
        await callback.message.answer_photo(
            photo=FSInputFile(photo_url),
            caption=msg,
            reply_markup=back_kb(),
            parse_mode="HTML"
        )
    except Exception:
        # Fallback to text
        await callback.message.answer(
            text=msg,
            reply_markup=back_kb(),
            parse_mode="HTML"
        )
    await callback.answer()

# --- ПОДПИСКИ ---

@dp.callback_query(F.data == "sub_menu")
async def cb_sub_menu(callback: types.CallbackQuery):
    sub = await get_subscription(callback.from_user.id)
    is_subbed = sub is not None
    city_name = sub[1] if sub else None
    
    txt = (
        "📬 <b>Настройка рассылки</b>\n\n"
        "Получай прогноз погоды каждое утро (в 07:00) и вечер (в 18:00).\n"
        "Бот сам пришлет красивую сводку."
    )
    
    try:
        await callback.message.delete() 
        await callback.message.answer(
             txt, 
             reply_markup=sub_keyboard(callback.from_user.id, is_subbed, city_name), 
             parse_mode="HTML"
        )
    except:
        pass

@dp.callback_query(F.data == "sub_pick")
async def cb_sub_pick(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=sub_city_pick_keyboard())

@dp.callback_query(F.data.startswith("sub_set_"))
async def cb_subscribe(callback: types.CallbackQuery):
    coords_key = callback.data.split("sub_set_")[1]
    city_data = CITIES.get(coords_key)
    
    await add_subscription(callback.from_user.id, coords_key, city_data['name'])
    
    await callback.answer("✅ Подписка оформлена!", show_alert=True)
    await cb_sub_menu(callback)

@dp.callback_query(F.data == "sub_unsub")
async def cb_unsub(callback: types.CallbackQuery):
    await remove_subscription(callback.from_user.id)
    await callback.answer("❌ Подписка отменена", show_alert=True)
    await cb_sub_menu(callback)

# --- ВЕБ-СЕРВЕР и РАССЫЛКА ---

async def send_scheduled_weather():
    while True:
        try:
            now = datetime.now(timezone.utc)
            msk_hour = (now.hour + 3) % 24
            
            if (msk_hour == 7 or msk_hour == 18) and now.minute == 0:
                subscribers = await get_all_subscribers()
                for user_id, city_key, city_name in subscribers:
                    try:
                        lat_lon = city_key.replace("lat=", "").replace("lon=", "").split("&")
                        data = await get_weather_data(lat_lon[0], lat_lon[1])
                        if data:
                            msg = format_weather(data, city_name)
                            photo_url = get_random_photo(city_key)
                            await bot.send_photo(
                                chat_id=user_id,
                                photo=FSInputFile(photo_url),
                                caption=f"📬 <b>Рассылка погоды</b>\n\n{msg}",
                                parse_mode="HTML"
                            )
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        logger.error(f"Failed to send to {user_id}: {e}")
                
                await asyncio.sleep(65)
                
            await asyncio.sleep(10)
        except Exception:
            await asyncio.sleep(10)

async def handle_health(request):
    return web.Response(text="Bot is alive!", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Web server started on port {port}")

async def main():
    await init_db()
    
    # Запускаем веб-сервер (для Render)
    await start_web_server()
    
    # Запускаем планировщик
    asyncio.create_task(send_scheduled_weather())
    
    # Запускаем бота
    logger.info("🚀 Погода34 запускается...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
