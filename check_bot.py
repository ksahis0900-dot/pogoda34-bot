#!/usr/bin/env python3
"""
Скрипт для проверки статуса бота на Render
"""
import requests
import sys

RENDER_URL = "https://pogoda34-bot.onrender.com"

def check_bot_status():
    print(f"🔍 Проверяю статус бота на {RENDER_URL}...")
    
    try:
        response = requests.get(RENDER_URL, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ Бот работает! Ответ: {response.text}")
            return True
        else:
            print(f"⚠️ Бот вернул код {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Таймаут! Возможно бот спит (это нормально для бесплатного плана)")
        print("💡 Попробуйте отправить /start боту в Telegram - он проснется")
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к боту")
        print("Возможные причины:")
        print("  1. Бот еще не задеплоен на Render")
        print("  2. Неправильный URL")
        print("  3. Проблемы с интернетом")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = check_bot_status()
    sys.exit(0 if success else 1)
