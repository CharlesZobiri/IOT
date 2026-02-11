#!/usr/bin/env python3
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import pymysql
import paho.mqtt.publish as publish

app = Flask(__name__)
CORS(app)

# Configuration DB
DB_HOST = "localhost"
DB_USER = "apiuser"
DB_PASS = "apipass"
DB_NAME = "serverroom"

# Configuration MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USER = "dashboard"
MQTT_PASS = "dashpass"

def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

# ========== DASHBOARD WEB ==========
@app.route('/')
def index():
    return render_template('index.html')

# ========== API ENDPOINTS ==========
@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    conn = get_db()
    cursor = conn.cursor()
    
    result = {}
    for sensor in ['temperature', 'humidity', 'light', 'distance', 'motion']:
        cursor.execute(
            "SELECT value, timestamp FROM sensor_data WHERE sensor_type=%s ORDER BY timestamp DESC LIMIT 1",
            (sensor,)
        )
        row = cursor.fetchone()
        result[sensor] = row if row else None
    
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/api/alarm', methods=['POST'])
def alarm_control():
    data = request.get_json()
    state = data.get('state', 'OFF')
    
    try:
        publish.single(
            "server-room/alarm/cmd",
            payload=state,
            hostname=MQTT_BROKER,
            port=MQTT_PORT,
            auth={'username': MQTT_USER, 'password': MQTT_PASS}
        )
        return jsonify({"status": "ok", "alarm": state})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/buzzer', methods=['POST'])
def buzzer_control():
    data = request.get_json()
    state = data.get('state', 'OFF')
    
    try:
        publish.single(
            "server-room/buzzer/cmd",
            payload=state,
            hostname=MQTT_BROKER,
            port=MQTT_PORT,
            auth={'username': MQTT_USER, 'password': MQTT_PASS}
        )
        return jsonify({"status": "ok", "buzzer": state})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/history/<sensor>', methods=['GET'])
def history(sensor):
    limit = request.args.get('limit', 100, type=int)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT value, timestamp FROM sensor_data WHERE sensor_type=%s ORDER BY timestamp DESC LIMIT %s",
        (sensor, limit)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(rows)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
