import requests


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
    print(get_addresses())
    print(get_menu())


if __name__ == '__main__':
    main()
