from flask import Flask, request, jsonify, Response
from core.database import Location, Machine, db

app = Flask(__name__)


@app.before_request
def before_request():
    """Ensure fresh database connection before each request"""
    if db:
        if not db.is_closed():
            db.close()
        db.connect()


@app.teardown_request
def teardown_request(exception=None):
    """Close database connection after each request"""
    if db and not db.is_closed():
        db.close()


@app.route("/", methods=["GET"])
def get_data():
    """
    Fetch locations with their associated rooms and machines from the database.
    Supports filtering by room ID or machine ID using query parameters.

    Query Parameters:
        room (optional): Filter results to show only specified room ID
        machine (optional): Filter results to show only specified machine (license plate or QR code)

    Returns:
        tuple: A tuple containing:
            - JSON response with an array of location objects
            - HTTP status code (200 for success, 500 for errors)
    """
    try:
        room_id = request.args.get("room")
        machine_id = request.args.get("machine")

        locations = []
        for location in Location.select():
            loc_data = {
                "locationId": location.locationId,
                "description": location.description,
                "label": location.label,
                "dryerCount": location.dryerCount,
                "washerCount": location.washerCount,
                "machineCount": location.machineCount,
                "lastUpdated": location.lastUpdated,
                "rooms": {},
            }

            for room in location.rooms:
                # Skip if room filter is set and doesn't match
                if room_id and room.roomId != room_id:
                    continue

                room_data = {
                    "roomId": room.roomId,
                    "connected": room.connected,
                    "description": room.description,
                    "label": room.label,
                    "dryerCount": room.dryerCount,
                    "washerCount": room.washerCount,
                    "machineCount": room.machineCount,
                    "freePlay": room.freePlay,
                    "lastUpdated": room.lastUpdated,
                    "machines": [],
                }

                for machine in room.machines:
                    # Skip if machine filter is set and doesn't match
                    if (
                        machine_id
                        and machine.licensePlate != machine_id
                        and machine.qrCodeId != machine_id
                    ):
                        continue

                    machine_data = {
                        "licensePlate": machine.licensePlate,
                        "qrCodeId": machine.qrCodeId,
                        "lastUser": machine.lastUser,
                        "available": machine.available,
                        "type": machine.type,
                        "timeRemaining": machine.timeRemaining,
                        "mode": machine.mode,
                        "lastUpdated": machine.lastUpdated,
                    }
                    room_data["machines"].append(machine_data)

                # Only add room if it has machines (when machine filter is applied)
                if not machine_id or room_data["machines"]:
                    loc_data["rooms"][room.roomId] = room_data

            # Only add location if it has rooms (when room or machine filter is applied)
            if not (room_id or machine_id) or loc_data["rooms"]:
                locations.append(loc_data)

        return jsonify(locations), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/claim", methods=["POST"])
