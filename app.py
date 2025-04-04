from flask import Flask, request, jsonify, Response
from core.database import Location, Machine, db

app = Flask(__name__)


@app.before_request
def before_request():
    """Connect to database before each request"""
    db.connect(reuse_if_open=True) if db else None


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
