#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import pymysql
import time

# Configuration DB
DB_HOST = "localhost"
DB_USER = "apiuser"
DB_PASS = "apipass"
DB_NAME = "serverroom"

# Configuration MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USER = "logger"
MQTT_PASS = "logpass"

def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        client.subscribe("server-room/#")
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    
    # Extraire le type de capteur du topic
    sensor_type = topic.split("/")[-1]
    
    # Ne logger que les capteurs valides
    if sensor_type in ['temperature', 'light', 'motion', 'humidity', 'distance']:
        try:
            value = float(payload)
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sensor_data (sensor_type, value) VALUES (%s, %s)",
                (sensor_type, value)
            )
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Logged: {topic} = {value}")
        except Exception as e:
            print(f"Error logging {topic}: {e}")

# Créer le client MQTT
client = mqtt.Client(client_id="mqtt-logger")
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.on_connect = on_connect
client.on_message = on_message

# Connexion au broker
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
