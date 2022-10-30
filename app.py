import json
import os
import time

import redis
import requests
from dotenv import load_dotenv
from flask import Flask, request

from check_db import get_categories
from fb_send_cart import send_cart
from fb_send_menu import send_menu
from store import (add_to_cart, authenticate, get_cart,
                   get_cart_items, get_product, remove_product_from_cart)

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    if request.args.get('hub.mode') == 'subscribe' \
            and request.args.get('hub.challenge'):
        if not request.args.get(
            'hub.verify_token'
        ) == os.environ['VERIFY_TOKEN']:
            return 'Verification token mismatch', 403
        return request.args['hub.challenge'], 200

    return 'Hello world', 200


def handle_start(sender_id, message_text):
    categories = get_categories(db=DB)
    for category in categories:
        if category['name'] == 'Основные':
            send_menu(
                sender_id,
                category=category['id'],
                categories=categories,
                db=DB,
            )
    return "MENU"


def handle_menu(sender_id, message_text):
    token = DB.get('token').decode('utf-8')
    if message_text == 'cart':
        cart_payload = get_cart(
            client_id=f'facebook_{sender_id}',
            access_token=token,
        )
        grand_total = cart_payload[
            'meta']['display_price']['with_tax']['formatted']
        cart_items = get_cart_items(
            client_id=f'facebook_{sender_id}',
            access_token=token,
        )
        send_cart(
            recipient_id=sender_id,
            grand_total=grand_total,
            cart_items=cart_items,
        )
        return 'CART'

    categories = get_categories(db=DB)
    for pizza_category in categories:
        if message_text == pizza_category['id']:
            send_menu(
                sender_id,
                category=message_text,
                categories=categories,
                db=DB,
            )
            return 'MENU'
    add_to_cart(
        client_id=f'facebook_{sender_id}',
        product_id=message_text,
        quantity=1,
        access_token=token
    )
    product_name = get_product(
        product_id=message_text,
        access_token=token
    )['name']
    message = f'Пицца {product_name} добавлена в корзину'
    send_message(sender_id, message)
    return 'MENU'


def handle_cart(sender_id, message_text):
    token = DB.get('token').decode('utf-8')
    if message_text == 'back':
        categories = get_categories(db=DB)
        for category in categories:
            if category['name'] == 'Основные':
                send_menu(
                    sender_id,
                    category=category['id'],
                    categories=categories,
                    db=DB,
                )
                return 'MENU'
    elif ':' in message_text:
        command, pizza_id = message_text.split(':')
        if command == 'add':
            add_to_cart(
                client_id=f'facebook_{sender_id}',
                product_id=pizza_id,
                quantity=1,
                access_token=token
            )
            product_name = get_product(
                product_id=pizza_id,
                access_token=token
            )['name']
            message = f'Еше одна пицца {product_name} добавлена в корзину'
            send_message(sender_id, message)
        else:
            remove_product_from_cart(
                product_id=pizza_id,
                cart_id=f'facebook_{sender_id}',
                access_token=token,
            )
            message = 'Пицца удалена из корзины'
            send_message(sender_id, message)
    cart_payload = get_cart(
        client_id=f'facebook_{sender_id}',
        access_token=token,
    )
    grand_total = cart_payload[
        'meta']['display_price']['with_tax']['formatted']
    cart_items = get_cart_items(
        client_id=f'facebook_{sender_id}',
        access_token=token,
    )
    send_cart(
        recipient_id=sender_id,
        grand_total=grand_total,
        cart_items=cart_items,
    )
    return 'CART'


def handle_users_reply(sender_id, message_text):
    expiration = int(DB.get('token_expiration').decode('utf-8'))
    if expiration < time.time():
        moltin_token = authenticate(
            os.getenv('MOLTIN_CLIENT_ID'),
            os.getenv('MOLTIN_CLIENT_SECRET')
        )
        DB.set('token', moltin_token['token'])
        DB.set('token_expiration', moltin_token['expires'])

    states_functions = {
        'START': handle_start,
        'MENU': handle_menu,
        'CART': handle_cart,
    }
    recorded_state = DB.get(sender_id)
    if not recorded_state or recorded_state.decode(
        "utf-8"
    ) not in states_functions.keys():
        user_state = "START"
    else:
        user_state = recorded_state.decode("utf-8")
    if message_text == "start":
        user_state = "START"
    state_handler = states_functions[user_state]
    next_state = state_handler(sender_id, message_text)
    DB.set(sender_id, next_state)


@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                if messaging_event.get('message'):
                    handle_users_reply(
                        messaging_event['sender']['id'],
                        messaging_event["message"]["text"],
                    )
                elif messaging_event.get('postback'):
                    handle_users_reply(
                        messaging_event['sender']['id'],
                        messaging_event['postback']['payload'],
                    )
    return 'ok', 200


def send_message(recipient_id, message_text):
    params = {'access_token': os.environ['PAGE_ACCESS_TOKEN']}
    headers = {'Content-Type': 'application/json'}
    request_content = json.dumps({
        'recipient': {
            'id': recipient_id
        },
        'message': {
            'text': message_text
        }
    })
    response = requests.post(
        'https://graph.facebook.com/v2.6/me/messages',
        params=params,
        headers=headers,
        data=request_content,
    )
    response.raise_for_status()


def main():
    load_dotenv()
    global DB
    DB = redis.Redis(
        host=os.getenv('DATABASE_HOST'),
        port=os.getenv('DATABASE_PORT'),
        password=os.getenv('DATABASE_PASSWORD')
    )
    moltin_token = authenticate(
        os.getenv('MOLTIN_CLIENT_ID'),
        os.getenv('MOLTIN_CLIENT_SECRET')
    )

    DB.set('token', moltin_token['token'])
    DB.set('token_expiration', moltin_token['expires'])
    app.run(debug=True)


if __name__ == '__main__':
    main()
