import os

from dotenv import load_dotenv
from store import (authenticate, create_flow, create_field)


def main():
    load_dotenv()
    client_id = os.getenv('MOLTIN_CLIENT_ID')
    client_secret = os.getenv('MOLTIN_CLIENT_SECRET')
    token = authenticate(client_id, client_secret)

    flow_payload = create_flow(
        access_token=token['token'],
        name='Pizzeria',
        slug='pizzeria-1',
        description='',
        enabled=True,
    )
    flowId = flow_payload['data']['id']
    print(flowId)
    fields = [
        {
            'name': 'Address',
            'slug': 'address',
            'field_type': 'string',
            'description': 'Address field',
            'required': True,
            'enabled': True,
        },
        {
            'name': 'Alias',
            'slug': 'alias',
            'field_type': 'string',
            'description': 'Alias field',
            'required': True,
            'enabled': True
        },
        {
            'name': 'Longitude',
            'slug': 'longitude',
            'field_type': 'float',
            'description': 'Longitude field',
            'required': True,
            'enabled': True
        },
        {
            'name': 'Latitude',
            'slug': 'latitude',
            'field_type': 'float',
            'description': 'Latitude field',
            'required': True,
            'enabled': True,
        }
    ]
    for field in fields:
        field_payload = create_field(
            access_token=token['token'],
            name=field['name'],
            slug=field['slug'],
            field_type=field['field_type'],
            description=field['description'],
            required=field['required'],
            enabled=field['enabled'],
            flowId=flowId,
            )
        print(field_payload['data']['id'])


if __name__ == '__main__':
    main()
