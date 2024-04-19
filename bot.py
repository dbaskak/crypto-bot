from dotenv import load_dotenv
import os
import telebot

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
print(os.getenv('BOT_TOKEN'))

if BOT_TOKEN is None:
    print("Ошибка: токен бота не определен. Проверьте переменные окружения.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, message.text)


bot.infinity_polling()
