import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://mycscgo.com/api/v3/location"
LOCATION_ID = "07cfb089-a19f-40c6-a6a7-5874aeb64d1b"


def flatten_dict(d, parent_key="", sep="_"):
    """
    Flatten a nested dictionary into a single-level dictionary with composite keys.

    Args:
        d (dict): The dictionary to flatten
        parent_key (str, optional): The parent key for nested dictionaries. Defaults to ''.
        sep (str, optional): Separator between nested keys. Defaults to '_'.

    Returns:
        dict: Flattened dictionary where nested keys are joined with the separator

    Example:
        Input: {'a': {'b': 1, 'c': {'d': 2}}}
        Output: {'a_b': 1, 'a_c_d': 2}
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_location_data(location_id):
    """
    Fetch all rooms for the given location from the API.

    Args:
        location_id (str): Unique identifier for the location

    Returns:
        dict: Location data including sorted rooms list. Format:
            {
                "locationId": str,
                "description": str,
                "rooms": [
                    {
                        "roomId": str,
                        "locationId": str,
                        ...
                    },
                    ...
                ]
            }

    Raises:
        requests.exceptions.RequestException: If API request fails
    """
    url = f"{BASE_URL}/{location_id}"
    response = requests.get(url)
    response.raise_for_status()

    location_data = response.json()
    location_data["rooms"] = list(
        sorted(location_data["rooms"], key=lambda room: room["roomId"])
    )
    return location_data


def get_machines(room):
    """
    Fetch all machines for the given room from the API.

    Args:
        room (dict): Room dictionary containing 'locationId' and 'roomId'

    Returns:
        list: Sorted list of machine dictionaries, sorted by type and sticker number.
            [
                {
                    "type": str,
                    "stickerNumber": int,
                    "licensePlate": str,
                    ...
                },
                ...
            ]

    Raises:
        requests.exceptions.RequestException: If API request fails
    """
    url = f"{BASE_URL}/{room['locationId']}/room/{room['roomId']}/machines"
    response = requests.get(url)
    response.raise_for_status()
    return sorted(
        response.json(), key=lambda machine: (machine["type"], machine["stickerNumber"])
    )


def scrape_location(location_id):
    """
    Scrape location, rooms, and machines data concurrently from the API.

    Uses ThreadPoolExecutor to fetch machine data for multiple rooms in parallel,
    improving performance for locations with many rooms.

    Args:
        location_id (str): Unique identifier for the location

    Returns:
        tuple: Contains three elements:
            - dict: Location data (without rooms)
            - list: Room data sorted by roomId
            - list: Flattened machine data sorted by type and sticker number

    Example Return Format:
        (
            {
                "locationId": "abc123",
                "description": "Main Building",
                ...
            },
            [
                {
                    "roomId": "room1",
                    "locationId": "abc123",
                    ...
                },
                ...
            ],
            [
                {
                    "type": "washer",
                    "stickerNumber": 1,
                    "licensePlate": "W001",
                    ...
                },
                ...
            ]
        )

    Raises:
        requests.exceptions.RequestException: If any API request fails
    """
    location_data = get_location_data(location_id)
    rooms = location_data.pop("rooms")
    machines = []

    with ThreadPoolExecutor(max_workers=len(rooms)) as executor:
        future_to_room = {executor.submit(get_machines, room): room for room in rooms}

        for future in as_completed(future_to_room):
            machines.extend(map(flatten_dict, future.result()))

    machines.sort(key=lambda machine: (machine["type"], machine["stickerNumber"]))

    return location_data, rooms, machines


if __name__ == "__main__":
    print(scrape_location(LOCATION_ID))
