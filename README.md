# README - Système de Monitoring IoT Server Room

## 📋 Vue d'ensemble

Système complet de monitoring de salle serveur utilisant ESP32, Arduino UNO, Raspberry Pi, MQTT, API REST et Dashboard web temps réel.

**Capteurs déployés :**
- 🌡️ **ESP32 + DHT11** : Température et humidité
- 💡 **Arduino UNO + Photorésistance** : Luminosité
- 📏 **Arduino UNO + HC-SR04** : Distance ultrason
- 🚨 **Système d'alarme** : Contrôle à distance

***

## 🏗️ Architecture du système

```
┌─────────────┐      ┌─────────────┐
│   ESP32     │      │ Arduino UNO │
│  DHT11      │      │ LDR + HCSR04│
└──────┬──────┘      └──────┬──────┘
       │ MQTT               │ MQTT
       │ Publish            │ Publish
       └────────┬───────────┘
                │
         ┌──────▼──────┐
         │  MQTT Broker│
         │  Mosquitto  │
         │ Raspberry Pi│
         └──────┬──────┘
                │ Subscribe
         ┌──────▼──────────┐
         │  mqtt_logger.py │
         │  (Service)      │
         └──────┬──────────┘
                │
         ┌──────▼──────┐
         │   MariaDB   │
         │  serverroom │
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │   API REST  │
         │  Flask:5000 │
         └──────┬──────┘
                │
         ┌──────▼──────┐
         │  Dashboard  │
         │   Web UI    │
         └─────────────┘
```

***

## 📁 Structure des dossiers

```
/home/dev/
├── mqtt_logger/
│   ├── mqtt_logger.py          # Service d'enregistrement MQTT → DB
│   └── requirements.txt        # paho-mqtt, pymysql
│
├── api_rest/
│   ├── api.py                  # API Flask endpoints
│   └── requirements.txt        # flask, pymysql, flask-cors
│
└── dashboard/
    ├── app.py                  # Application Flask dashboard
    ├── templates/
    │   └── index.html          # Interface web
    └── requirements.txt        # flask
```

***

## 🔧 Configuration Matérielle

### ESP32 + DHT11
```
DHT11          ESP32
-----          -----
VCC   -------> 3.3V
GND   -------> GND
DATA  -------> GPIO 4
```

### Arduino UNO + LDR + HC-SR04
```
LDR (Photorésistance)     Arduino UNO
---------------------     -----------
Broche 1 -------> 5V
Broche 2 -------> A0 + Résistance 10kΩ → GND

HC-SR04        Arduino UNO
-------        -----------
VCC   -------> 5V
GND   -------> GND
TRIG  -------> Pin 2 (D2)
ECHO  -------> Pin 3 (D3)
```

***

## 🔐 Credentials et Configuration

### Réseau WiFi
```cpp
const char* ssid = "b3Mh8KqZ";
const char* password = "9CgN7p4D";
```

### MQTT Broker (Mosquitto)
- **IP Broker :** `10.160.24.188`
- **Port :** `1883`

#### Utilisateurs MQTT

| Utilisateur | Mot de passe | Rôle |
|------------|--------------|------|
| `admin` | `adminpass` | Lecture/écriture partout |
| `esp32` | `esp32pass` | Publie température/humidité, lit commandes alarme |
| `arduino` | `arduinopass` | Publie luminosité/distance |
| `dashboard` | `dashpass` | Lit tous les topics, écrit commandes |
| `logger` | `logpass` | Enregistre messages en DB |

### Base de données MariaDB
```bash
Nom DB: serverroom
Utilisateur: apiuser
Mot de passe: apipass
Host: localhost
Port: 3306
```

### Topics MQTT

| Topic | Publisher | Subscriber | Description |
|-------|-----------|------------|-------------|
| `server-room/temperature` | ESP32 | logger, dashboard | Température °C |
| `server-room/humidity` | ESP32 | logger, dashboard | Humidité % |
| `server-room/light` | Arduino | logger, dashboard | Luminosité lux |
| `server-room/distance` | Arduino | logger, dashboard | Distance cm |
| `server-room/alarm/cmd` | Dashboard | ESP32, Arduino | Commande alarme ON/OFF |
| `server-room/camera/cmd` | Dashboard | (futur) | Commande caméra |

***

## 💾 Installation Complète

### 1. Raspberry Pi - Configuration initiale

