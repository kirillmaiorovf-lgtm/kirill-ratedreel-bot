# bot.py
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
KINOPOISK_API_KEY = os.environ["KINOPOISK_API_KEY"]

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Напиши жанр (например, *боевик*)!", parse_mode="Markdown")

async def send_movies(update: Update, genre: str):
    headers = {
        "X-API-KEY": KINOPOISK_API_KEY,
        "User-Agent": "MovieBot/1.0"
    }
    try:
        response = requests.get(
            "https://api.kinopoisk.dev/v1.4/movie",
            params={"genres.name": genre, "rating.kp": "8.5-10", "limit": 3},
            headers=headers,
            timeout=10
        )
        if response.status_code != 200:
            await update.message.reply_text("⚠️ Не удалось получить данные.")
            return

        movies = response.json().get('docs', [])
        if not movies:
            await update.message.reply_text(f"😔 Нет фильмов по жанру «{genre}» с КП ≥ 8.5.")
            return

        for m in movies:
            name = m.get('name') or m.get('alternativeName', '—')
            year = m.get('year', '???')
            rating = m.get('rating', {}).get('kp', '—')
            desc = (m.get('description') or 'Описание отсутствует')[:120] + "…"
            poster = m.get('poster', {}).get('url')
            film_id = m.get('id')
            link = f"https://www.kinopoisk.ru/film/{film_id}" if film_id else "https://www.kinopoisk.ru"

            caption = f"🎬 <b>{name}</b> ({year})\n⭐ КП: {rating}\n\n{desc}\n<a href='{link}'>Подробнее</a>"

            if poster:
                await update.message.reply_photo(photo=poster, caption=caption, parse_mode="HTML")
            else:
                await update.message.reply_text(caption, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await update.message.reply_text("❌ Что-то пошло не так.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_movies(update, update.message.text.strip().lower())

if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()
