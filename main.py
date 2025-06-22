import asyncio
import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import socketio
import threading
import paho.mqtt.client as mqtt

# === Load env vars ===
load_dotenv()

# === Wrapper Socket.IO and FastAPI ===
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# === Frontend ===
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# === MQTT Config ===
BROKER = os.getenv("HIVEMQ_BROKER")
PORT = 8883
USERNAME = os.getenv("HIVEMQ_SUBSCRIBER_USERNAME")
PASSWORD = os.getenv("HIVEMQ_SUBSCRIBER_PASSWORD")

TOPIC_UPDATE = "bike/gps/update"

state = {"lat": -22.2572774, "lon": -45.6963601, "status": "safe"}

loop = asyncio.get_event_loop()


# === MQTT Callbacks ===
def on_connect(client, userdata, flags, reasonCode, properties):
    print("Connected to MQTT")
    client.subscribe(TOPIC_UPDATE)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        state["lat"] = payload.get("lat", state["lat"])
        state["lon"] = payload.get("lon", state["lon"])
        state["status"] = payload.get("status", state["status"])

        print(f"[MQTT] Received: {payload}")

        asyncio.run_coroutine_threadsafe(
            sio.emit("location_update", state),
            loop,
        )

    except Exception as e:
        print(f"Error processing MQTT message: {e}")


def mqtt_thread():
    client = mqtt.Client(client_id="BikeSubscriber", protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    client.on_message = on_message

    client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
    client.username_pw_set(USERNAME, PASSWORD)

    client.connect(BROKER, PORT, 60)
    client.loop_forever()


# === Start MQTT Thread ===
threading.Thread(target=mqtt_thread, daemon=True).start()


# === FastAPI Routes ===
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
