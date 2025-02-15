from flask import Flask, jsonify, Response
import json

app = Flask(__name__)


def load_data():
    """Load data from JSON file."""
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "data.json not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format in data.json"}


@app.route("/", methods=["GET"])
def get_data():
    """Fetch and return data.json content."""
    data = load_data()
    return jsonify(data)


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
