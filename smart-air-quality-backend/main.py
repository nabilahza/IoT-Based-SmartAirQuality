import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import paho.mqtt.client as mqtt
import firebase_admin
from firebase_admin import credentials, firestore

# =========================================================
# FIRESTORE INITIALIZATION
# =========================================================
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred)
db = firestore.client()

# =========================================================
# MQTT CONFIGURATION
# =========================================================
MQTT_BROKER = "34.10.35.179"
MQTT_PORT = 8883
MQTT_TOPIC = "airquality/room1"
MQTT_USER = "mqttsubscriber01"
MQTT_PASS = "mqttsubscriberpassword"
CA_CERT_PATH = "ca.crt"

# =========================================================
# MQTT CALLBACKS
# =========================================================
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT, rc =", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print("MQTT ", payload)

    try:
        data = json.loads(payload)

        doc = {
            "sensor_id": data.get("sensor_id"),
            "gas": data.get("gas"),
            "level": data.get("level"),
            "fan": data.get("fan"),
            "led": data.get("led"),
            "timestamp": firestore.SERVER_TIMESTAMP
        }

        db.collection("air_quality").add(doc)
        print("Written to Firestore")

    except Exception as e:
        print("Error processing message:", e)

# =========================================================
# START MQTT CLIENT
# =========================================================
def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)

    client.tls_set(ca_certs=CA_CERT_PATH)
    client.tls_insecure_set(True)  # OK for self-signed cert

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

# =========================================================
# HTTP SERVER (REQUIRED BY CLOUD RUN)
# =========================================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"MQTT subscriber running")

def start_http():
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    server.serve_forever()

# =========================================================
# MAIN ENTRY POINT
# =========================================================
if __name__ == "__main__":
    # Start MQTT in background thread
    threading.Thread(target=start_mqtt, daemon=True).start()

    # Start HTTP server (blocks forever)
    start_http()
