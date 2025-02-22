import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

BASE_URL = "https://mycscgo.com/api/v3/location"
LOCATION_ID = "07cfb089-a19f-40c6-a6a7-5874aeb64d1b"


def get_location_data(location_id):
    """Fetch all rooms for the given location."""
    url = f"{BASE_URL}/{location_id}"
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    data["rooms"] = {room["roomId"]: room for room in sorted(data["rooms"], key=lambda room: room['roomId'])}
    return data


def get_machines(room):
    """Fetch all machines for the given room."""
    url = f"{BASE_URL}/{room['locationId']}/room/{room['roomId']}/machines"
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    room['machines'] = room['machines'] = sorted(data, key=lambda machine: (machine['type'], machine['stickerNumber']))


def scrape_location(location_id):
    """Scrape rooms and machines concurrently."""
    location_data = get_location_data(location_id)
    rooms = location_data["rooms"]

    with ThreadPoolExecutor(max_workers=len(rooms)) as executor:
        future_to_room = [executor.submit(get_machines, room) for room in rooms.values()]

        for future in as_completed(future_to_room):
            future.result()

    return location_data


def run():
    """Scrape location data and save it to a JSON file."""
    machines_info = scrape_location(LOCATION_ID)

    # Save to JSON file
    with open("data.json", "w") as f:
        json.dump(machines_info, f, indent=4)

    return f"Data saved to data.json"


if __name__ == "__main__":
    print(run())
