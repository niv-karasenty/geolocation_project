from flask import Flask, request, jsonify
import logging
import threading
import time
from pyproj import Transformer

# matplotlib backend must be set before any other matplotlib import.
# TkAgg opens an interactive window; switch to Qt5Agg if you prefer Qt.
import matplotlib
matplotlib.use("TkAgg")

from dashboard import GeolocationDashboard

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOST = "0.0.0.0"
PORT = 5005

# Hardcoded receiver positions (x, y in metres).
# Treat these as a local Cartesian frame -- or drop in lat/lon values
# directly if your dashboard scale allows it.

def gps_to_xy(gps, lat, lon):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32636", always_xy=True)  # UTM zone example
    # replace latitude and longitude
    x, y = transformer.transform(32.0860, 34.7830)
    return x, y

# replace with relevant lat, lon, gps addresses values
rx1_x, rx1_y = gps_to_xy("", 32, 34)
rx2_x, rx2_y = gps_to_xy("", 32, 34)

RX1_POS = {"x": rx1_x,  "y": rx1_y}
RX2_POS = {"x": rx2_x, "y": rx2_y}

# Half-width of the angular wedge built around each measured AoA.
# e.g. aoa=45 deg + uncertainty=10 -> wedge [35, 55] deg
AOA_UNCERTAINTY_DEG = 10.0

# How often (seconds) the main thread checks for new data and redraws.
UPDATE_INTERVAL = 1.0

# ---------------------------------------------------------------------------
# Shared state (written by Flask thread, read by main thread)
# ---------------------------------------------------------------------------

latest      = {"RX1": None, "RX2": None}   # most recent aoa_deg per receiver
state_lock  = threading.Lock()

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)

def _build_rx(pos, aoa_deg):
    """
    Turn a receiver position + single AoA measurement into the dict
    format that geolocation / dashboard expects.

    Parameters
    ----------
    pos     : dict  {"x": float, "y": float}
    aoa_deg : float  measured angle-of-arrival (degrees, CCW from East)

    Returns
    -------
    dict  {"x", "y", "min_angle", "max_angle"}
    """
    return {
        "x":         pos["x"],
        "y":         pos["y"],
        "min_angle": aoa_deg - AOA_UNCERTAINTY_DEG,
        "max_angle": aoa_deg + AOA_UNCERTAINTY_DEG,
    }


@app.route("/data", methods=["POST"])
def receive_data():
    """
    Accept an AoA reading from one receiver.

    Expected JSON body:
        { "rx_id": "RX1" | "RX2",  "aoa_deg": <float> }

    The client does not need to read the response body.
    """
    if not request.is_json:
        logging.warning("Rejected non-JSON request")
        return jsonify({"status": "error",
                        "message": "Content-Type must be application/json"}), 415

    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"status": "error",
                        "message": "Invalid or empty JSON body"}), 400

    rx_id   = payload.get("rx_id")
    aoa_deg = payload.get("aoa_deg")

    if rx_id not in ("RX1", "RX2"):
        return jsonify({"status": "error",
                        "message": 'rx_id must be "RX1" or "RX2"'}), 400

    if not isinstance(aoa_deg, (int, float)):
        return jsonify({"status": "error",
                        "message": "aoa_deg must be a number"}), 400

    with state_lock:
        latest[rx_id] = float(aoa_deg)

    logging.info(f"Stored {rx_id}  aoa={aoa_deg:.2f} deg")
    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health():
    """Simple liveness probe."""
    return jsonify({"status": "alive"}), 200


# ---------------------------------------------------------------------------
# Dashboard loop (runs on the main thread)
# ---------------------------------------------------------------------------

def dashboard_loop():
    """
    Create the dashboard window and update it every UPDATE_INTERVAL seconds.

    Runs on the main thread so matplotlib's GUI toolkit is happy.
    Reads from `latest` (protected by state_lock) to get the newest
    AoA from each receiver, then calls dash.update().
    """
    dash = GeolocationDashboard()

    logging.info("Dashboard ready -- waiting for data from both receivers...")

    while True:
        with state_lock:
            aoa1 = latest["RX1"]
            aoa2 = latest["RX2"]

        if aoa1 is not None and aoa2 is not None:
            rx1 = _build_rx(RX1_POS, aoa1)
            rx2 = _build_rx(RX2_POS, aoa2)
            try:
                dash.update(rx1, rx2)
            except Exception as exc:
                logging.error(f"Dashboard update failed: {exc}")
        else:
            # Keep the window responsive even while waiting for data.
            try:
                dash.fig.canvas.flush_events()
            except Exception:
                pass

        time.sleep(UPDATE_INTERVAL)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Start Flask in a background daemon thread so it does not block the
    # main thread (which belongs to matplotlib's event loop).
    flask_thread = threading.Thread(
        target=lambda: app.run(host=HOST, port=PORT,
                               debug=False, use_reloader=False),
        daemon=True,   # killed automatically when main thread exits
        name="flask-server",
    )
    flask_thread.start()

    print(f"\n  Server listening on http://{HOST}:{PORT}")
    print(f"  POST AoA data  ->  http://{HOST}:{PORT}/data")
    print(f"  Health check   ->  http://{HOST}:{PORT}/health")
    print(f"\n  RX1 position: ({RX1_POS['x']}, {RX1_POS['y']}) m")
    print(f"  RX2 position: ({RX2_POS['x']}, {RX2_POS['y']}) m")
    print(f"  AoA wedge half-width: ?{AOA_UNCERTAINTY_DEG} deg")
    print(f"  Dashboard refresh interval: {UPDATE_INTERVAL} s\n")

    # Dashboard loop blocks here on the main thread (as required by TkAgg).
    dashboard_loop()