"""Module to operate moltin store api."""
import requests


def authenticate(client_id, client_secret):
    """Authenticate."""
    response = requests.post(
        'https://api.moltin.com/oauth/access_token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
    )
    response.raise_for_status()
    payload = response.json()
    return {'token': payload['access_token'], 'expires': payload['expires']}


def get_all_products(access_token):
    """Get all products in store."""
    response = requests.get(
        'https://api.moltin.com/v2/products',
        headers={
            'Authorization': f'Bearer {access_token}',
        }
    )
    response.raise_for_status()
    return response.json()['data']


def get_file(file_id, access_token):
    """Get image file."""
    response = requests.get(
        f'https://api.moltin.com/v2/files/{file_id}',
        headers={
            'Authorization': f'Bearer {access_token}',
        }
    )
    response.raise_for_status()
    return response.json()['data']


def get_photo(link):
    """Download photo by bytes."""
    response = requests.get(link)
    response.raise_for_status()
    return response.content


def get_product(product_id, access_token):
    """Get a specific product."""
    response = requests.get(
        f'https://api.moltin.com/v2/products/{product_id}',
        headers={
            'Authorization': f'Bearer {access_token}',
        }
    )
    response.raise_for_status()
    return response.json()['data']


def get_cart(client_id, access_token):
    """Get a cart."""
    response = requests.get(
        f'https://api.moltin.com/v2/carts/{client_id}',
        headers={'Authorization': f'Bearer {access_token}'},
    )
    response.raise_for_status()
    return response.json()['data']


def get_cart_items(client_id, access_token):
    """Get all items in store cart."""
    response = requests.get(
        f'https://api.moltin.com/v2/carts/{client_id}/items',
        headers={'Authorization': f'Bearer {access_token}'},
    )
    response.raise_for_status()
    return response.json()['data']


def add_to_cart(client_id, product_id, quantity, access_token):
    """Add a product to cart."""
    payload = {
        "data": {
            "id": product_id,
            "type": "cart_item",
            "quantity": quantity,
        }}
    response = requests.post(
        f'https://api.moltin.com/v2/carts/{client_id}/items',
        headers={
            'Authorization': f'Bearer {access_token}',
        },
        json=payload,
    )
    response.raise_for_status()
    return response.json()


def remove_product_from_cart(product_id, cart_id, access_token):
    """Remove a product from cart."""
    response = requests.delete(
        f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}',
        headers={
            'Authorization': f'Bearer {access_token}',
        },
    )
    response.raise_for_status()


def create_customer(email, access_token):
    """Create a customer."""
    response = requests.post(
        'https://api.moltin.com/v2/customers',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        },
        json={
            'data': {
                'type': 'customer',
                'name': email,
                'email': email,
            }
        },
    )
    response.raise_for_status()


def create_product(access_token, payload):
    """Create a product."""
    response = requests.post(
        'https://api.moltin.com/v2/products',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        },
        json={
            'data': payload,
        },
    )
    response.raise_for_status()
    return response.json()


def create_file(access_token, file_location):
    """Create a file."""
    response = requests.post(
        'https://api.moltin.com/v2/files',
        headers={
            'Authorization': f'Bearer {access_token}',
        },
        files={
            'file_location': (None, file_location)
        }
    )
    response.raise_for_status()
    return response.json()


def create_image_relationship(access_token, productId, imageId):
    """Create relationship between file and product."""
    response = requests.post(
        f'https://api.moltin.com/v2/products/{productId}/relationships/main-image',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        },
        json={
            'data': {
                'type': 'main_image',
                'id': imageId,
            },
        }       
    )
    response.raise_for_status()
    return response.json()