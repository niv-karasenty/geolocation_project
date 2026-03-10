from flask import Flask, request, jsonify
import logging

HOST = "0.0.0.0"
PORT = 5005

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

def process_value(value):
    result = ""
    if isinstance(value, (int, float)):
        if value < 0:
            result = "NEGATIVE signal detected"

    else:
        result = f"Unknown type ({type(value).__name__}): {value}"

    return result


@app.route("/data", methods=["POST"])
def receive_data():
    # ── Validate content type ──
    if not request.is_json:
        logging.warning("Request is not JSON")
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 415

    payload = request.get_json(silent=True)

    if payload is None:
        logging.warning("Could not parse JSON body")
        return jsonify({"status": "error", "message": "Invalid or empty JSON body"}), 400

    # ── Extract parameter ──
    if "value" not in payload:
        logging.warning(f"Missing 'value' key. Got: {payload}")
        return jsonify({"status": "error", "message": "JSON must contain a 'value' key"}), 422

    raw_value = payload["value"]

    result = process_value(raw_value)
    print(f"Incoming value : {raw_value!r}")
    print(f"Output         : {result}")

    logging.info(f"Processed value={raw_value!r} → {result}")

    return jsonify({
        "status": "ok",
        "received": raw_value,
        "result": result
    }), 200

@app.route("/health", methods=["GET"])
def health():
    """Simple health-check endpoint."""
    return jsonify({"status": "alive"}), 200

if __name__ == "__main__":
    print(f"\n Server starting on http://{HOST}:{PORT}")
    print(f"   POST JSON to → http://{HOST}:{PORT}/data")
    print(f"   Health check → http://{HOST}:{PORT}/health\n")
    app.run(host=HOST, port=PORT, debug=False)