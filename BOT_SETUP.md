# Настройка бота

## Шаг 1: Создай бота в Telegram

1. Открой [@BotFather](https://t.me/BotFather) в Telegram
2. Отправь `/newbot`
3. Введи имя бота
4. Скопируй токен

## Шаг 2: Получи API ключ OpenWeather

1. Зарегистрируйся на [openweathermap.org](https://openweathermap.org)
2. Перейди в раздел "API Keys"
3. Скопируй ключ (бесплатный план даёт 1000 запросов/день)

## Шаг 3: Заполни .env файл

```env
BOT_TOKEN=твой_токен
OPENWEATHER_API_KEY=твой_ключ
```

## Шаг 4: Запусти бота

```bash
pip install -r requirements.txt
python bot.py
```

Готово! Бот запущен и отвечает в Telegram.