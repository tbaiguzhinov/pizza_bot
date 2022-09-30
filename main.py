import os

import requests
from dotenv import load_dotenv

from store import (authenticate, get_flow, create_entry)


def get_addresses():
    response = requests.get(
        'https://dvmn.org/media/filer_public/90/90/9090ecbf-249f-42c7-8635-a96985268b88/addresses.json',
    )
    response.raise_for_status()
    return response.json()


def main():
    load_dotenv()
    client_id = os.getenv('MOLTIN_CLIENT_ID')
    client_secret = os.getenv('MOLTIN_CLIENT_SECRET')
    token = authenticate(client_id, client_secret)

    pizzeriaFlowId = '4529323b-85cb-48d1-bae5-35381049131c'

    flow = get_flow(token['token'], pizzeriaFlowId)

    addresses = get_addresses()

    for item in addresses:
        fields_values = {
            'address': item['address']['full'],
            'alias': item['alias'],
            'longitude': float(item['coordinates']['lon']),
            'latitude': float(item['coordinates']['lat']),
        }
        entry_payload = create_entry(
            access_token=token['token'],
            flow_slug=flow['data']['slug'],
            field_values=fields_values)
        print(entry_payload['data'])

if __name__ == '__main__':
    main()
