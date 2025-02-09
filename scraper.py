import requests
import concurrent.futures
import json

BASE_URL = "https://mycscgo.com/api/v3/location"
LOCATION_ID = "07cfb089-a19f-40c6-a6a7-5874aeb64d1b"


def get_rooms(location_id):
    """Fetch all rooms for the given location."""
    url = f"{BASE_URL}/{location_id}"
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    return list(filter(None, [room.get("roomId", None) for room in data.get("rooms", [])]))


def get_machines(room_id):
    """Fetch all machines for the given room."""
    url = f"{BASE_URL}/{LOCATION_ID}/room/{room_id}/machines"
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()
    return {room_id: data}


def scrape_location(location_id):
    """Scrape rooms and machines concurrently."""
    rooms = get_rooms(location_id)
    machines_data = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(rooms)) as executor:
        future_to_room = {executor.submit(get_machines, room): room for room in rooms}

        for future in concurrent.futures.as_completed(future_to_room):
            room_id = future_to_room[future]
            try:
                machines_data.update(future.result())
            except Exception as e:
                print(f"Error fetching machines for room {room_id}: {e}")

    return machines_data


if __name__ == "__main__":
    machines_info = scrape_location(LOCATION_ID)

    # Save to JSON file
    with open("data.json", "w") as f:
        json.dump(machines_info, f, indent=4)

    print(f"Data saved to data.json")
