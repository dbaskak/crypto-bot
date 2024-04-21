from dotenv import load_dotenv
from telebot import types

import os
import telebot
import requests
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filename='bot.log',
                    filemode='w')
logger = logging.getLogger(__name__)

# contacts_db imports
from contacts import connect_db, add_contact, get_contacts, delete_contact

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

if BOT_TOKEN is None:
    print("Ошибка: токен бота не определен. Проверьте переменные окружения.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)


# "Sey hello" function
@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Привіт! Я ваш crypto-помічник.\n/start\n/help\n/commands\n")


# Select the desired menu item
@bot.message_handler(commands=['commands'])
def list_commands(message):
    commands = (
        "/start - Почати роботу з ботом\n"
        "/hello - Вітання\n"
        "/rate - отримати поточні курси криптовалют\n"
        "/save_contact - Зберегти контакт\n"
        "/view_contacts - Показати всі контакти\n"
        "/delete_contact - Видалити контакт\n"
        "/help - Отримати довідку по командам"
    )
    bot.reply_to(message, commands)


# Response on "help" menu item
@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "Відправте команду, та я допомогу вам с інфоромацієй по ній.")


# Raises error for bad responses
def get_crypto_rate(coin_id='bitcoin', currency='usd'):
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        rate = data.get(coin_id, {}).get(currency, 'No data')
        return rate
    except requests.RequestException as e:
        return f"Помилка: {str(e)}"


# Response on "rate" menu item - choose the crypto
@bot.message_handler(commands=['rate'])
def handle_rate(message):
    markup = types.InlineKeyboardMarkup()
    cryptos = ['Bitcoin', 'Ethereum', 'Ripple', 'Litecoin']
    for crypto in cryptos:
        markup.add(types.InlineKeyboardButton(text=crypto, callback_data=f'crypto_{crypto.lower()}'))
    bot.send_message(message.chat.id, "Оберіть криптовалюту:", reply_markup=markup)


# Response on "rate" menu item - choose the currency
@bot.callback_query_handler(func=lambda call: call.data.startswith('crypto_'))
def handle_crypto_choice(call):
    crypto = call.data.split('_')[1]
    markup = types.InlineKeyboardMarkup()
    currencies = ['USD', 'EUR', 'CHF', 'UAH']
    for currency in currencies:
        markup.add(types.InlineKeyboardButton(text=currency, callback_data=f'rate_{crypto}_{currency.lower()}'))
    bot.edit_message_text("Зараз оберіть валюту:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)


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


# contacts part
conn = connect_db()

user_data = {}


# User add
@bot.message_handler(commands=['add_contact'])
def handle_add_contact(message):
    logger.info(f"Користувач {message.from_user.id} запросив додавання нового контакта")
    bot.reply_to(message, "Введіть ім'я контакта:")
    bot.register_next_step_handler(message, ask_contact_name, message.from_user.id)


def ask_contact_name(message, user_id):
    user_data[message.from_user.id] = {'name': message.text}
    bot.reply_to(message, "Введіть номер телефону контакта:")
    bot.register_next_step_handler(message, ask_contact_phone, user_id)


def ask_contact_phone(message, user_id):
    user_data[message.from_user.id]['phone'] = message.text
    bot.reply_to(message, "Введіть email контакта:")
    bot.register_next_step_handler(message, ask_contact_email, user_id)


def ask_contact_email(message, user_id):
    user_data[message.from_user.id]['email'] = message.text
    conn = connect_db()
    try:
        add_contact(
            user_id,
            conn,
            name=user_data[message.from_user.id]['name'],
            phone=user_data[message.from_user.id]['phone'],
            email=user_data[message.from_user.id]['email']
        )
        bot.reply_to(message, "Контакт додано.")
    except Exception as e:
        logger.error("Помилка при додаванні контакта: %s", e)
        bot.reply_to(message, "Не вдалось додати контакт.")
    finally:
        del user_data[message.from_user.id]
        conn.close()



# contact preview
@bot.message_handler(commands=['view_contacts'])
def handle_view_contacts(message):
    user_id = message.from_user.id
    logger.info(f"Користувач {user_id} запросив перегляд контактів")
    conn = connect_db()  # bd connect
    try:
        contacts = get_contacts(user_id, conn)
        if not contacts:
            bot.reply_to(message, "Список контактів порожній.")
        else:
            response = "\n".join(f"{id} - {name}, {phone}, {email}" for id, name, phone, email in contacts)
            bot.reply_to(message, response)
    except Exception as e:
        logger.error("Помилка при вилучені контактів: %s", e)
        bot.reply_to(message, "Не вдалось отримати список контактів.")
    finally:
        conn.close()  # bd disconnect


# contact delete
@bot.message_handler(commands=['delete_contact'])
def handle_delete_contact(message):
    logger.info(f"Користувач {message.from_user.id} запросив видалення контакта")
    bot.reply_to(message, "Введіть ID контакта, який хочете видалити:")
    bot.register_next_step_handler(message, perform_contact_deletion, message.from_user.id)


def perform_contact_deletion(message, user_id):
    conn = connect_db()
    try:
        contact_id = int(message.text)
        if delete_contact(contact_id, user_id):
            bot.reply_to(message, "Контакт видалено.")
        else:
            bot.reply_to(message, "Контакт не знайдено або не належить вам.")
    except ValueError:
        bot.reply_to(message, "ID має бути числом. Спробуйте ще раз.")
    except Exception as e:
        logger.error("Помилка при видаленні контакта: %s", e)
        bot.reply_to(message, "Не вдалось видалити контакт.")
    finally:
        conn.close()


bot.infinity_polling()
