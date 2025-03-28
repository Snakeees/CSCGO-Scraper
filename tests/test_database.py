import pytest
import os
from peewee import SqliteDatabase

# Set testing environment
os.environ['TESTING'] = 'true'

from database import Location, Room, Machine

# Use SQLite for testing
MODELS = [Location, Room, Machine]
test_db = SqliteDatabase(':memory:')


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


def test_machine_time_remaining(setup_database):
    # Create test dependencies
    location = Location.create(
        locationId="test-loc",
        dryerCount=1,
        label="Test Location",
        machineCount=1,
        washerCount=0
    )

    room = Room.create(
        roomId="test-room",
        connected=True,
        dryerCount=1,
        freePlay=False,
        label="Test Room",
        locationId=location,
        machineCount=1,
        washerCount=0
    )

    # Test cases for timeRemaining
    test_cases = [
        (0, "idle machine"),
        (1800, "30 minute cycle"),
        (60, "final minute"),
        (3600, "1 hour cycle")
    ]

    for time_value, case_desc in test_cases:
        machine = Machine.create(
            available=True,
            capability_addTime=True,
            capability_showAddTimeNotice=True,
            capability_showSettings=True,
            controllerType="test",
            doorClosed=True,
            freePlay=False,
            licensePlate="TEST001",
            location=location,
            mode="ready",
            nfcId="nfc123",
            notAvailableReason="",
            opaqueId="op123",
            qrCodeId="qr123",
            roomId=room,
            settings_cycle="normal",
            settings_dryerTemp="high",
            settings_soil="normal",
            stickerNumber=1,
            timeRemaining=time_value,
            type="dryer"
        )

        # Verify the value was stored correctly
        saved_machine = Machine.get(Machine.opaqueId == "op123")
        assert saved_machine.timeRemaining == time_value, f"Failed for {case_desc}"

        # Clean up for next test case
        machine.delete_instance()


def test_machine_time_remaining_constraints(setup_database):
    location = Location.create(
        locationId="test-loc",
        dryerCount=1,
        label="Test Location",
        machineCount=1,
        washerCount=0
    )

    room = Room.create(
        roomId="test-room",
        connected=True,
        dryerCount=1,
        freePlay=False,
        label="Test Room",
        locationId=location,
        machineCount=1,
        washerCount=0
    )

    # Test negative time (should not be allowed in real application)
    with pytest.raises(ValueError):
        Machine.create(
            available=True,
            capability_addTime=True,
            capability_showAddTimeNotice=True,
            capability_showSettings=True,
            controllerType="test",
            doorClosed=True,
            freePlay=False,
            licensePlate="TEST001",
            location=location,
            mode="ready",
            nfcId="nfc123",
            notAvailableReason="",
            opaqueId="op123",
            qrCodeId="qr123",
            roomId=room,
            settings_cycle="normal",
            settings_dryerTemp="high",
            settings_soil="normal",
            stickerNumber=1,
            timeRemaining=-1,
            type="dryer"
        )
