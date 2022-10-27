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
from store import authenticate, get_all_products, get_file

app = Flask(__name__)


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


@app.route('/', methods=['POST'])
def webhook():
    '''
    Основной вебхук, на который будут приходить сообщения от Facebook.
    '''
    data = request.get_json()
    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                if messaging_event.get('message'):  # someone sent us a message
                    sender_id = messaging_event['sender']['id']        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event['recipient']['id']  # the recipient's ID, which should be your page's facebook ID
                    # message_text = 
                    send_menu(sender_id)
    return 'ok', 200


def send_menu(recipient_id):
    expiration = int(DB.get('token_expiration').decode('utf-8'))
    if expiration < time.time():
        moltin_token = authenticate(
            os.getenv('MOLTIN_CLIENT_ID'),
            os.getenv('MOLTIN_CLIENT_SECRET')
        )
        DB.set('token', moltin_token['token'])
        DB.set('token_expiration', moltin_token['expires'])
    token = DB.get('token').decode('utf-8')
    pizzas = get_all_products(token)[:5]
    
    elements = []
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
                {
                    'type':'postback',
                    'title':'Добавить в корзину',
                    'payload':'DEVELOPER_DEFINED_PAYLOAD'
                }              
            ]
        })    
    params = {'access_token': os.environ['PAGE_ACCESS_TOKEN']}
    headers = {'Content-Type': 'application/json'}
    request_content = json.dumps({
        'recipient': {
            'id': recipient_id
        },
        'message': {
            'attachment': {
                'type':'template',
                'payload': {
                    'template_type':'generic',
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
    response = requests.post('https://graph.facebook.com/v2.6/me/messages', params=params, headers=headers, data=request_content)
    print(response.text)
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
