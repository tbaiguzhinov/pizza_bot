from email import message
import os
import redis
from sqlite3 import dbapi2
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv

import requests
from flask import Flask, request
from store import authenticate, get_all_products, get_file, get_products_by_category_id

app = Flask(__name__)


PIZZA_CATEGORIES = {
    '77e66c39-6805-4afa-aeb7-92a6bce4e410': 'Основные',
    '99e7f4f4-a3a3-406c-9926-6274da515804': 'Особые',
    'd54f4c66-5758-4e2a-a741-42f6605d12f3': 'Сытные',
    '16ff3239-1a75-4c00-9d22-fac38746af4c': 'Острые',
}


@app.route('/', methods=['GET'])
def verify():
    '''
    При верификации вебхука у Facebook он отправит запрос на этот адрес. На него нужно ответить VERIFY_TOKEN.
    '''
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.challenge'):
        if not request.args.get('hub.verify_token') == os.environ['VERIFY_TOKEN']:
            return 'Verification token mismatch', 403
        return request.args['hub.challenge'], 200

    return 'Hello world', 200


def handle_start(sender_id, message_text):
    if message_text not in PIZZA_CATEGORIES:
        send_menu(sender_id, category='77e66c39-6805-4afa-aeb7-92a6bce4e410')
    else:
        send_menu(sender_id, category=message_text)
    return "START"


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
    }
    recorded_state = DB.get(sender_id)
    if not recorded_state or recorded_state.decode("utf-8") not in states_functions.keys():
        user_state = "START"
    else:
        user_state = recorded_state.decode("utf-8")
    if message_text == "/start":
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


def send_menu(recipient_id, category):
    token = DB.get('token').decode('utf-8')
    pizzas = get_products_by_category_id(token, category)

    elements = [{
        'title': 'Меню',
        'image_url': 'https://raw.githubusercontent.com/tbaiguzhinov/pizza_bot/facebook-bot/pizzeria_logo/Pizza-logo-design-template-Vector-PNG.png',
        'subtitle': 'Здесь вы можете выбрать один из вариантов',
        'buttons': [
            {
                'type': 'postback',
                'title': 'Корзина',
                'payload': 'DEVELOPER_DEFINED_PAYLOAD'
            },
            {
                'type': 'postback',
                'title': 'Акции',
                'payload': 'DEVELOPER_DEFINED_PAYLOAD'
            },
            {
                'type': 'postback',
                'title': 'Сделать заказ',
                'payload': 'DEVELOPER_DEFINED_PAYLOAD'
            }
        ]
    }]
    for pizza in pizzas:
        name = pizza['name']
        price = pizza['price'][0]['amount']
        description = pizza['description']
        file_id = pizza['relationships']['main_image']['data']['id']
        url = get_file(file_id=file_id, access_token=token)
        elements.append({
            'title': f'{name} ({price} р.)',
            'image_url': url['link']['href'],
            'subtitle': description,
            'buttons': [
                {'type': 'postback',
                 'title': 'Добавить в корзину',
                 'payload': 'DEVELOPER_DEFINED_PAYLOAD'},
            ]
        })
    elements.append({
        'title': 'Не нашли нужную пиццу?',
        'image_url': 'https://primepizza.ru/uploads/position/large_0c07c6fd5c4dcadddaf4a2f1a2c218760b20c396.jpg',
        'subtitle': 'Остальные пиццы можно посмотреть в одной из категорий',
        'buttons': []})
    for pizza_category, pizza_name in PIZZA_CATEGORIES.items():
        if pizza_category == category:
            continue
        elements[-1]['buttons'].append(
            {'type': 'postback',
             'title': pizza_name,
             'payload': pizza_category}
        )
    params = {'access_token': os.environ['PAGE_ACCESS_TOKEN']}
    headers = {'Content-Type': 'application/json'}
    request_content = json.dumps({
        'recipient': {
            'id': recipient_id
        },
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'generic',
                    'elements': elements,
                }
            }}
    })
    response = requests.post(
        'https://graph.facebook.com/v2.6/me/messages',
        params=params,
        headers=headers,
        data=request_content,
    )
    response.raise_for_status()


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
    response = requests.post('https://graph.facebook.com/v2.6/me/messages',
                             params=params, headers=headers, data=request_content)
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