```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances
sudo apt install -y mariadb-server mosquitto mosquitto-clients python3-pip
```

### 2. Configuration MariaDB

```bash
# Connexion MySQL
sudo mysql -u root

# Créer la base de données
CREATE DATABASE serverroom;
CREATE USER 'apiuser'@'localhost' IDENTIFIED BY 'apipass';
GRANT ALL PRIVILEGES ON serverroom.* TO 'apiuser'@'localhost';
FLUSH PRIVILEGES;
USE serverroom;

# Créer la table
CREATE TABLE sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_type VARCHAR(50),
    value FLOAT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

EXIT;
```

### 3. Configuration Mosquitto

```bash
# Configuration authentification
sudo nano /etc/mosquitto/mosquitto.conf
```

**Contenu :**
```conf
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
acl_file /etc/mosquitto/acl
```

**Créer les utilisateurs :**
```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd admin
# Entrer: adminpass

sudo mosquitto_passwd -b /etc/mosquitto/passwd esp32 esp32pass
sudo mosquitto_passwd -b /etc/mosquitto/passwd arduino arduinopass
sudo mosquitto_passwd -b /etc/mosquitto/passwd dashboard dashpass
sudo mosquitto_passwd -b /etc/mosquitto/passwd logger logpass
```

**Créer l'ACL :**
```bash
sudo nano /etc/mosquitto/acl
```

**Contenu :**
```conf
# Admin = lecture/écriture partout
user admin
topic readwrite #

# ESP32 = DHT11 (température + humidité) + commandes alarme
user esp32
topic read server-room/alarm/cmd
topic write server-room/temperature
topic write server-room/humidity

# Arduino = luminosité + distance + commandes alarme
user arduino
topic read server-room/alarm/cmd
topic write server-room/light
topic write server-room/distance

# Dashboard = lit tout, écrit commandes
user dashboard
topic read server-room/#
topic write server-room/alarm/cmd
topic write server-room/camera/cmd

# Logger = lit tout
user logger
topic read server-room/#
```

**Redémarrer Mosquitto :**
```bash
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto
```

### 4. Installation mqtt_logger

```bash
# Créer le dossier
mkdir -p ~/mqtt_logger
cd ~/mqtt_logger

# Créer requirements.txt
cat > requirements.txt << EOF
paho-mqtt
pymysql
EOF

# Installer les dépendances
pip3 install -r requirements.txt

# Créer mqtt_logger.py
nano mqtt_logger.py
```

**Contenu mqtt_logger.py :**
```python
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
```

**Rendre exécutable :**
```bash
chmod +x mqtt_logger.py
```

**Créer le service systemd :**
```bash
sudo nano /etc/systemd/system/mqtt-logger.service
```

**Contenu :**
```ini
[Unit]
Description=MQTT to MariaDB Logger
After=network.target mosquitto.service mariadb.service

[Service]
Type=simple
User=dev
WorkingDirectory=/home/dev/mqtt_logger
ExecStart=/usr/bin/python3 /home/dev/mqtt_logger/mqtt_logger.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Activer le service :**
```bash
sudo systemctl daemon-reload
sudo systemctl enable mqtt-logger
sudo systemctl start mqtt-logger
sudo systemctl status mqtt-logger
```

### 5. Installation API REST

```bash
# Créer le dossier
mkdir -p ~/api_rest
cd ~/api_rest

# Créer requirements.txt
cat > requirements.txt << EOF
flask
pymysql
flask-cors
EOF

# Installer les dépendances
pip3 install -r requirements.txt

# Créer api.py
nano api.py
```

**Contenu api.py :**
```python
#!/usr/bin/env python3
from flask import Flask, jsonify, request
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
    
    publish.single(
        "server-room/alarm/cmd",
        payload=state,
        hostname=MQTT_BROKER,
        port=MQTT_PORT,
        auth={'username': MQTT_USER, 'password': MQTT_PASS}
    )
    
    return jsonify({"status": "ok", "alarm": state})

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
```

**Rendre exécutable :**
```bash
chmod +x api.py
```

**Créer le service systemd :**
```bash
sudo nano /etc/systemd/system/api-rest.service
```

**Contenu :**
```ini
[Unit]
Description=Server Room API REST
After=network.target mariadb.service

