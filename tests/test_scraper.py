import pytest
from unittest.mock import patch, Mock
import requests
from core.scraper import get_location_data, get_machines, scrape_location

# Sample mock data for testing
mock_location_response = {
    "locationId": "07cfb089-a19f-40c6-a6a7-5874aeb64d1b",
    "rooms": [
        {"roomId": "room1", "locationId": "07cfb089-a19f-40c6-a6a7-5874aeb64d1b"},
        {"roomId": "room2", "locationId": "07cfb089-a19f-40c6-a6a7-5874aeb64d1b"},
    ],
}

mock_machines_response = [
    {"type": "washer", "stickerNumber": 101},
    {"type": "dryer", "stickerNumber": 201},
]


@patch("scraper.requests.get")
def test_get_location_data_success(mock_get):
    mock_get.return_value = Mock(status_code=200)
    mock_get.return_value.json.return_value = mock_location_response

    result = get_location_data("07cfb089-a19f-40c6-a6a7-5874aeb64d1b")
    assert "rooms" in result
    assert len(result["rooms"]) == 2
    assert result["rooms"][0]["roomId"] == "room1"


@patch("scraper.requests.get")
def test_get_location_data_http_error(mock_get):
    mock_get.side_effect = requests.exceptions.HTTPError("404 Client Error")

    with pytest.raises(requests.exceptions.HTTPError):
        get_location_data("invalid-location-id")


@patch("scraper.requests.get")
def test_get_machines_success(mock_get):
    mock_get.return_value = Mock(status_code=200)
    mock_get.return_value.json.return_value = mock_machines_response

    room = {"roomId": "room1", "locationId": "07cfb089-a19f-40c6-a6a7-5874aeb64d1b"}
    result = get_machines(room)

    assert len(result) == 2
    assert result[0]["type"] == "dryer"  # Should be sorted
    assert result[1]["type"] == "washer"


@patch("scraper.get_location_data")
@patch("scraper.get_machines")
def test_scrape_location(mock_get_machines, mock_get_location_data):
    mock_get_location_data.return_value = mock_location_response
    # Return different machines for each room to avoid duplicates
    mock_get_machines.side_effect = [
        [{"type": "washer", "stickerNumber": 101}],
        [{"type": "dryer", "stickerNumber": 201}],
    ]

    location_data, rooms, machines = scrape_location(
        "07cfb089-a19f-40c6-a6a7-5874aeb64d1b"
    )

    assert "locationId" in location_data
    assert len(rooms) == 2
    assert len(machines) == 2
    # Verify machines are sorted by type and stickerNumber
    assert machines[0]["type"] == "dryer"
    assert machines[1]["type"] == "washer"
