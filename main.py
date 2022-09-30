import logging
import os
import textwrap
import time
from functools import partial

import redis
import telegram
from dotenv import load_dotenv
from email_validator import (EmailNotValidError, EmailSyntaxError,
                             validate_email)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, Filters, MessageHandler, Updater)

from get_logger import TelegramLogsHandler
from store import (add_to_cart, authenticate, create_customer,
                   get_all_products, get_cart, get_cart_items, get_file,
                   get_photo, get_product, remove_product_from_cart)
from get_location import get_coordinates

logger = logging.getLogger('Logger')


def get_product_keyboard(products):
    keyboard = []
    for product in products:
        button = [
            InlineKeyboardButton(
                product['name'],
                callback_data=product['id'],
            )
        ]
        keyboard.append(button)
    keyboard.append([InlineKeyboardButton(
        'Корзина', callback_data='cart')])
    return InlineKeyboardMarkup(keyboard)


def start(db, update: Update, context: CallbackContext):
    """Start bot."""
    products = get_all_products(db.get('token').decode("utf-8"))
    reply_markup = get_product_keyboard(products)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Пожалуйста, выберите:',
        reply_markup=reply_markup,
    )
    return "HANDLE_MENU"


def handle_menu(db, update: Update, context: CallbackContext):
    """Handle menu."""
    context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=update.callback_query.message.message_id,
    )
    callback = update.callback_query.data
    if callback == 'cart':
        return 'HANDLE_CART'
    product_id = callback
    product = get_product(product_id, db.get('token').decode("utf-8"))
    file = get_file(
        file_id=product['relationships']['main_image']['data']['id'],
        access_token=db.get('token').decode("utf-8"),
    )
    photo = get_photo(link=file['link']['href'])
    name = product['name']
    price = product['price'][0]['amount']
    description = product['description']
    text = f'{name}\n\nСтоимость: {price} рублей\n\n{description}'

    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('Добавить', callback_data=f'1,{product_id}'),
            ],
            [InlineKeyboardButton('Корзина', callback_data='cart')],
            [InlineKeyboardButton('Назад', callback_data='back')]]
    )

    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=photo,
        caption=text,
        reply_markup=reply_markup,
    )
    return "HANDLE_DESCRIPTION"


def handle_description(db, update: Update, context: CallbackContext):
    """Handle description of product."""
    callback = update.callback_query.data
    if callback == 'cart':
        client_id = update.effective_chat.id
        cart_items = get_cart_items(client_id, db.get('token').decode("utf-8"))
        cart_payload = get_cart(client_id, db.get('token').decode("utf-8"))
        grand_total = cart_payload[
            'meta']['display_price']['with_tax']['formatted']
        amount = 0
        text = []
        keyboard = []
        for item in cart_items:
            name = item['name']
            product_id = item['id']
            description = item['description']
            quantity = item['quantity']
            text.append(textwrap.dedent(
                f'''
                {name}
                {description}
                '''))
            amount += quantity
            keyboard.append([InlineKeyboardButton(
                f'Убрать из корзины {name}', callback_data=f'{product_id}')])
        text.append(textwrap.dedent(
            f'''
            {amount}пицц в корзине на сумму {grand_total}
            К оплате: {grand_total}
            '''))
        keyboard.append([InlineKeyboardButton(
            'Оплатить', callback_data='pay')])
        keyboard.append([InlineKeyboardButton('В меню', callback_data='back')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=''.join(text),
            reply_markup=reply_markup,
        )
        return 'HANDLE_CART'
    elif callback != 'back':
        quantity, product_id = callback.split(',')
        client_id = update.effective_chat.id
        add_to_cart(client_id, product_id,
                    int(quantity), db.get('token').decode("utf-8"))
        return "HANDLE_DESCRIPTION"
    else:
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.callback_query.message.message_id,
        )
        products = get_all_products(db.get('token').decode("utf-8"))
        reply_markup = get_product_keyboard(products)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Please choose:',
            reply_markup=reply_markup,
        )
        return "HANDLE_MENU"


