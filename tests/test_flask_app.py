import pytest
from unittest.mock import patch, mock_open
from peewee import SqliteDatabase
from app import app
from core.database import Location, Room, Machine

# Use SQLite for testing
MODELS = [Location, Room, Machine]
test_db = SqliteDatabase(":memory:")

# Sample mock data for testing
mock_data = {
    "locationId": "loc1",
    "description": "Test Location",
    "label": "Test",
    "dryerCount": 1,
    "washerCount": 1,
    "machineCount": 2,
    "rooms": {
        "room1": {
            "roomId": "room1",
            "machines": [
                {
                    "licensePlate": "machine1",
                    "qrCodeId": "qr1",
                    "lastUser": None,
                    "type": "washer",
                    "stickerNumber": 1,
                }
            ],
        }
    },
}


@pytest.fixture
def setup_database():
    # Bind model classes to test db
    for model in MODELS:
        model._meta.database = test_db
    # Create tables
    test_db.connect()
    test_db.create_tables(MODELS)
    yield
    # Clean up
    test_db.drop_tables(MODELS)
    test_db.close()


@pytest.fixture
def client(setup_database):
    with app.test_client() as client:
        yield client


def test_get_data_success(client, setup_database):
    # Create test data in the database
    location = Location.create(
        locationId="loc1",
        description="Test Location",
        label="Test",
        dryerCount=1,
        washerCount=1,
        machineCount=2,
    )

    room = Room.create(
        roomId="room1",
        locationId=location,
        connected=True,
        description="Test Room",
        label="Room 1",
        dryerCount=1,
        washerCount=1,
        machineCount=2,
        freePlay=False,
    )

    Machine.create(
        licensePlate="machine1",
        qrCodeId="qr1",
        lastUser=None,
        available=True,
        type="washer",
        timeRemaining=0,
        mode="ready",
        roomId=room,
        locationId=location,
        stickerNumber=1,
        # Add missing required fields
        capability_addTime=True,
        capability_showAddTimeNotice=True,
        capability_showSettings=True,
        controllerType="test",
        doorClosed=True,
        freePlay=False,
        nfcId="nfc123",
        notAvailableReason="",
        opaqueId="op123",
        settings_cycle="normal",
        settings_dryerTemp="high",
        settings_soil="normal",
    )

    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["locationId"] == "loc1"


def test_claim_success(client, setup_database):
    # Create test data with all required fields
    location = Location.create(
        locationId="loc1",
        description="Test Location",
        label="Test Location",
        dryerCount=1,
        washerCount=1,
        machineCount=2,
    )

    room = Room.create(
        roomId="room1",
        locationId=location,
        connected=True,
        description="Test Room",
        label="Room 1",
        dryerCount=1,
        washerCount=1,
        machineCount=2,
        freePlay=False,
    )

    Machine.create(
        licensePlate="machine1",
        qrCodeId="qr1",
        lastUser=None,
        available=True,
        type="washer",
        timeRemaining=0,
        mode="ready",
        roomId=room,
        locationId=location,
        stickerNumber=1,
        # Add all required fields
        capability_addTime=True,
        capability_showAddTimeNotice=True,
        capability_showSettings=True,
        controllerType="test",
        doorClosed=True,
        freePlay=False,
        nfcId="nfc123",
        notAvailableReason="",
        opaqueId="op123",
        settings_cycle="normal",
        settings_dryerTemp="high",
        settings_soil="normal",
    )

    response = client.post(
        "/claim", json={"user_id": "user123", "machine_id": "machine1"}
    )
    assert response.status_code == 200
    assert response.get_json() == {"success": True}

    # Verify the machine was updated
    machine = Machine.get(Machine.licensePlate == "machine1")
    assert machine.lastUser == "user123"


def test_claim_missing_data(client):
    response = client.post("/claim", json={})
    assert response.status_code == 404
    assert response.get_json() == {"error": "No data provided"}


def test_claim_machine_not_found(client, setup_database):
    # Create test data with all required fields
    location = Location.create(
        locationId="loc1",
        description="Test Location",
        label="Test Location",
        dryerCount=1,
        washerCount=1,
        machineCount=2,
    )

    response = client.post(
        "/claim", json={"user_id": "user123", "machine_id": "invalid_machine"}
    )
    assert response.status_code == 404
    assert response.get_json() == {"error": "Machine with id invalid_machine not found"}


def test_access_logs_success(client):
    log_content = "Access log content"
    with patch("builtins.open", mock_open(read_data=log_content)):
        response = client.get("/logs/access")
        assert response.status_code == 200
        assert response.data.decode() == log_content


def test_access_logs_not_found(client):
    with patch("builtins.open", side_effect=FileNotFoundError):
        response = client.get("/logs/access")
        assert response.status_code == 404
        assert response.data.decode() == "access.log not found"
