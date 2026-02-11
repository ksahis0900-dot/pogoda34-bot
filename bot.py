import asyncio
import os
import logging
import json
import aiohttp
from datetime import datetime, timedelta, timezone
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# ═══════════════════════════════════════════════════════
#  🌤 ПОГОДА34 — Бот погоды Волгоградской области
#  Персональный семейный бот с советами для детей
# ═══════════════════════════════════════════════════════

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("Погода34")

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден в .env")
    exit(1)
if not OPENWEATHER_API_KEY:
    print("❌ OPENWEATHER_API_KEY не найден в .env")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ─── Файл для хранения подписок ───
SUBS_FILE = "subscriptions.json"

def load_subs() -> dict:
    try:
        with open(SUBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_subs(subs: dict):
    with open(SUBS_FILE, "w", encoding="utf-8") as f:
        json.dump(subs, f, ensure_ascii=False, indent=2)

# ─── Города Волгоградской области ───
CITIES = {
    "volgograd":    {"name": "Волгоград",      "en": "Volgograd",       "emoji": "🏙"},
    "volzhsky":     {"name": "Волжский",        "en": "Volzhskiy",       "emoji": "🌊"},
    "kamyshin":     {"name": "Камышин",         "en": "Kamyshin",        "emoji": "🌾"},
    "mikhaylovka":  {"name": "Михайловка",      "en": "Mikhaylovka",     "emoji": "🏡"},
    "uryupinsk":    {"name": "Урюпинск",        "en": "Uryupinsk",      "emoji": "🧶"},
    "frolovo":      {"name": "Фролово",         "en": "Frolovo",         "emoji": "🌻"},
    "kalach":       {"name": "Калач-на-Дону",   "en": "Kalach-na-Donu",  "emoji": "🐟"},
    "kotovo":       {"name": "Котово",           "en": "Kotovo",          "emoji": "🐱"},
    "gorodishche":  {"name": "Городище",         "en": "Gorodishche",     "emoji": "🏰"},
    "surovikino":   {"name": "Суровикино",       "en": "Surovikino",      "emoji": "⚔️"},
}

BASE_URL = "https://api.openweathermap.org/data/2.5"


# ═══════════════════════════════════════════════════════
#  🎨 ВИЗУАЛЬНЫЕ ЭЛЕМЕНТЫ
# ═══════════════════════════════════════════════════════

def weather_emoji(desc: str) -> str:
    d = desc.lower()
    if "ясно" in d or "чист" in d:      return "☀️"
    if "малооблач" in d:                 return "🌤"
    if "перемен" in d:                   return "⛅"
    if "облач" in d:                     return "☁️"
    if "пасмур" in d:                    return "🌥"
    if "гроза" in d:                     return "⛈"
    if "ливень" in d:                    return "🌧"
    if "дождь" in d:                     return "🌦"
    if "снег" in d:                      return "❄️"
    if "морос" in d:                     return "🌧"
    if "туман" in d or "дымка" in d:     return "🌫"
    return "🌤"


def temp_emoji(temp: float) -> str:
    if temp <= -20: return "🥶"
    if temp <= -5:  return "❄️"
    if temp <= 5:   return "🧣"
    if temp <= 15:  return "🍂"
    if temp <= 25:  return "😊"
    if temp <= 35:  return "🔥"
    return "🥵"


def temp_bar(temp: float, min_t: float = -30, max_t: float = 40) -> str:
    """Красивый температурный бар из юникод-символов."""
    filled = int(max(0, min(10, (temp - min_t) / (max_t - min_t) * 10)))
    if temp <= 0:
        bar = "🟦" * filled + "⬜" * (10 - filled)
    elif temp <= 15:
        bar = "🟨" * filled + "⬜" * (10 - filled)
    elif temp <= 25:
        bar = "🟧" * filled + "⬜" * (10 - filled)
    else:
        bar = "🟥" * filled + "⬜" * (10 - filled)
    return bar


def wind_direction(deg: int) -> str:
    arrows = ["⬆️ С", "↗️ СВ", "➡️ В", "↘️ ЮВ", "⬇️ Ю", "↙️ ЮЗ", "⬅️ З", "↖️ СЗ"]
    return arrows[round(deg / 45) % 8]


def wind_desc(speed: float) -> str:
    if speed < 1:   return "Штиль 🍃"
    if speed < 5:   return "Лёгкий ветерок 🍃"
    if speed < 10:  return "Умеренный ветер 💨"
    if speed < 15:  return "Сильный ветер 💨💨"
    if speed < 20:  return "Очень сильный ветер! 🌬"
    return "Ураганный ветер!!! 🌪"


def kids_advice(temp: float, desc: str, wind_speed: float) -> str:
    """Советы по одежде для детей — самая полезная фича для родителей!"""
    d = desc.lower()
    feels = temp - (wind_speed * 0.5)  # Простой учёт ветра

    lines = []

    # Одежда по температуре
    if feels <= -20:
        lines.append("🧥 Зимний комбинезон + термобельё")
        lines.append("🧣 Шарф, шапка-ушанка, варежки")
        lines.append("👢 Тёплые зимние сапоги")
        lines.append("⚠️ <b>Не гуляйте дольше 20 мин!</b>")
    elif feels <= -10:
        lines.append("🧥 Тёплая куртка + свитер")
        lines.append("🧣 Шарф и тёплая шапка")
        lines.append("🧤 Варежки обязательно!")
        lines.append("👢 Тёплая обувь")
    elif feels <= 0:
        lines.append("🧥 Зимняя куртка")
        lines.append("🧣 Шапка и перчатки")
        lines.append("👢 Утеплённая обувь")
    elif feels <= 10:
        lines.append("🧥 Демисезонная куртка")
        lines.append("🧢 Лёгкая шапка")
        lines.append("👟 Закрытая обувь")
    elif feels <= 18:
        lines.append("👕 Кофта + лёгкая куртка")
        lines.append("👖 Джинсы или штаны")
        lines.append("👟 Кроссовки")
    elif feels <= 25:
        lines.append("👕 Футболка и шорты")
        lines.append("🧢 Кепка от солнца")
        lines.append("👟 Лёгкая обувь")
    else:
        lines.append("👕 Лёгкая одежда")
        lines.append("🧢 Панамка обязательно!")
        lines.append("🧴 Солнцезащитный крем!")
        lines.append("💧 <b>Вода с собой!</b>")

    # Дополнительно по осадкам
    if "дождь" in d or "ливень" in d or "морос" in d:
        lines.append("☂️ <b>Не забудьте зонт!</b>")
        lines.append("👢 Резиновые сапоги")
    elif "снег" in d:
        lines.append("☃️ Можно лепить снеговика!")

    # Ветер
    if wind_speed > 10:
        lines.append("🌬 <b>Сильный ветер — капюшон!</b>")

    return "\n".join(f"   {line}" for line in lines)


def format_time_ago() -> str:
    now = datetime.now(timezone.utc) + timedelta(hours=3)  # МСК
    return now.strftime("%H:%M")


# ═══════════════════════════════════════════════════════
#  🌐 API ЗАПРОСЫ
# ═══════════════════════════════════════════════════════

async def fetch_weather(city_en: str) -> dict | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/weather", params={
                "q": city_en, "appid": OPENWEATHER_API_KEY,
                "units": "metric", "lang": "ru"
            }) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Weather API {resp.status}")
                return None
    except Exception as e:
        logger.error(f"Weather error: {e}")
        return None


