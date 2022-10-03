import requests

from geopy import distance


def get_coordinates(address, apikey):
    response = requests.get(
        "https://geocode-maps.yandex.ru/1.x",
        params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        }
    )
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection'][
        'featureMember'
    ]

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")

    return (lon, lat)


def measure_distance(lon1, lat1, lon2, lat2):
    return distance.distance((lat1, lon1), (lat2, lon2)).km


def get_closest_pizzeria(coordinates, pizzerias):
    customer_lon, customer_lat = coordinates
    pizzerias_coords = []
    for pizzeria in pizzerias:
        address = pizzeria['address']
        pizzeria_lon = pizzeria['longitude']
        pizzeria_lat = pizzeria['latitude']
        pizzerias_coords.append({
            'address': address,
            'longitude': pizzeria_lon,
            'latitude': pizzeria_lat,
            'distance': measure_distance(
                customer_lon,
                customer_lat,
                pizzeria_lon,
                pizzeria_lat,
            ),
        })

    def get_distance(pizzeria):
        return pizzeria['distance']
    return min(pizzerias_coords, key=get_distance)
