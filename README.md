# IoT Server Room Monitoring System

Complete server room monitoring system using ESP32, Arduino UNO, Raspberry Pi, MQTT, REST API, and real-time web dashboard.

## Deployed Sensors

- **🌡️ ESP32 + DHT11**: Temperature and humidity
- **💡 Arduino UNO + Photoresistor**: Light intensity
- **📏 Arduino UNO + HC-SR04**: Ultrasonic distance
- **🚨 Alarm System**: Remote control

## System Architecture

```
ESP32/Arduino (sensors)
    ↓
MQTT Broker (Mosquitto/Raspberry Pi)
    ↓
mqtt_logger.py (Python service)
    ↓
MariaDB
    ↓
REST API (Flask)
    ↓
Web Dashboard (Flask)
```

## Project Structure

- `mqtt_logger/` - MQTT logging service to database
- `api_rest/` - Flask API endpoints
- `dashboard/` - Flask dashboard + web interface

## Hardware Configuration

- ESP32 + DHT11 (temperature/humidity)
- Arduino UNO + LDR (light) + HC-SR04 (distance)

## Installation

1. Prepare Raspberry Pi (update, install MariaDB, Mosquitto, Python3-pip)
2. Configure MariaDB (database, user, tables)
3. Configure Mosquitto (authentication, ACL)
4. Install Python dependencies: `pip install -r requirements.txt`
5. Flash ESP32/Arduino firmwares with network/MQTT parameters

## Getting Started

1. Start MQTT broker and MariaDB on Raspberry Pi
2. Run `mqtt_logger.py` service
3. Launch Flask API (`api.py`)
4. Launch web dashboard (`app.py`)
5. Access web interface to view real-time data

## REST API Endpoints

- `GET /api/temperature` - Latest temperature
- `GET /api/humidity` - Latest humidity
- `GET /api/light` - Latest light level
- `GET /api/distance` - Latest distance
- `POST /api/alarm` - Control alarm

## Technologies

- Python 3 (Flask, paho-mqtt, pymysql)
- MariaDB
- Mosquitto MQTT
- ESP32 (Arduino IDE)
- Arduino UNO
- HTML/CSS