def handle_cart(db, update: Update, context: CallbackContext):
    """Handle user cart."""
    callback = update.callback_query.data
    if callback == 'back':
        products = get_all_products(db.get('token').decode("utf-8"))
        keyboard = []
        for product in products:
            button = [
                InlineKeyboardButton(
                    product['name'],
                    callback_data=product['id'],
                )
            ]
            keyboard.append(button)
        keyboard.append([InlineKeyboardButton(
            'Корзина', callback_data='cart')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Пожалуйста, выберите:',
            reply_markup=reply_markup,
        )
        return "HANDLE_MENU"
    elif callback == 'pay':
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Пожалуйста, укажите Вашу почту:',
        )
        return 'OBTAIN_GEOLOCATION'
    else:
        remove_product_from_cart(
            product_id=callback,
            cart_id=update.effective_chat.id,
            access_token=db.get('token').decode("utf-8"),
        )
        return 'HANDLE_CART'


def obtain_email(db, update: Update, context: CallbackContext):
    """Get user email."""
    email = update.message.text
    try:
        email = validate_email(email, timeout=5).email
        text = f'Вы прислали мне эту почту: {email}'
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
        )
        create_customer(email, db.get('token').decode("utf-8"))
        text = 'Хорошо, пришлите нам ваш адрес текстом или геолокацию.'
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
        )
        return 'OBTAIN_GEOLOCATION'
    except (EmailSyntaxError, EmailNotValidError) as text:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=str(text),
        )
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Пожалуйста, укажите Вашу почту:',
        )
        return 'OBTAIN_EMAIL'


def obtain_geolocation(db, update: Update, context: CallbackContext):
    """Get users geolocation."""
    message = None
    if update.edited_message:
        message = update.edited_message
    else:
        message = update.message
    if message.location:
        current_pos = (message.location.latitude, message.location.longitude)
        context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=current_pos,
            )
    else:
        current_pos = get_coordinates(message.text, db.get('yandex_key').decode("utf-8"))
        if current_pos:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=current_pos,
            )
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Не удалось определить адрес, попробуйте еще раз.',
            )
            return 'OBTAIN_GEOLOCATION'
    return 'OBTAIN_EMAIL'


def handle_users_reply(
    db,
    update: Update,
    context: CallbackContext
):
    """Handle user replies."""
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'OBTAIN_EMAIL': obtain_email,
        'OBTAIN_GEOLOCATION': obtain_geolocation,
    }
    state_handler = states_functions[user_state]
    try:
        expiration = int(db.get('token_expiration').decode("utf-8"))
        if expiration < time.time():
            moltin_token = authenticate(
                os.getenv('MOLTIN_CLIENT_ID'),
                os.getenv('MOLTIN_CLIENT_SECRET')
            )
            db.set('token', moltin_token['token'])
            db.set('token_expiration', moltin_token['expires'])
            logger.error('Token updated')
        next_state = state_handler(db, update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def error_handler(update: Update, context: CallbackContext):
    """Handle errors."""
    logger.error(msg="Телеграм бот упал с ошибкой:", exc_info=context.error)


def main():
    """Main function."""
    load_dotenv()
    logger_bot_token = os.getenv('LOGGER_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    logger_bot = telegram.Bot(logger_bot_token)
    logger.addHandler(TelegramLogsHandler(logger_bot, chat_id))
    logger.warning("Pizza бот запущен")

    database_password = os.getenv("DATABASE_PASSWORD")
    database_host = os.getenv("DATABASE_HOST")
    database_port = os.getenv("DATABASE_PORT")
    db = redis.Redis(
        host=database_host,
        port=database_port,
        password=database_password
    )

    moltin_token = authenticate(
        os.getenv('MOLTIN_CLIENT_ID'),
        os.getenv('MOLTIN_CLIENT_SECRET')
    )
    
    db.set('token', moltin_token['token'])
    db.set('token_expiration', moltin_token['expires'])
    db.set('yandex_key', os.getenv('YANDEX_KEY'))
    
    expiration = moltin_token['expires']
    logger.error(f'Token updated until {expiration}')
    handle_users_reply_partial = partial(handle_users_reply, db)

    tg_token = os.getenv("TELEGRAM_TOKEN")
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply_partial))
    dispatcher.add_handler(MessageHandler(
        Filters.text, handle_users_reply_partial))
    dispatcher.add_handler(MessageHandler(
        Filters.location, handle_users_reply_partial))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply_partial))
    dispatcher.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