[Service]
Type=simple
User=dev
WorkingDirectory=/home/dev/api_rest
ExecStart=/usr/bin/python3 /home/dev/api_rest/api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Activer le service :**
```bash
sudo systemctl daemon-reload
sudo systemctl enable api-rest
sudo systemctl start api-rest
sudo systemctl status api-rest
```

### 6. Installation Dashboard

```bash
# Créer la structure
mkdir -p ~/dashboard/templates
cd ~/dashboard

# Créer requirements.txt
cat > requirements.txt << EOF
flask
EOF

pip3 install -r requirements.txt

# Créer app.py
nano app.py
```

**Contenu app.py :**
```python
#!/usr/bin/env python3
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

**Créer le template HTML :**
```bash
nano templates/index.html
```

**Contenu index.html :**
```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Server Room Monitoring</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            transition: transform 0.3s;
        }
        .card:hover { transform: translateY(-5px); }
        .card-icon {
            font-size: 3em;
            text-align: center;
            margin-bottom: 15px;
        }
        .card-title {
            font-size: 1.2em;
            color: #333;
            text-align: center;
            margin-bottom: 10px;
            font-weight: bold;
        }
        .card-value {
            font-size: 2.5em;
            color: #667eea;
            text-align: center;
            font-weight: bold;
        }
        .card-unit {
            font-size: 0.8em;
            color: #666;
            text-align: center;
            margin-top: 5px;
        }
        .controls {
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        .btn {
            padding: 15px 30px;
            font-size: 1.1em;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            font-weight: bold;
        }
        .btn-alarm {
            background: #e74c3c;
            color: white;
        }
        .btn-alarm.active {
            background: #27ae60;
        }
        .btn:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        }
        .timestamp {
            color: white;
            text-align: center;
            margin-top: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖥️ Server Room Monitoring</h1>
        
        <div class="grid">
            <div class="card">
                <div class="card-icon">🌡️</div>
                <div class="card-title">Température</div>
                <div class="card-value" id="temp">--</div>
                <div class="card-unit">°C</div>
            </div>
            
            <div class="card">
                <div class="card-icon">💧</div>
                <div class="card-title">Humidité</div>
                <div class="card-value" id="humidity">--</div>
                <div class="card-unit">%</div>
            </div>
            
            <div class="card">
                <div class="card-icon">💡</div>
                <div class="card-title">Luminosité</div>
                <div class="card-value" id="light">--</div>
                <div class="card-unit">lux</div>
            </div>
            
            <div class="card">
                <div class="card-icon">📏</div>
                <div class="card-title">Distance</div>
                <div class="card-value" id="distance">--</div>
                <div class="card-unit">cm</div>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn btn-alarm" id="alarmBtn" onclick="toggleAlarm()">
                🚨 Alarme OFF
            </button>
        </div>
        
        <div class="timestamp">
            Dernière mise à jour : <span id="lastUpdate">--</span>
        </div>
    </div>

    <script>
        let alarmState = false;

        function updateData() {
            fetch('http://10.160.24.188:5000/api/dashboard')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('temp').textContent = 
                        data.temperature ? data.temperature.value.toFixed(1) : '--';
                    
                    document.getElementById('humidity').textContent = 
                        data.humidity ? data.humidity.value.toFixed(1) : '--';
                    
                    document.getElementById('light').textContent = 
                        data.light ? Math.round(data.light.value) : '--';
                    
                    document.getElementById('distance').textContent = 
                        data.distance ? data.distance.value.toFixed(1) : '--';
                    
                    document.getElementById('lastUpdate').textContent = 
                        new Date().toLocaleTimeString('fr-FR');
                })
                .catch(error => console.error('Erreur:', error));
        }

        function toggleAlarm() {
            alarmState = !alarmState;
            const btn = document.getElementById('alarmBtn');
            
            fetch('http://10.160.24.188:5000/api/alarm', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({state: alarmState ? 'ON' : 'OFF'})
            })
            .then(response => response.json())
            .then(data => {
                if (alarmState) {
                    btn.classList.add('active');
                    btn.textContent = '🚨 Alarme ON';
                } else {
                    btn.classList.remove('active');
                    btn.textContent = '🚨 Alarme OFF';
                }
            })
            .catch(error => console.error('Erreur:', error));
        }

        // Mise à jour automatique toutes les 5 secondes
        updateData();
        setInterval(updateData, 5000);
    </script>
