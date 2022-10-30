import json
import os

import requests

from check_db import get_menu, get_pizza_image


def send_menu(recipient_id, category, categories, db):
    pizzas = get_menu(db=db, category=category)

    elements = get_menu_first_page() + get_pizza_menu(pizzas, db) + \
        get_other_pizzas(category, categories)

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


def get_menu_first_page():
    return [{
        'title': 'Меню',
        'image_url': 'https://raw.githubusercontent.com/tbaiguzhinov/pizza_bot/facebook-bot/pizzeria_logo/Pizza-logo-design-template-Vector-PNG.png',
        'subtitle': 'Здесь вы можете выбрать один из вариантов',
        'buttons': [
            {
                'type': 'postback',
                'title': 'Корзина',
                'payload': 'cart'
            },
            {
                'type': 'postback',
                'title': 'Акции',
                'payload': 'actions'
            },
            {
                'type': 'postback',
                'title': 'Сделать заказ',
                'payload': 'order'
            }
        ]
    }]


def get_pizza_menu(pizzas, db):
    pizza_menu = []
    for pizza in pizzas:
        name = pizza['name']
        price = pizza['price'][0]['amount']
        image_url = get_pizza_image(db=db, product_id=pizza['id'])
        pizza_menu.append({
            'title': f'{name} ({price} р.)',
            'image_url': image_url,
            'subtitle': pizza['description'],
            'buttons': [
                {'type': 'postback',
                 'title': 'Добавить в корзину',
                 'payload': pizza['id']},
            ]
        })
    return pizza_menu


def get_other_pizzas(category, categories):
    pizza_menus = {
        'title': 'Не нашли нужную пиццу?',
        'image_url': 'https://primepizza.ru/uploads/position/large_0c07c6fd5c4dcadddaf4a2f1a2c218760b20c396.jpg',
        'subtitle': 'Остальные пиццы можно посмотреть в одной из категорий',
        'buttons': []}
    for pizza_category in categories:
        if pizza_category['id'] == category:
            continue
        pizza_menus['buttons'].append(
            {'type': 'postback',
             'title': pizza_category['name'],
             'payload': pizza_category['id']}
        )
    return [pizza_menus]
