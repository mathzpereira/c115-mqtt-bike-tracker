import os
import paho.mqtt.client as mqtt
import random
import math
import time
from dotenv import load_dotenv

load_dotenv()

BROKER = os.getenv("HIVEMQ_BROKER")
PORT = 8883

USERNAME = os.getenv("HIVEMQ_PUBLISHER_USERNAME")
PASSWORD = os.getenv("HIVEMQ_PUBLISHER_PASSWORD")

TOPIC_LAT = "bike/gps/lat"
TOPIC_LON = "bike/gps/lon"
TOPIC_STATUS = "bike/status"

lat_ref = -22.2572774
lon_ref = -45.6963601
safe_radius_km = 0.5

lat = lat_ref
lon = lon_ref

client = mqtt.Client(client_id="BikePublisher", userdata=None, protocol=mqtt.MQTTv5)
client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
client.username_pw_set(USERNAME, PASSWORD)
client.connect(BROKER, PORT)
client.loop_start()


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return R * c


try:
    while True:
        lat += random.uniform(-0.0005, 0.0005)
        lon += random.uniform(-0.0005, 0.0005)

        distance = haversine(lat, lon, lat_ref, lon_ref)
        status = "safe" if distance <= safe_radius_km else "out_of_zone"

        client.publish(TOPIC_LAT, lat)
        client.publish(TOPIC_LON, lon)
        client.publish(TOPIC_STATUS, status)

        print(f"Publicando -> LAT: {lat}, LON: {lon}, STATUS: {status}")

        time.sleep(3)

except KeyboardInterrupt:
    print("Encerrando publisher...")
    client.loop_stop()
    client.disconnect()
