import requests
import time
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from bs4 import BeautifulSoup

import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = 935294742

bot = Bot(token=TOKEN)

last_brent = None
last_diesel = None
last_alert = 0


# 🔹 нефть
def get_brent():
    try:
        url = "https://www.investing.com/commodities/brent-oil"
        headers = {"User-Agent": "Mozilla/5.0"}
        soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

        price = soup.select_one('[data-test="instrument-price-last"]')
        return float(price.text.replace(",", "")) if price else 0
    except:
        return 0


# 🔹 дизель (ICE Gasoil)
def get_diesel():
    try:
        url = "https://www.investing.com/commodities/london-gas-oil"
        headers = {"User-Agent": "Mozilla/5.0"}
        soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

        price = soup.select_one('[data-test="instrument-price-last"]')
        return float(price.text.replace(",", "")) if price else 0
    except:
        return 0


def check_market(context: CallbackContext):
    global last_brent, last_diesel, last_alert

    brent = get_brent()
    diesel = get_diesel()

    print(f"Brent: {brent} | Diesel: {diesel}")

    if brent == 0 or diesel == 0:
        return

    if last_diesel:
        change = ((diesel - last_diesel) / last_diesel) * 100

        # защита от спама (1 раз в час)
        if time.time() - last_alert > 3600:

            if change > 3:
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⛽ ЗАПРАВЬСЯ СЕЙЧАС!\nДизель +{change:.2f}%\nЦена: {diesel}\n👉 скоро подорожает"
                )
                last_alert = time.time()

            elif change > 2:
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚠️ Дизель растёт +{change:.2f}%\nЦена: {diesel}"
                )
                last_alert = time.time()

            elif change < -2:
                bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⛔ Можно подождать\nДизель падает {change:.2f}%\nЦена: {diesel}"
                )
                last_alert = time.time()

    last_brent = brent
    last_diesel = diesel


def price_command(update: Update, context: CallbackContext):
    brent = get_brent()
    diesel = get_diesel()

    update.message.reply_text(
        f"🛢 Brent: {brent}\n⛽ Diesel (Gasoil): {diesel}"
    )


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("price", price_command))

    updater.job_queue.run_repeating(check_market, interval=900, first=10)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()