</body>
</html>
```

**Note :** Le dashboard utilise l'API REST, donc **ne pas** créer de service systemd pour `app.py`. L'API REST (`api.py`) sert à la fois l'API et le dashboard sur le port 5000.

***

## 📟 Code ESP32

**Fichier : `esp32_serverroom.ino`**

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

// WiFi
const char* ssid = "b3Mh8KqZ";
const char* password = "9CgN7p4D";

// MQTT
const char* mqtt_server = "10.160.24.188";
const int mqtt_port = 1883;
const char* mqtt_user = "esp32";
const char* mqtt_password = "esp32pass";

// DHT11
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  Serial.print("Connexion WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connecté");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message recu [");
  Serial.print(topic);
  Serial.print("]: ");
  
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
  
  if (String(topic) == "server-room/alarm/cmd") {
    if (message == "ON") {
      Serial.println("ALARME ACTIVEE");
      // Ajouter code LED/Buzzer
    } else {
      Serial.println("ALARME DESACTIVEE");
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Connexion MQTT...");
    if (client.connect("ESP32Client", mqtt_user, mqtt_password)) {
      Serial.println("connecté");
      client.subscribe("server-room/alarm/cmd");
    } else {
      Serial.print("Echec, rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Lecture DHT11
  float temp = dht.readTemperature();
  float hum = dht.readHumidity();

  if (!isnan(temp) && !isnan(hum)) {
    // Température
    char tempStr [docs.aws.amazon](https://docs.aws.amazon.com/iot/latest/developerguide/iot-dc-testconn-provision.html);
    dtostrf(temp, 4, 2, tempStr);
    client.publish("server-room/temperature", tempStr);
    Serial.print("Temperature publiee: ");
    Serial.println(tempStr);

    // Humidité
    char humStr [docs.aws.amazon](https://docs.aws.amazon.com/iot/latest/developerguide/iot-dc-testconn-provision.html);
    dtostrf(hum, 4, 2, humStr);
    client.publish("server-room/humidity", humStr);
    Serial.print("Humidite publiee: ");
    Serial.println(humStr);
  }

  delay(10000); // 10 secondes
}
```

**Bibliothèques requises (Arduino IDE) :**
- WiFi (incluse)
- PubSubClient by Nick O'Leary
- DHT sensor library by Adafruit

***

## 📟 Code Arduino UNO

**Fichier : `arduino_serverroom.ino`**

```cpp
#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <HCSR04.h>

// WiFi
const char* ssid = "b3Mh8KqZ";
const char* password = "9CgN7p4D";

// MQTT
const char* mqtt_server = "10.160.24.188";
const int mqtt_port = 1883;
const char* mqtt_user = "arduino";
const char* mqtt_password = "arduinopass";

// Pins
const int LDR_PIN = A0;
const int TRIG_PIN = 2;
const int ECHO_PIN = 3;

WiFiClient arduinoClient;
PubSubClient client(arduinoClient);
UltraSonicDistanceSensor distanceSensor(TRIG_PIN, ECHO_PIN);

void setup_wifi() {
  Serial.print("Connexion WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connecté");
  Serial.println(WiFi.localIP());
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message recu [");
  Serial.print(topic);
  Serial.print("]: ");
  
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
  
  if (String(topic) == "server-room/alarm/cmd") {
    if (message == "ON") {
      Serial.println("ALARME ACTIVEE");
    } else {
      Serial.println("ALARME DESACTIVEE");
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Connexion MQTT...");
    if (client.connect("ArduinoClient", mqtt_user, mqtt_password)) {
      Serial.println("connecté");
      client.subscribe("server-room/alarm/cmd");
    } else {
      Serial.print("Echec, rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(9600);
  pinMode(LDR_PIN, INPUT);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // ===== Luminosité =====
  int ldrValue = analogRead(LDR_PIN);
  float lux = map(ldrValue, 0, 1023, 0, 1000);
  
  char luxStr [docs.aws.amazon](https://docs.aws.amazon.com/iot/latest/developerguide/iot-dc-testconn-provision.html);
  dtostrf(lux, 4, 0, luxStr);
  client.publish("server-room/light", luxStr);
  Serial.print("Luminosite publiee: ");
  Serial.println(luxStr);

  // ===== Distance =====
  float distance = distanceSensor.measureDistanceCm();
  
  if (distance > 0 && distance < 400) {
    char distStr [docs.aws.amazon](https://docs.aws.amazon.com/iot/latest/developerguide/iot-dc-testconn-provision.html);
    dtostrf(distance, 4, 2, distStr);
    client.publish("server-room/distance", distStr);
    Serial.print("Distance publiee: ");
    Serial.println(distStr);
  }

  delay(10000); // 10 secondes
}
```

