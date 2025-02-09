from flask import Flask, jsonify
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
