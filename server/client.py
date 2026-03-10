import json
import urllib.request
import urllib.error

SERVER_URL = "http://10.147.25.23:5005/data"
TIMEOUT = 3  # seconds

def send_to_server(value):
    payload = json.dumps({"value": value}).encode("utf-8")

    req = urllib.request.Request(
        SERVER_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            body = response.read().decode("utf-8")
            result = json.loads(body)
            print(f"[client] Server replied: {result}")
            return result

    except urllib.error.URLError as e:
        print(f"[client] Connection error: {e.reason}")
        print(f"[client] Is server.py running?")
    except json.JSONDecodeError:
        print("[client] Could not decode server response")
    except Exception as e:
        print(f"[client] Unexpected error: {e}")
    return None

if __name__ == "__main__":
    test_values = [0, 5, 42, 150, -3, "on", "off", "hello"]
    send_to_server(test_values[1])