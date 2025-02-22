from flask import Flask, request, jsonify, Response
import json

app = Flask(__name__)


def load_data():
    """Load data from JSON file."""
    try:
        with open("data.json", "r") as f:
            return json.load(f), 200
    except FileNotFoundError:
        return {"error": "data.json not found"}, 404
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format in data.json"}, 404


def save_data(data):
    """Save data into JSON file."""
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)


def claim(user_id, machine_id):
    data, status = load_data()
    if status != 200:
        return data, status

    for room in data.get("rooms", {}).values():
        for machine in room.get("machines", []):
            if machine["licensePlate"] == machine_id or machine["qrCodeId"] == user_id:
                machine["lastUser"] = user_id
                save_data(data)
                return {"success": True}, 200

    return {"error": f"Machine with id {machine_id} not found"}, 404


@app.route("/", methods=["GET"])
def get_data():
    """Fetch and return data.json content."""
    data, status = load_data()
    return jsonify(data), status


@app.route("/claim", methods=["POST"])
def get_claim():
    # Parse JSON data from the request
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 404

    user_id = data.get("user_id")
    machine_id = data.get("machine_id")

    if not user_id or not machine_id:
        return jsonify({"error": "Missing required fields"}), 404

    claim_response, status = claim(user_id, machine_id)

    return jsonify(claim_response), status


@app.route("/logs/access", methods=["GET"])
def access_logs():
    """Fetch and return access log content as plain text."""
    try:
        with open("logs/access.log", "r") as f:
            content = f.read()
        return Response(content, mimetype="text/plain")
    except FileNotFoundError:
        return Response("access.log not found", status=404, mimetype="text/plain")


@app.route("/logs/error", methods=["GET"])
def error_logs():
    """Fetch and return error log content as plain text."""
    try:
        with open("logs/error.log", "r") as f:
            content = f.read()
        return Response(content, mimetype="text/plain")
    except FileNotFoundError:
        return Response("error.log not found", status=404, mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
