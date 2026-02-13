# IoT Server Room Monitoring System

Complete server room monitoring system using ESP32, Arduino UNO, Raspberry Pi, MQTT, REST API, and real-time web dashboard.

## 📋 Overview

This project implements a comprehensive monitoring solution for server rooms with real-time data collection, storage, and visualization.

## 🔌 Hardware & Sensors

| Component             | Purpose                           |
| --------------------- | --------------------------------- |
| ESP32 + DHT11         | Temperature & humidity monitoring |
| Arduino UNO + LDR     | Light intensity detection         |
| Arduino UNO + HC-SR04 | Ultrasonic distance measurement   |
| Raspberry Pi          | MQTT broker & database host       |

## 🏗️ System Architecture

```
Sensors (ESP32/Arduino)
    ↓
MQTT Broker (Mosquitto)
    ↓
mqtt_logger.py (Python service)
    ↓
MariaDB
    ↓
REST API (Flask)
    ↓
Web Dashboard
```

## 📁 Project Structure

```
.
├── mqtt_logger/      # MQTT logging service
├── api_rest/         # Flask REST API
├── dashboard/        # Web dashboard interface
└── README.md
```

## 📡 MQTT Topics

- `sensors/esp32/temperature` - Temperature readings
- `sensors/esp32/humidity` - Humidity readings
- `sensors/arduino/light` - Light intensity
- `sensors/arduino/distance` - Distance measurements
- `control/alarm` - Alarm control commands

## 🔌 REST API Endpoints

- `GET /api/temperature` - Latest temperature
- `GET /api/humidity` - Latest humidity
- `GET /api/light` - Latest light level
- `GET /api/distance` - Latest distance
- `POST /api/alarm` - Control alarm

## 🛠️ Installation

1. Update Raspberry Pi and install dependencies
2. Configure MariaDB with database and tables
3. Set up Mosquitto broker with authentication
4. Install Python dependencies: `pip install -r requirements.txt`
5. Flash ESP32/Arduino with network configuration

## 🚀 Getting Started

1. Start MQTT broker and MariaDB
2. Run `mqtt_logger.py`
3. Launch Flask API: `python api.py`
4. Launch dashboard: `python app.py`
5. Access dashboard and view real-time data

## 🔐 Authentication

- Token-based API authentication
- MQTT broker credentials (username/password)
- Flask session management

## 📚 Technologies

- Python 3 (Flask, paho-mqtt, pymysql)
- MariaDB
- Mosquitto MQTT
- ESP32 (Arduino IDE)
- Arduino UNO
- HTML/CSS/JavaScript

## ✨ Features

- Real-time data streaming via MQTT
- Historical data storage and retrieval
- REST API with token authentication
- Interactive web dashboard with charts
- Remote alarm control system
- Responsive web interface