def get_claim():
    """
    Process a machine claim request by updating the lastUser field.

    Expected JSON payload:
        {
            "user_id": "string",    # ID of the user claiming the machine
            "machine_id": "string"  # License plate or QR code of the machine
        }

    Returns:
        tuple: A tuple containing:
            - JSON response with success status or error message
            - HTTP status code:
                - 200: Successful claim
                - 404: Missing data or machine not found
                - 500: Server error

    Example Success Response:
        {"success": true}

    Example Error Response:
        {"error": "Machine with id ABC123 not found"}
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 404

    user_id = data.get("user_id")
    machine_id = data.get("machine_id")

    if not user_id or not machine_id:
        return jsonify({"error": "Missing required fields"}), 404

    try:
        # Try to find machine by license plate or QR code
        machine = (
            Machine.select()
            .where(
                (Machine.licensePlate == machine_id) | (Machine.qrCodeId == machine_id)
            )
            .first()
        )

        if not machine:
            return jsonify({"error": f"Machine with id {machine_id} not found"}), 404

        # Update the lastUser field
        machine.lastUser = user_id
        machine.save()

        return jsonify({"success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _serialize_machine(machine, *, room=None, location=None):
    """Return a machine dict including room/location context."""
    return {
        "licensePlate": machine.licensePlate,
        "qrCodeId": machine.qrCodeId,
        "stickerNumber": machine.stickerNumber,
        "lastUser": machine.lastUser,
        "available": machine.available,
        "type": machine.type,
        "timeRemaining": machine.timeRemaining,
        "mode": machine.mode,
        "lastUpdated": machine.lastUpdated,
        # context for the PWA
        "roomId": getattr(room, "roomId", None) if room else None,
        "roomLabel": getattr(room, "label", None) if room else None,
        "locationId": getattr(location, "locationId", None) if location else None,
        "locationLabel": getattr(location, "label", None) if location else None,
    }


@app.route("/machines", methods=["GET"])
def list_machines():
    """
    Fetch a flat list of machines with optional filters.

    Query Parameters (all optional):
        room: Filter by roomId (string)
        location: Filter by locationId (string)
        machine: Filter by licensePlate or qrCodeId
        type: Filter by machine type ("washer" or "dryer")
        available: Filter by availability ("true"/"false"/"1"/"0")
        limit: Max number of results to return (default 100)
        offset: Number of results to skip (default 0)

    Returns:
        tuple: (JSON array of machines, 200) or error JSON with status code.
    """
    try:
        room_q = request.args.get("room")
        location_q = request.args.get("location")
        machine_q = request.args.get("machine")
        type_q = request.args.get("type")
        available_q = request.args.get("available")

        try:
            limit = int(request.args.get("limit", "10000"))
            offset = int(request.args.get("offset", "0"))
        except ValueError:
            return jsonify({"error": "limit/offset must be integers"}), 400

        out = []
        for location in Location.select():
            if location_q and str(location.locationId) != str(location_q):
                continue

            for room in location.rooms:
                if room_q and str(room.roomId) != str(room_q):
                    continue

                for machine in room.machines:
                    if machine_q and (
                        str(machine.licensePlate) != str(machine_q)
                        and str(machine.qrCodeId) != str(machine_q)
                    ):
                        continue

                    if type_q and str(machine.type).lower() != str(type_q).lower():
                        continue

                    if available_q is not None:
                        want = available_q.lower() in ("1", "true", "yes")
                        if bool(machine.available) != want:
                            continue

                    out.append(
                        _serialize_machine(machine, room=room, location=location)
                    )

        # Always return 200 with a list (even if empty), paginated slice
        return jsonify(out[offset : offset + limit]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/<room_id>/machines", methods=["GET"])
def list_room_machines(room_id: str):
    """
    Fetch machines within a specific room.

    Path:
        /<room_id>/machines

    Query Parameters (optional):
        machine: Filter by licensePlate or qrCodeId
        type: Filter by machine type ("washer" or "dryer")
        available: Filter by availability ("true"/"false"/"1"/"0")

    Returns:
        tuple: (JSON array of machines in the room, 200) or error JSON with status code.
    """
    try:
        type_q = request.args.get("type")
        available_q = request.args.get("available")
        machine_q = request.args.get("machine")

        found_room = None
        found_location = None

        for location in Location.select():
            for room in location.rooms:
                if str(room.roomId) == str(room_id):  # roomId is a string
                    found_room = room
                    found_location = location
                    break
            if found_room:
                break

        if not found_room:
            return jsonify({"error": f"room {room_id} not found"}), 404

        machines = []
        for machine in found_room.machines:
            if machine_q and (
                str(machine.licensePlate) != str(machine_q)
                and str(machine.qrCodeId) != str(machine_q)
            ):
                continue

            if type_q and str(machine.type).lower() != str(type_q).lower():
                continue

            if available_q is not None:
                want = available_q.lower() in ("1", "true", "yes")
                if bool(machine.available) != want:
                    continue

            machines.append(
                _serialize_machine(machine, room=found_room, location=found_location)
            )

        return jsonify(machines), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/logs/access", methods=["GET"])
def access_logs():
    """
    Fetch and return the contents of the access log file.

    Returns:
        Response: Plain text response containing:
            - Log file contents on success (200)
            - Error message if file not found (404)
    """
    try:
        with open("logs/access.log", "r") as f:
            content = f.read()
        return Response(content, mimetype="text/plain")
    except FileNotFoundError:
        return Response("access.log not found", status=404, mimetype="text/plain")


@app.route("/logs/error", methods=["GET"])
def error_logs():
    """
    Fetch and return the contents of the error log file.

    Returns:
        Response: Plain text response containing:
            - Log file contents on success (200)
            - Error message if file not found (404)
    """
    try:
        with open("logs/error.log", "r") as f:
            content = f.read()
        return Response(content, mimetype="text/plain")
    except FileNotFoundError:
        return Response("error.log not found", status=404, mimetype="text/plain")


@app.route("/discord/<discord_id>/room", methods=["GET"])
def get_discord_room(discord_id: str):
    """
    Get the room ID associated with a Discord ID.

    Path:
        /discord/<discord_id>/room

    Returns:
        tuple: JSON response with room ID or error message and status code
    """
    try:
        from core.database import Discord

        discord_entry = Discord.get_or_none(Discord.discordId == discord_id)

        if not discord_entry:
            return jsonify({"error": f"Discord ID {discord_id} not found"}), 404

        return jsonify({"discordId": discord_id, "roomId": discord_entry.roomId}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/discord/<discord_id>/room", methods=["POST"])
def set_discord_room(discord_id: str):
    """
    Set or update the room ID for a Discord ID.

    Path:
        /discord/<discord_id>/room

    Expected JSON payload:
        {
            "room_id": "string"  # Room ID to associate with Discord ID
        }

    Returns:
        tuple: JSON response with success status or error message and status code
    """
    try:
        from core.database import Discord

        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        room_id = data.get("room_id")

        if not room_id:
            return jsonify({"error": "Missing room_id field"}), 400

        # Create or update Discord entry
        discord_entry, created = Discord.get_or_create(
            discordId=discord_id, defaults={"roomId": room_id}
        )

        if not created:
            discord_entry.roomId = room_id
            discord_entry.save()

        return (
            jsonify(
                {
                    "success": True,
                    "discordId": discord_id,
                    "roomId": room_id,
                    "created": created,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
