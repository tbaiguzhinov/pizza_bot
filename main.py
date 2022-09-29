import os
from itertools import count
from urllib.error import HTTPError

import requests
from requests import HTTPError
from dotenv import load_dotenv
from transliterate import translit

from store import (authenticate, create_file, create_image_relationship,
                   create_product)


def get_addresses():
    response = requests.get(
        'https://dvmn.org/media/filer_public/90/90/9090ecbf-249f-42c7-8635-a96985268b88/addresses.json',
    )
    response.raise_for_status()
    return response.json()


def get_menu():
    response = requests.get(
        'https://dvmn.org/media/filer_public/a2/5a/a25a7cbd-541c-4caf-9bf9-70dcdf4a592e/menu.json',
    )
    response.raise_for_status()
    return response.json()


def main():
    menu_payload = get_menu()
    load_dotenv()
    client_id = os.getenv('MOLTIN_CLIENT_ID')
    client_secret = os.getenv('MOLTIN_CLIENT_SECRET')
    token = authenticate(client_id, client_secret)
    iterator = count(1, 1)
    for menu_item in menu_payload:
        name = menu_item['name']
        slug = translit(
            name,
            language_code='ru',
            reversed=True
        ).lower().rstrip().replace(' ', '-').replace('\'', '')
        sku = f'{slug}-{next(iterator):03}'
        payload = {
            'type': 'product',
            'name': name,
            'slug': slug,
            'sku': sku,
            'description': menu_item['description'],
            'manage_stock': False,
            'price': [
                {
                    'amount': menu_item['price'],
                    'currency': 'RUB',
                    'includes_tax': True,
                },
            ],
            'status': 'live',
            'commodity_type': 'physical',
        }
        product_result = create_product(
            access_token=token['token'], payload=payload)
        file_result = create_file(
            access_token=token['token'],
            file_location=menu_item['product_image']['url']
        )
        result = create_image_relationship(
            access_token=token['token'],
            productId=product_result['data']['id'],
            imageId=file_result['data']['id']
        )
        print(result)


if __name__ == '__main__':
    main()
