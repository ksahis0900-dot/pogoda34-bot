import asyncio
import os
from aiogram import Bot
from dotenv import load_dotenv

async def check_bot():
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Error: No BOT_TOKEN found in .env")
        return
    
    try:
        bot = Bot(token=token)
        me = await bot.get_me()
        print(f"Bot connected: @{me.username} ({me.id})")
        await bot.session.close()
    except Exception as e:
        print(f"Error connecting to bot: {e}")

if __name__ == "__main__":
    asyncio.run(check_bot())
