import requests

def get_coordinates(address, apikey):
    print(address)
    response = requests.get(
        "https://geocode-maps.yandex.ru/1.x",
        params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        }
    )
    print(response)
    response.raise_for_status()
    print(response.json())
    found_places = response.json()['response']['GeoObjectCollection'][
        'featureMember'
    ]

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")

    return (lon, lat)
