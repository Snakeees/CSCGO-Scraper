import os
import datetime
from peewee import (
    MySQLDatabase,
    Model,
    CharField,
    TextField,
    IntegerField,
    BooleanField,
    DateTimeField,
    ForeignKeyField,
)
from typing import Dict, Any

# Initialize db as None - will be set based on environment
if os.getenv('TESTING'):
    db = None  # Will be set by tests
else:
    if os.getenv("DATABASE_IP") is None:
        raise Exception("DATABASE_IP is not set")

    # Establish a connection to the MySQL database using environment variables
    db = MySQLDatabase(
        os.getenv("DATABASE_COLLECTION"),
        user=os.getenv("DATABASE_USERNAME"),
        password=os.getenv("DATABASE_PASSWORD"),
        host=os.getenv("DATABASE_IP"),
        port=int(os.getenv("DATABASE_PORT")),
    )
    # Connect only if not in testing mode
    db.connect()


# BaseModel to set the database for all models
class BaseModel(Model):
    class Meta:
        database = db

    @classmethod
    def _check_updates_needed(cls, existing: Any, data: Dict[str, Any], exclude_fields: tuple = ('lastUpdated',)) -> bool:
        for key, new_value in data.items():
            if key in exclude_fields:
                continue
            if getattr(existing, key) != new_value:
                return True
        return False


# Location table definition
class Location(BaseModel):
    locationId = CharField(primary_key=True)  # Primary key
    description = TextField(null=True)  # Optional description
    dryerCount = IntegerField()  # Number of dryers at the location
    label = CharField()  # Label/name of the location
    machineCount = IntegerField()  # Total number of machines
    washerCount = IntegerField()  # Number of washers
    lastUpdated = DateTimeField(default=datetime.datetime.now)  # Timestamp of last update

    @classmethod
    def upsert(cls, data: Dict[str, Any]) -> None:
        loc_id = data.get('locationId')
        existing = cls.get_or_none(cls.locationId == loc_id)

        if existing is None:
            data['lastUpdated'] = datetime.datetime.now()
            cls.create(**data)
        elif cls._check_updates_needed(existing, data):
            data['lastUpdated'] = datetime.datetime.now()
            cls.update(**data).where(cls.locationId == loc_id).execute()


# Room table definition
class Room(BaseModel):
    roomId = CharField(primary_key=True)  # Primary key
    connected = BooleanField()  # Indicates if the room is connected
    description = TextField(null=True)  # Optional room description
    dryerCount = IntegerField()  # Number of dryers in the room
    freePlay = BooleanField()  # Indicates if machines are in free play mode
    label = CharField()  # Label/name of the room
    locationId = ForeignKeyField(Location, backref='rooms', column_name='locationId')  # FK to Location
    machineCount = IntegerField()  # Total number of machines
    washerCount = IntegerField()  # Number of washers
    lastUpdated = DateTimeField(default=datetime.datetime.now)  # Timestamp of last update

    @classmethod
    def upsert(cls, data: Dict[str, Any]) -> None:
        room_id = data.get('roomId')
        existing = cls.get_or_none(cls.roomId == room_id)

        if existing is None:
            data['lastUpdated'] = datetime.datetime.now()
            cls.create(**data)
        elif cls._check_updates_needed(existing, data):
            data['lastUpdated'] = datetime.datetime.now()
            cls.update(**data).where(cls.roomId == room_id).execute()


# Machine table definition
class Machine(BaseModel):
    available = BooleanField()  # Availability status
    capability_addTime = BooleanField()  # Can add time?
    capability_showAddTimeNotice = BooleanField()  # Show add-time notice?
    capability_showSettings = BooleanField()  # Show settings?
    controllerType = CharField()  # Controller type
    display = TextField(null=True)  # Display text
    doorClosed = BooleanField()  # Is door closed?
    freePlay = BooleanField()  # Is in free play mode?
    groupId = CharField(null=True)  # Optional group ID
    inService = BooleanField(null=True)  # In service or not
    licensePlate = CharField()  # Machine's license plate
    location = ForeignKeyField(Location, backref='machines', column_name='locationId')  # FK to Location
    mode = CharField()  # Current mode
    nfcId = CharField()  # NFC identifier
    notAvailableReason = CharField()  # Reason for unavailability
    opaqueId = CharField()  # Opaque identifier
    qrCodeId = CharField()  # QR code identifier
    roomId = ForeignKeyField(Room, backref='machines', column_name='roomId')  # FK to Room
    settings_cycle = CharField()  # Selected cycle setting
    settings_dryerTemp = CharField()  # Dryer temperature setting
    settings_soil = CharField()  # Soil level setting
    settings_washerTemp = CharField(null=True)  # Optional washer temperature
    stackItems = TextField(null=True)  # Optional stack info
    stickerNumber = IntegerField()  # Sticker number
    timeRemaining = IntegerField()  # Time remaining in current cycle
    type = CharField()  # Machine type (e.g., washer, dryer)
    lastUpdated = DateTimeField(default=datetime.datetime.now)  # Timestamp of last update
    lastUser = CharField(null=True)  # Optional last user ID or name

    def save(self, *args, **kwargs):
        if self.timeRemaining < 0:
            raise ValueError("timeRemaining cannot be negative")
        return super().save(*args, **kwargs)

    @classmethod
    def create(cls, **query):
        if query.get('timeRemaining', 0) < 0:
            raise ValueError("timeRemaining cannot be negative")
        return super().create(**query)

    @classmethod
    def upsert(cls, data: Dict[str, Any]) -> None:
        opaque_id = data.get('opaqueId')
        existing = cls.get_or_none(cls.opaqueId == opaque_id)

        if existing is None:
            data['lastUpdated'] = datetime.datetime.now()
            data['lastUser'] = "Unknown"
            cls.create(**data)
        elif cls._check_updates_needed(existing, data, exclude_fields=('lastUpdated', 'lastUser')):
            data['lastUpdated'] = datetime.datetime.now()
            if data["timeRemaining"] - existing.timeRemaining > 5:
                data['lastUser'] = "Unknown"
            cls.update(**data).where(cls.opaqueId == opaque_id).execute()


# Connect to the database and create tables if they don't exist
if not os.getenv('TESTING'):
    db.create_tables([Location, Room, Machine], safe=True)
