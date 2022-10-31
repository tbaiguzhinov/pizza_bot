import json
import os
import redis

from dotenv import load_dotenv
from store import (get_all_categories, get_file, get_product,
                   get_products_by_category_id, authenticate)


def get_categories(db):
    token = db.get('token').decode('utf-8')
    categories = get_all_categories(token=token)
    db.set('categories', json.dumps(categories))
    return categories


def get_menu(db, category):
    token = db.get('token').decode('utf-8')
    pizzas = get_products_by_category_id(token, category)
    for pizza in pizzas:
        file_id = pizza['relationships']['main_image']['data']['id']
        url = get_file(file_id=file_id, access_token=token)
        pizza['image_url'] = url
    db.set(category, json.dumps(pizzas))
    return pizzas


def get_pizza_image(db, product_id):
    token = db.get('token').decode('utf-8')
    product = get_product(product_id=product_id, access_token=token)
    image_url = get_file(
        file_id=product['relationships']['main_image']['data']['id'],
        access_token=token
    )['link']['href']
    db.set(product_id, image_url)
    return image_url


def main():
    load_dotenv()
    db = redis.Redis(
        host=os.getenv('DATABASE_HOST'),
        port=os.getenv('DATABASE_PORT'),
        password=os.getenv('DATABASE_PASSWORD')
    )
    moltin_token = authenticate(
        os.getenv('MOLTIN_CLIENT_ID'),
        os.getenv('MOLTIN_CLIENT_SECRET')
    )
    db.set('token', moltin_token['token'])

    categories = get_categories(db=db)
    for category in categories:
        products = get_menu(db, category['id'])
        for product in products:
            get_pizza_image(db, product['id'])


if __name__ == '__main__':
    main()