async def fetch_forecast(city_en: str) -> dict | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/forecast", params={
                "q": city_en, "appid": OPENWEATHER_API_KEY,
                "units": "metric", "lang": "ru"
            }) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Forecast API {resp.status}")
                return None
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        return None


# ═══════════════════════════════════════════════════════
#  📝 ФОРМАТИРОВАНИЕ СООБЩЕНИЙ
# ═══════════════════════════════════════════════════════

def format_weather(data: dict, city_name: str, city_emoji: str) -> str:
    m = data["main"]
    w = data["weather"][0]
    wind = data["wind"]
    
    temp = round(m["temp"])
    feels = round(m["feels_like"])
    hum = m["humidity"]
    pres = m["pressure"]
    desc = w["description"].capitalize()
    ws = round(wind["speed"], 1)
    wd = wind.get("deg", 0)
    vis = data.get("visibility", 0)
    vis_km = round(vis / 1000, 1) if vis else "—"
    
    # Время восхода/заката
    sunrise = datetime.utcfromtimestamp(data["sys"]["sunrise"] + data["timezone"])
    sunset = datetime.utcfromtimestamp(data["sys"]["sunset"] + data["timezone"])
    
    we = weather_emoji(w["description"])
    te = temp_emoji(temp)
    bar = temp_bar(temp)
    
    msg = (
        f"{'═' * 25}\n"
        f"   {city_emoji} <b>{city_name}</b>\n"
        f"{'═' * 25}\n\n"
        
        f"   {we}  <b>{desc}</b>\n\n"
        
        f"   {te} <b>Температура</b>\n"
        f"   ┌─────────────────────┐\n"
        f"   │  🌡 Сейчас:  <b>{temp:+d}°C</b>\n"
        f"   │  🤔 Ощущ.:   <b>{feels:+d}°C</b>\n"
        f"   │  {bar}\n"
        f"   └─────────────────────┘\n\n"
        
        f"   💧 <b>Влажность:</b>   {hum}%\n"
        f"   🌬 <b>Ветер:</b>  {ws} м/с {wind_direction(wd)}\n"
        f"      <i>{wind_desc(ws)}</i>\n"
        f"   🔻 <b>Давление:</b>   {pres} гПа\n"
        f"   👁 <b>Видимость:</b>  {vis_km} км\n\n"
        
        f"   🌅 Восход: {sunrise.strftime('%H:%M')}  "
        f"🌇 Закат: {sunset.strftime('%H:%M')}\n\n"
        
        f"{'─' * 25}\n"
        f"   👶 <b>ОДЕВАЕМ ДЕТЕЙ:</b>\n"
        f"{'─' * 25}\n"
        f"{kids_advice(temp, w['description'], ws)}\n\n"
        
        f"{'─' * 25}\n"
        f"   🕐 Обновлено: {format_time_ago()} МСК\n"
        f"{'═' * 25}"
    )
    return msg