**Bibliothèques requises (Arduino IDE) :**
- WiFiNINA by Arduino
- PubSubClient by Nick O'Leary
- HCSR04 by Martin Sosic

***

## 🚀 Utilisation

### Démarrer tous les services

```bash
sudo systemctl start mosquitto
sudo systemctl start mqtt-logger
sudo systemctl start api-rest
```

### Vérifier les services

```bash
sudo systemctl status mosquitto
sudo systemctl status mqtt-logger
sudo systemctl status api-rest
```

### Accéder au Dashboard

Ouvrir un navigateur :
```
http://10.160.24.188:5000/
```

### Tester l'API

```bash
# Données dashboard
curl http://10.160.24.188:5000/api/dashboard

# Historique température
curl http://10.160.24.188:5000/api/history/temperature?limit=10

# Activer alarme
curl -X POST http://10.160.24.188:5000/api/alarm \
  -H "Content-Type: application/json" \
  -d '{"state":"ON"}'
```

### Écouter les messages MQTT

```bash
mosquitto_sub -h localhost -p 1883 -u dashboard -P "dashpass" -t "server-room/#" -v
```

***

## 🔍 Dépannage

### Voir les logs mqtt_logger

```bash
sudo journalctl -u mqtt-logger -f
```

### Voir les logs API REST

```bash
sudo journalctl -u api-rest -f
```

### Tester la connexion MQTT

```bash
# Publier un message test
mosquitto_pub -h localhost -p 1883 -u admin -P "adminpass" -t "server-room/test" -m "hello"

# S'abonner à tous les topics
mosquitto_sub -h localhost -p 1883 -u admin -P "adminpass" -t "#" -v
```

### Vérifier la base de données

```bash
mysql -u apiuser -p serverroom

# Dans MySQL:
SELECT sensor_type, COUNT(*) as nb FROM sensor_data GROUP BY sensor_type;
SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10;
```

### Redémarrer tous les services

```bash
sudo systemctl restart mosquitto mqtt-logger api-rest
```

***

## 📊 Endpoints API

| Endpoint | Méthode | Description | Exemple réponse |
|----------|---------|-------------|-----------------|
| `/api/dashboard` | GET | Dernières valeurs tous capteurs | `{"temperature": {...}, "humidity": {...}}` |
| `/api/history/<sensor>` | GET | Historique capteur | `[{"value": 28.0, "timestamp": "..."}]` |
| `/api/alarm` | POST | Contrôle alarme | `{"status": "ok", "alarm": "ON"}` |

***

## 🛠️ Maintenance

### Nettoyer les anciennes données (> 7 jours)

```bash
mysql -u apiuser -p serverroom -e "DELETE FROM sensor_data WHERE timestamp < DATE_SUB(NOW(), INTERVAL 7 DAY);"
```

### Sauvegarder la base de données

```bash
mysqldump -u apiuser -p serverroom > backup_serverroom_$(date +%Y%m%d).sql
```

### Restaurer la base de données

```bash
mysql -u apiuser -p serverroom < backup_serverroom_20260211.sql
```

***

## 📝 Notes importantes

1. **Sécurité** : Ce setup est pour un environnement local. Pour une production, utilisez MQTT avec TLS et des mots de passe plus robustes.

2. **Performance** : La DB peut grossir rapidement. Mettre en place un script cron pour nettoyer les anciennes données.

3. **Scalabilité** : Pour plus de capteurs, ajouter simplement :
   - Permissions dans `/etc/mosquitto/acl`
   - Traitement dans `mqtt_logger.py`
   - Affichage dans `index.html`

4. **IP Statique** : Configurer une IP fixe sur le Raspberry Pi pour éviter les changements d'adresse.

***

## 📞 Support

- **Mosquitto logs** : `/var/log/mosquitto/mosquitto.log`
- **Services logs** : `journalctl -u <service-name>`
- **Test connectivité** : `ping 10.160.24.188`

***

**Version :** 1.0  
**Date :** 11 Février 2026  
**Auteur :** Projet IoT Server Room