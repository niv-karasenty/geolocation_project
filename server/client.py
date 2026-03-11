import json
import urllib.request
import urllib.error
import time

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SERVER_URL = "http://172.20.10.7:5005/data"   # change IP if client is remote
TIMEOUT    = 3    # seconds before giving up on a request

# ---------------------------------------------------------------------------
# Core send function
# ---------------------------------------------------------------------------

def send_aoa(rx_id, aoa_deg):
    """
    Send one AoA measurement to the server.

    The server does not send meaningful data back; this is fire-and-forget.
    Any connection error is printed but not re-raised so your measurement
    loop keeps running even if the network blips.

    Parameters
    ----------
    rx_id   : str    "RX1" or "RX2"
    aoa_deg : float  measured angle-of-arrival (degrees, CCW from East)
    """
    data    = {"rx_id": rx_id, "aoa_deg": float(aoa_deg)}
    payload = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        SERVER_URL,
        data    = payload,
        headers = {"Content-Type": "application/json"},
        method  = "POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            # Read and discard response -- server just says {"status": "ok"}.
            response.read()
        print(f"[client] Sent {rx_id}  aoa={aoa_deg:.2f} deg  -> ok")

    except urllib.error.URLError as e:
        print(f"[client] Connection error ({rx_id}): {e.reason}")
        print( "[client] Is server.py running?")
    except Exception as e:
        print(f"[client] Unexpected error ({rx_id}): {e}")


# ---------------------------------------------------------------------------
# Demo: simulate two receivers sending readings at short intervals
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Simulated sequence of (RX1_aoa, RX2_aoa) readings.
    # Replace with real measurements from your hardware.
    readings = [
        (45.0, 120.0),
        (50.0, 115.0),
        (48.0, 118.0),
    ]

    print(f"[client] Sending {len(readings)} readings to {SERVER_URL}")
    print( "[client] Make sure server.py is running first.\n")

    for i, (aoa1, aoa2) in enumerate(readings):
        print(f"-- Reading {i + 1} --")
        send_aoa("RX1", aoa1)
        send_aoa("RX2", aoa2)
        time.sleep(1.5)   # short interval so dashboard animates nicely

    print("\n[client] Done.")