def format_forecast_msg(data: dict, city_name: str, city_emoji: str) -> str:
    if not data or "list" not in data:
        return "❌ Не удалось загрузить прогноз."

    days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    months_ru = ["", "янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]

    msg = (
        f"{'═' * 25}\n"
        f"   {city_emoji} <b>{city_name}</b>\n"
        f"   📅 <b>Прогноз на 5 дней</b>\n"
        f"{'═' * 25}\n\n"
    )

    seen = set()
    count = 0

    for item in data["list"]:
        dt_txt = item["dt_txt"]
        date_str = dt_txt.split(" ")[0]
        time_str = dt_txt.split(" ")[1]

        if date_str in seen:
            continue
        if time_str not in ("12:00:00", "15:00:00"):
            continue

        seen.add(date_str)
        count += 1
        if count > 5:
            break

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = days_ru[dt.weekday()]
        date_label = f"{dt.day} {months_ru[dt.month]}"

        temp = round(item["main"]["temp"])
        temp_min = round(item["main"]["temp_min"])
        temp_max = round(item["main"]["temp_max"])
        feels = round(item["main"]["feels_like"])
        desc = item["weather"][0]["description"].capitalize()
        we = weather_emoji(item["weather"][0]["description"])
        hum = item["main"]["humidity"]
        ws = round(item["wind"]["speed"], 1)
        te = temp_emoji(temp)

        bar = temp_bar(temp)

        msg += (
            f"   ┌─── {te} <b>{day_name}, {date_label}</b>\n"
            f"   │\n"
            f"   │  {we} {desc}\n"
            f"   │  🌡 <b>{temp_min:+d}°</b> … <b>{temp_max:+d}°</b>"
            f"  (ощущ. {feels:+d}°)\n"
            f"   │  {bar}\n"
            f"   │  💧 {hum}%   🌬 {ws} м/с\n"
            f"   │\n"
        )

        # Совет для детей на каждый день
        advice = kids_advice(temp, item["weather"][0]["description"], ws)
        advice_short = advice.split("\n")[0].strip() if advice else ""
        if advice_short:
            msg += f"   │  👶 {advice_short}\n"

        msg += f"   └{'─' * 24}\n\n"

    if count == 0:
        msg += "   Прогноз пока недоступен.\n\n"

    msg += (
        f"   🕐 Обновлено: {format_time_ago()} МСК\n"
        f"{'═' * 25}"
    )
    return msg


# ═══════════════════════════════════════════════════════
#  ⌨️ КЛАВИАТУРЫ
# ═══════════════════════════════════════════════════════

def city_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    items = list(CITIES.items())

    # По одному городу в ряд — крупные кнопки!
    for key, val in items:
        buttons.append([
            InlineKeyboardButton(
                text=f"{val['emoji']}  {val['name']}",
                callback_data=f"w_{key}"
            )
        ])

    # Кнопки подписки внизу
    buttons.append([
        InlineKeyboardButton(text="📬 Подписка на рассылку", callback_data="sub_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def detail_keyboard(city_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data=f"w_{city_key}"),
            InlineKeyboardButton(text="📅 Прогноз", callback_data=f"f_{city_key}"),
        ],
        [
            InlineKeyboardButton(text="🏙 Другой город", callback_data="cities"),
        ],
    ])


def sub_keyboard(user_id: str, subs: dict) -> InlineKeyboardMarkup:
    is_subbed = user_id in subs
    buttons = []

    if is_subbed:
        city_key = subs[user_id]["city"]
        city_name = CITIES.get(city_key, {}).get("name", "?")
        buttons.append([
            InlineKeyboardButton(
                text=f"✅ Подписка: {city_name}",
                callback_data="sub_info"
            )
        ])
        buttons.append([
            InlineKeyboardButton(text="❌ Отписаться", callback_data="unsub")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="📬 Подписаться (утро + вечер)",
                callback_data="sub_pick"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="cities")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def sub_city_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    items = list(CITIES.items())
    for key, val in items:
        buttons.append([
            InlineKeyboardButton(
                text=f"{val['emoji']}  {val['name']}",
                callback_data=f"sub_{key}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="sub_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ═══════════════════════════════════════════════════════
#  📨 ОБРАБОТЧИКИ КОМАНД
# ═══════════════════════════════════════════════════════

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"{'═' * 25}\n"
        f"   🌤 <b>ПОГОДА34</b>\n"
        f"   Волгоградская область\n"
        f"{'═' * 25}\n\n"
        f"   Привет! 👋\n\n"
        f"   Я — твой персональный бот\n"
        f"   погоды с советами по\n"
        f"   одежде для детей! 👶\n\n"
        f"   🌡 Текущая погода\n"
        f"   📅 Прогноз на 5 дней\n"
        f"   👶 Советы что надеть\n"
        f"   📬 Рассылка утром и вечером\n\n"
        f"{'─' * 25}\n"
        f"   Выбери город:\n"
        f"{'═' * 25}",
        reply_markup=city_keyboard(),
        parse_mode="HTML",
    )


@dp.message(Command("weather", "w"))
async def cmd_weather(message: types.Message):
    await message.answer(
        f"{'═' * 25}\n"
        f"   🏙 <b>ВЫБЕРИ ГОРОД</b>\n"
        f"{'═' * 25}",
        reply_markup=city_keyboard(),
        parse_mode="HTML",
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        f"{'═' * 25}\n"
        f"   ℹ️ <b>СПРАВКА</b>\n"
        f"{'═' * 25}\n\n"
        f"   /start — Приветствие\n"
        f"   /weather — Выбор города\n"
        f"   /help — Эта справка\n\n"
        f"   <b>Как пользоваться:</b>\n"
        f"   1️⃣ Выбери город\n"
        f"   2️⃣ Смотри погоду\n"
        f"   3️⃣ Читай советы для детей\n"
        f"   4️⃣ Подпишись на рассылку!\n\n"
        f"   📬 Рассылка приходит\n"
        f"   в <b>07:00</b> и <b>18:00</b> МСК\n\n"
        f"{'═' * 25}",
        parse_mode="HTML",
    )


# ═══════════════════════════════════════════════════════
#  🔘 CALLBACK ОБРАБОТЧИКИ
# ═══════════════════════════════════════════════════════

@dp.callback_query(F.data.startswith("w_"))
async def cb_weather(cb: types.CallbackQuery):
    key = cb.data[2:]
    if key not in CITIES:
        await cb.answer("❌ Город не найден")
        return

    city = CITIES[key]
    await cb.answer(f"⏳ {city['name']}...")

    data = await fetch_weather(city["en"])
    if data:
        msg = format_weather(data, city["name"], city["emoji"])
        try:
            await cb.message.edit_text(msg, reply_markup=detail_keyboard(key), parse_mode="HTML")
        except Exception:
            await cb.message.answer(msg, reply_markup=detail_keyboard(key), parse_mode="HTML")
    else:
        try:
            await cb.message.edit_text(
                f"❌ Не удалось загрузить погоду\nдля <b>{city['name']}</b>.\nПопробуй позже!",
                reply_markup=detail_keyboard(key), parse_mode="HTML"
            )
        except Exception:
            pass


@dp.callback_query(F.data.startswith("f_"))
async def cb_forecast(cb: types.CallbackQuery):
    key = cb.data[2:]
    if key not in CITIES:
        await cb.answer("❌ Город не найден")
        return

    city = CITIES[key]
    await cb.answer(f"⏳ Прогноз {city['name']}...")

    data = await fetch_forecast(city["en"])
    if data:
        msg = format_forecast_msg(data, city["name"], city["emoji"])
        try:
            await cb.message.edit_text(msg, reply_markup=detail_keyboard(key), parse_mode="HTML")
        except Exception:
            await cb.message.answer(msg, reply_markup=detail_keyboard(key), parse_mode="HTML")
    else:
        try:
            await cb.message.edit_text(
                f"❌ Не удалось загрузить прогноз\nдля <b>{city['name']}</b>.",
                reply_markup=detail_keyboard(key), parse_mode="HTML"
            )
        except Exception:
            pass


@dp.callback_query(F.data == "cities")
async def cb_cities(cb: types.CallbackQuery):
    await cb.answer()
    try:
        await cb.message.edit_text(
            f"{'═' * 25}\n"
            f"   🏙 <b>ВЫБЕРИ ГОРОД</b>\n"
            f"{'═' * 25}",
            reply_markup=city_keyboard(),
            parse_mode="HTML",
        )
    except Exception:
        await cb.message.answer(
            f"{'═' * 25}\n"
            f"   🏙 <b>ВЫБЕРИ ГОРОД</b>\n"
            f"{'═' * 25}",
            reply_markup=city_keyboard(),
            parse_mode="HTML",
        )


# ─── Подписка ───

@dp.callback_query(F.data == "sub_menu")
async def cb_sub_menu(cb: types.CallbackQuery):
    await cb.answer()
    subs = load_subs()
    uid = str(cb.from_user.id)

    if uid in subs:
        city_key = subs[uid]["city"]
        city_name = CITIES.get(city_key, {}).get("name", "?")
        text = (
            f"{'═' * 25}\n"
            f"   📬 <b>ПОДПИСКА</b>\n"
            f"{'═' * 25}\n\n"
            f"   ✅ Ты подписан!\n"
            f"   📍 Город: <b>{city_name}</b>\n\n"
            f"   Рассылка приходит:\n"
            f"   🌅 <b>07:00</b> — утренняя\n"
            f"   🌆 <b>18:00</b> — вечерняя\n\n"
            f"{'═' * 25}"
        )
    else:
        text = (
            f"{'═' * 25}\n"
            f"   📬 <b>ПОДПИСКА</b>\n"
            f"{'═' * 25}\n\n"
            f"   Подпишись и получай погоду\n"
            f"   автоматически каждый день!\n\n"
            f"   🌅 <b>07:00</b> — утренний прогноз\n"
            f"   🌆 <b>18:00</b> — вечерний прогноз\n\n"
            f"   С советами что надеть\n"
            f"   детям! 👶\n\n"
            f"{'═' * 25}"
        )

    try:
        await cb.message.edit_text(text, reply_markup=sub_keyboard(uid, subs), parse_mode="HTML")
    except Exception:
        await cb.message.answer(text, reply_markup=sub_keyboard(uid, subs), parse_mode="HTML")


@dp.callback_query(F.data == "sub_pick")
async def cb_sub_pick(cb: types.CallbackQuery):
    await cb.answer()
    try:
        await cb.message.edit_text(
            f"{'═' * 25}\n"
            f"   📬 <b>ВЫБЕРИ ГОРОД</b>\n"
            f"   для рассылки\n"
            f"{'═' * 25}",
            reply_markup=sub_city_keyboard(),
            parse_mode="HTML",
        )
    except Exception:
        pass


@dp.callback_query(F.data.startswith("sub_") & ~F.data.in_({"sub_menu", "sub_pick", "sub_info"}))
async def cb_subscribe(cb: types.CallbackQuery):
    key = cb.data[4:]
    if key not in CITIES:
        await cb.answer("❌ Город не найден")
        return

    subs = load_subs()
    uid = str(cb.from_user.id)
    subs[uid] = {"city": key, "chat_id": cb.message.chat.id}
    save_subs(subs)

    city = CITIES[key]
    await cb.answer(f"✅ Подписка на {city['name']}!")

    try:
        await cb.message.edit_text(
            f"{'═' * 25}\n"
            f"   ✅ <b>ПОДПИСКА ОФОРМЛЕНА!</b>\n"
            f"{'═' * 25}\n\n"
            f"   📍 Город: <b>{city['name']}</b>\n\n"
            f"   Ты будешь получать погоду:\n"
            f"   🌅 <b>07:00</b> утром\n"
            f"   🌆 <b>18:00</b> вечером\n\n"
            f"   С советами для детей! 👶\n\n"
            f"{'═' * 25}",
            reply_markup=sub_keyboard(uid, subs),
            parse_mode="HTML",
        )
    except Exception:
        pass


@dp.callback_query(F.data == "unsub")
async def cb_unsub(cb: types.CallbackQuery):
    subs = load_subs()
    uid = str(cb.from_user.id)
    if uid in subs:
        del subs[uid]
        save_subs(subs)

    await cb.answer("❌ Подписка отменена")
    try:
        await cb.message.edit_text(
            f"{'═' * 25}\n"
            f"   ❌ <b>ПОДПИСКА ОТМЕНЕНА</b>\n"
            f"{'═' * 25}\n\n"
            f"   Ты больше не будешь\n"
            f"   получать рассылку.\n\n"
            f"   Можешь подписаться снова\n"
            f"   в любой момент!\n\n"
            f"{'═' * 25}",
            reply_markup=sub_keyboard(uid, subs),
            parse_mode="HTML",
        )
    except Exception:
        pass


@dp.callback_query(F.data == "sub_info")
async def cb_sub_info(cb: types.CallbackQuery):
    await cb.answer("ℹ️ Рассылка: 07:00 и 18:00 МСК")


# ═══════════════════════════════════════════════════════
#  ⏰ ФОНОВАЯ РАССЫЛКА ПОГОДЫ
# ═══════════════════════════════════════════════════════

async def send_scheduled_weather():
    """Отправляет погоду подписчикам в 07:00 и 18:00 МСК."""
    logger.info("⏰ Планировщик рассылки запущен")

    while True:
        try:
            now = datetime.now(timezone.utc) + timedelta(hours=3)  # МСК
            hour = now.hour
            minute = now.minute

            # Отправляем в 07:00 и 18:00
            if (hour == 7 or hour == 18) and minute == 0:
                logger.info(f"📬 Время рассылки: {hour}:00")
                subs = load_subs()

                for uid, info in subs.items():
                    try:
                        city_key = info["city"]
                        chat_id = info["chat_id"]
                        city = CITIES.get(city_key)

                        if not city:
                            continue

                        data = await fetch_weather(city["en"])
                        if data:
                            period = "🌅 Доброе утро!" if hour == 7 else "🌆 Добрый вечер!"
                            header = (
                                f"{'═' * 25}\n"
                                f"   {period}\n"
                                f"   📬 <b>Ежедневная рассылка</b>\n"
                                f"{'═' * 25}\n\n"
                            )
                            msg = header + format_weather(data, city["name"], city["emoji"])
                            await bot.send_message(
                                chat_id=chat_id,
                                text=msg,
                                parse_mode="HTML",
                                reply_markup=detail_keyboard(city_key)
                            )

                        await asyncio.sleep(0.5)  # Пауза между отправками

                    except Exception as e:
                        logger.error(f"Ошибка рассылки для {uid}: {e}")

                # Ждём 61 секунду чтобы не отправить дважды
                await asyncio.sleep(61)
            else:
                # Проверяем каждые 30 секунд
                await asyncio.sleep(30)

        except Exception as e:
            logger.error(f"Ошибка планировщика: {e}")
            await asyncio.sleep(60)


# ═══════════════════════════════════════════════════════
#  🌐 WEB-СЕРВЕР ДЛЯ HEALTH CHECK (RENDER.COM)
# ═══════════════════════════════════════════════════════

async def handle_health(request):
    """Health check endpoint — UptimeRobot будет пинговать его."""
    return web.Response(text="🌤 POGODA34 Bot is alive!", status=200)

async def start_web_server():
    """Запускает веб-сервер для health check."""
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 Health-check сервер на порту {PORT}")


# ═══════════════════════════════════════════════════════
#  🚀 ЗАПУСК
# ═══════════════════════════════════════════════════════

async def main():
    logger.info("🚀 Погода34 запускается...")

    # Запускаем health-check сервер
    await start_web_server()

    # Запускаем планировщик рассылки
    asyncio.create_task(send_scheduled_weather())

    # Запускаем бота
    logger.info("🤖 Бот готов к работе!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
