"""
Netlify Serverless Function for Telegram Bot
"""
import json
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiohttp

# Environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

# Cities configuration
CITIES = {
    "lat=48.708&lon=44.513": {"name": "Волгоград", "emoji": "🏙"},
    "lat=48.818&lon=44.757": {"name": "Волжский", "emoji": "⚡️"},
    "lat=50.083&lon=45.4": {"name": "Камышин", "emoji": "🍉"},
    "lat=50.067&lon=43.233": {"name": "Михайловка", "emoji": "🚜"},
    "lat=50.8&lon=42.0": {"name": "Урюпинск", "emoji": "🐐"},
    "lat=49.773&lon=43.655": {"name": "Фролово", "emoji": "🛢"},
    "lat=48.691&lon=43.526": {"name": "Калач-на-Дону", "emoji": "⚓️"},
    "lat=47.583&lon=43.133": {"name": "Котельниково", "emoji": "🚂"},
    "lat=50.315&lon=44.807": {"name": "Котово", "emoji": "🌲"},
    "lat=48.608&lon=42.85": {"name": "Суровикино", "emoji": "🌾"},
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def fetch_weather(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json() if response.status == 200 else None

def format_weather(data, name):
    if not data:
        return "⚠️ Ошибка получения данных"
    temp = round(data['main']['temp'])
    desc = data['weather'][0]['description'].capitalize()
    return f"📍 <b>{name.upper()}</b>\n🌡 <b>{temp:+d}°C</b>, {desc}\n💨 Ветер: {data['wind']['speed']} м/с\n💧 Влажность: {data['main']['humidity']}%"

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    kb = InlineKeyboardBuilder()
    for key, value in CITIES.items():
        kb.button(text=f"{value['emoji']} {value['name']}", callback_data=f"w_{key}")
    kb.adjust(2)
    
    text = "🌤 <b>ПОГОДА 34</b>\nВыберите город:"
    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data and c.data.startswith("w_"))
async def weather_callback(callback: types.CallbackQuery):
    key = callback.data.split("w_")[1]
    city = CITIES[key]
    await callback.answer(f"Загружаю: {city['name']}")
    
    coords = key.replace("lat=", "").replace("lon=", "").split("&")
    data = await fetch_weather(coords[0], coords[1])
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Меню", callback_data="home")
    
    await callback.message.edit_text(
        format_weather(data, city['name']),
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@dp.callback_query(lambda c: c.data == "home")
async def home_callback(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.delete()
    await start_handler(callback.message)

async def process_update(update_data):
    """Process incoming Telegram update"""
    update = types.Update(**update_data)
    await dp.feed_update(bot, update)

def handler(event, context):
    """Netlify Function handler"""
    try:
        # Parse incoming webhook
        body = json.loads(event['body'])
        
        # Process update asynchronously
        asyncio.run(process_update(body))
        
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'ok'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
