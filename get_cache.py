import json

from store import (get_all_categories, get_file, get_product,
                   get_products_by_category_id)


def get_categories(db):
    if 'categories' in db:
        return json.loads(db.get('categories').decode('utf-8'))
    token = db.get('token').decode('utf-8')
    categories = get_all_categories(token=token)
    db.set('categories', json.dumps(categories))
    return categories


def get_menu(db, category):
    if category in db:
        return json.loads(db.get(category).decode('utf-8'))
    token = db.get('token').decode('utf-8')
    pizzas = get_products_by_category_id(token, category)
    for pizza in pizzas:
        file_id = pizza['relationships']['main_image']['data']['id']
        url = get_file(file_id=file_id, access_token=token)
        pizza['image_url'] = url
    db.set(category, json.dumps(pizzas))
    return pizzas


def get_pizza_image(db, product_id):
    if product_id in db:
        return db.get(product_id).decode('utf-8')
    token = db.get('token').decode('utf-8')
    product = get_product(product_id=product_id, access_token=token)
    image_url = get_file(
        file_id=product['relationships']['main_image']['data']['id'],
        access_token=token
    )['link']['href']
    db.set(product_id, image_url)
    return image_url
