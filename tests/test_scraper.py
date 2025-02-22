import pytest
from unittest.mock import patch, Mock
import requests
import json
from scraper import get_location_data, get_machines, scrape_location, run

# Sample mock data for testing
mock_location_response = {
    "locationId": "07cfb089-a19f-40c6-a6a7-5874aeb64d1b",
    "rooms": [
        {"roomId": "room1", "locationId": "07cfb089-a19f-40c6-a6a7-5874aeb64d1b"},
        {"roomId": "room2", "locationId": "07cfb089-a19f-40c6-a6a7-5874aeb64d1b"}
    ]
}

mock_machines_response = [
    {"type": "washer", "stickerNumber": 101},
    {"type": "dryer", "stickerNumber": 201}
]


@patch('scraper.requests.get')
def test_get_location_data_success(mock_get):
    mock_get.return_value = Mock(status_code=200)
    mock_get.return_value.json.return_value = mock_location_response

    result = get_location_data("07cfb089-a19f-40c6-a6a7-5874aeb64d1b")
    assert "rooms" in result
    assert len(result["rooms"]) == 2
    assert result["rooms"]["room1"]["roomId"] == "room1"


@patch('scraper.requests.get')
def test_get_location_data_http_error(mock_get):
    mock_get.side_effect = requests.exceptions.HTTPError("404 Client Error")

    with pytest.raises(requests.exceptions.HTTPError):
        get_location_data("invalid-location-id")


@patch('scraper.requests.get')
def test_get_machines_success(mock_get):
    mock_get.return_value = Mock(status_code=200)
    mock_get.return_value.json.return_value = mock_machines_response

    room = {"roomId": "room1", "locationId": "07cfb089-a19f-40c6-a6a7-5874aeb64d1b"}
    get_machines(room)

    assert "machines" in room
    assert len(room["machines"]) == 2
    assert room["machines"][0]["type"] == "dryer"
    assert room["machines"][1]["type"] == "washer"


@patch('scraper.get_location_data')
@patch('scraper.get_machines')
def test_scrape_location(mock_get_machines, mock_get_location_data):
    mock_get_location_data.return_value = mock_location_response
    mock_get_machines.side_effect = lambda room: room.update({"machines": mock_machines_response})

    result = scrape_location("07cfb089-a19f-40c6-a6a7-5874aeb64d1b")
    assert "rooms" in result
    assert len(result["rooms"]) == 2
    for room in result["rooms"].values():
        assert "machines" in room
        assert len(room["machines"]) == 2


@patch('scraper.scrape_location')
def test_run(mock_scrape_location, tmp_path):
    mock_scrape_location.return_value = mock_location_response

    output_file = tmp_path / "data.json"
    with patch("builtins.open", new_callable=patch("io.open", create=True)) as mock_open:
        run()
        mock_open.assert_called_once_with("data.json", "w")
        handle = mock_open()
        written_data = json.loads(handle.write.call_args[0][0])
        assert written_data == mock_location_response
