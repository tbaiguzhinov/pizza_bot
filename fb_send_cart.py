import requests
import os
import json


def send_cart(recipient_id, grand_total, cart_items):
    elements = get_cart_first_page(grand_total) + get_cart_pizzas(cart_items)

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


def get_cart_first_page(grand_total):
    return [{
        'title': 'Корзина',
        'image_url': 'https://internet-marketings.ru/wp-content/uploads/2018/08/idealnaya-korzina-internet-magazina-1068x713.jpg',
        'subtitle': f'Ваш заказ на сумму {grand_total} рублей',
        'buttons': [
            {
                'type': 'postback',
                'title': 'Самовывоз',
                'payload': 'pickup'
            },
            {
                'type': 'postback',
                'title': 'Доставка',
                'payload': 'delivery'
            },
            {
                'type': 'postback',
                'title': 'К меню',
                'payload': 'back'
            }
        ]
    }]


def get_cart_pizzas(pizzas):
    cart_pizzas = []
    for pizza in pizzas:
        name = pizza['name']
        description = pizza['description']
        quantity = pizza['quantity']
        cart_pizzas.append({
            'title': f'{name} ({quantity} шт.)',
            'image_url': pizza['image']['href'],
            'subtitle': description,
            'buttons': [
                {'type': 'postback',
                 'title': 'Добавить еще одну',
                 'payload': pizza['id']},
                {'type': 'postback',
                 'title': 'Убрать из корзины',
                 'payload': pizza['id']},
            ]
        })
    return cart_pizzas