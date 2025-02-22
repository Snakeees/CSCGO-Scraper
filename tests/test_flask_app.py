import pytest
from unittest.mock import patch, mock_open
from flask import json
from app import app


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


# Mock data.json content
mock_data = {
    "rooms": {
        "room1": {
            "machines": [
                {"licensePlate": "machine1", "qrCodeId": "qr1", "lastUser": None},
                {"licensePlate": "machine2", "qrCodeId": "qr2", "lastUser": None}
            ]
        }
    }
}


def test_get_data_success(client):
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        response = client.get("/")
        assert response.status_code == 200
        assert response.get_json() == mock_data


def test_get_data_file_not_found(client):
    with patch("builtins.open", side_effect=FileNotFoundError):
        response = client.get("/")
        assert response.status_code == 404
        assert response.get_json() == {"error": "data.json not found"}


def test_get_data_invalid_json(client):
    with patch("builtins.open", mock_open(read_data="invalid json")):
        response = client.get("/")
        assert response.status_code == 404
        assert response.get_json() == {"error": "Invalid JSON format in data.json"}


def test_claim_success(client):
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))) as mock_file:
        response = client.post("/claim", json={"user_id": "user123", "machine_id": "machine1"})
        assert response.status_code == 200
        assert response.get_json() == {"success": True}


def test_claim_missing_data(client):
    response = client.post("/claim", json={})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Missing required fields"}


def test_claim_machine_not_found(client):
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        response = client.post("/claim", json={"user_id": "user123", "machine_id": "invalid_machine"})
        assert response.status_code == 404
        assert response.get_json() == {"error": "Machine with id invalid_machine not found"}


def test_access_logs_success(client):
    log_content = "Access log content"
    with patch("builtins.open", mock_open(read_data=log_content)):
        response = client.get("/logs/access")
        assert response.status_code == 200
        assert response.data.decode() == log_content


def test_access_logs_file_not_found(client):
    with patch("builtins.open", side_effect=FileNotFoundError):
        response = client.get("/logs/access")
        assert response.status_code == 404
        assert response.data.decode() == "access.log not found"


def test_error_logs_success(client):
    log_content = "Error log content"
    with patch("builtins.open", mock_open(read_data=log_content)):
        response = client.get("/logs/error")
        assert response.status_code == 200
        assert response.data.decode() == log_content


def test_error_logs_file_not_found(client):
    with patch("builtins.open", side_effect=FileNotFoundError):
        response = client.get("/logs/error")
        assert response.status_code == 404
        assert response.data.decode() == "error.log not found"
