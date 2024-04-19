from dotenv import load_dotenv
from telebot import types

import os
import telebot
import requests

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
# print(os.getenv('BOT_TOKEN'))
#
# if BOT_TOKEN is None:
#     print("Ошибка: токен бота не определен. Проверьте переменные окружения.")
#     exit(1)

bot = telebot.TeleBot(BOT_TOKEN)


# "Sey hello" function
@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я ваш crypto-помощник.\n/start\n/help\n/commands\n")


# Select the desired menu item
@bot.message_handler(commands=['commands'])
def list_commands(message):
    commands = (
        "/start - Начать работу с ботом\n"
        "/hello - Приветствие\n"
        "/rate - Получить текущие курсы криптовалют\n"
        "/save_contact - Сохранить контакт\n"
        "/view_contacts - Показать все контакты\n"
        "/delete_contact - Удалить контакт\n"
        "/help - Получить справку по командам"
    )
    bot.reply_to(message, commands)


# Response on "help" menu item
@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "Отправьте команду, и я помогу вам с информацией по ней.")


# Rate for Bitcoin
# def get_crypto_rate(coin_id='bitcoin'):
#     url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd'
#     response = requests.get(url)
#     data = response.json()
#     rate = data.get(coin_id, {}).get('usd', 'No data')
#     return rate


# Response on "rate" menu item
# @bot.message_handler(commands=['rate'])
# def get_rate(message):
#     coin_id = 'bitcoin'  # Will parametrize for different currencies rates
#     rate = get_crypto_rate(coin_id)
#     response_text = f"Курс {coin_id.capitalize()}: ${rate}"
#     bot.reply_to(message, response_text)


def get_crypto_rate(coin_id='bitcoin', currency='usd'):
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency}'
    response = requests.get(url)
    data = response.json()
    rate = data.get(coin_id, {}).get(currency, 'No data')
    return rate


# Response on "rate" menu item - choose the crypto
@bot.message_handler(commands=['rate'])
def handle_rate(message):
    markup = types.InlineKeyboardMarkup()
    cryptos = ['Bitcoin', 'Ethereum', 'Ripple', 'Litecoin']
    for crypto in cryptos:
        markup.add(types.InlineKeyboardButton(text=crypto, callback_data=f'crypto_{crypto.lower()}'))
    bot.send_message(message.chat.id, "Выберите криптовалюту:", reply_markup=markup)


# Response on "rate" menu item - choose the currency
@bot.callback_query_handler(func=lambda call: call.data.startswith('crypto_'))
def handle_crypto_choice(call):
    crypto = call.data.split('_')[1]
    markup = types.InlineKeyboardMarkup()
    currencies = ['USD', 'EUR', 'CHF', 'UAH']
    for currency in currencies:
        markup.add(types.InlineKeyboardButton(text=currency, callback_data=f'rate_{crypto}_{currency.lower()}'))
    bot.edit_message_text("Теперь выберите валюту:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)


# Show the rate
@bot.callback_query_handler(func=lambda call: call.data.startswith('rate_'))
def show_rate(call):
    _, crypto, currency = call.data.split('_')
    rate = get_crypto_rate(crypto, currency)
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"Курс {crypto.capitalize()} к {currency.upper()}: {rate}")


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, message.text)


bot.infinity_polling()
