from flask import Flask, request, jsonify, Response
from database import Location, Room, Machine

app = Flask(__name__)


@app.route("/", methods=["GET"])
def get_data():
    """
    Fetch all locations with their associated rooms and machines from the database.

    Returns:
        tuple: A tuple containing:
            - JSON response with an array of location objects, each containing:
                - Basic location info (ID, description, counts, etc.)
                - Nested rooms object with room details
                - Each room contains an array of machine objects
            - HTTP status code (200 for success, 500 for errors)

    Example Response:
        [
            {
                "locationId": "abc123",
                "description": "Main Building",
                "label": "Building A",
                "dryerCount": 10,
                "washerCount": 15,
                "machineCount": 25,
                "rooms": {
                    "room1": {
                        "roomId": "room1",
                        "machines": [
                            {
                                "licensePlate": "W001",
                                "available": true,
                                "type": "washer",
                                ...
                            }
                        ],
                        ...
                    }
                }
            }
        ]
    """
    try:
        locations = []
        for location in Location.select():
            loc_data = {
                "locationId": location.locationId,
                "description": location.description,
                "label": location.label,
                "dryerCount": location.dryerCount,
                "washerCount": location.washerCount,
                "machineCount": location.machineCount,
                "rooms": {}
            }
            
            for room in location.rooms:
                room_data = {
                    "roomId": room.roomId,
                    "connected": room.connected,
                    "description": room.description,
                    "label": room.label,
                    "dryerCount": room.dryerCount,
                    "washerCount": room.washerCount,
                    "machineCount": room.machineCount,
                    "freePlay": room.freePlay,
                    "machines": []
                }
                
                for machine in room.machines:
                    machine_data = {
                        "licensePlate": machine.licensePlate,
                        "qrCodeId": machine.qrCodeId,
                        "lastUser": machine.lastUser,
                        "available": machine.available,
                        "type": machine.type,
                        "timeRemaining": machine.timeRemaining,
                        "mode": machine.mode
                    }
                    room_data["machines"].append(machine_data)
                
                loc_data["rooms"][room.roomId] = room_data
            
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
        machine = (Machine
                  .select()
                  .where((Machine.licensePlate == machine_id) | 
                         (Machine.qrCodeId == machine_id))
                  .first())
        
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
