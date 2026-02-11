#!/usr/bin/env python3
"""
Contrôleur intelligent du buzzer
Analyse les données des capteurs et active le buzzer selon des règles
"""

import paho.mqtt.client as mqtt
import pymysql
import time

# Configuration MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USER = "admin"
MQTT_PASS = "adminpass"

# Configuration DB
DB_HOST = "localhost"
DB_USER = "apiuser"
DB_PASS = "apipass"
DB_NAME = "serverroom"

# Seuils d'alerte
TEMP_MAX = 30.0      # °C
HUMIDITY_MAX = 70.0  # %
DISTANCE_MIN = 50.0  # cm
LIGHT_MIN = 100      # lux (trop sombre)

# État du buzzer
buzzer_active = False
last_buzzer_time = 0
BUZZER_COOLDOWN = 30  # Éviter spam, 30 secondes minimum entre activations

def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def get_last_sensor_value(sensor_type):
    """Récupère la dernière valeur d'un capteur"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT value FROM sensor_data WHERE sensor_type=%s ORDER BY timestamp DESC LIMIT 1",
        (sensor_type,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row['value'] if row else None

def check_alerts():
    """Vérifie si des alertes doivent déclencher le buzzer"""
    alerts = []
    
    # Température
    temp = get_last_sensor_value('temperature')
    if temp and temp > TEMP_MAX:
        alerts.append(f"🌡️ Température élevée: {temp}°C")
    
    # Humidité
    humidity = get_last_sensor_value('humidity')
    if humidity and humidity > HUMIDITY_MAX:
        alerts.append(f"💧 Humidité élevée: {humidity}%")
    
    # Distance
    distance = get_last_sensor_value('distance')
    if distance and 0 < distance < DISTANCE_MIN:
        alerts.append(f"📏 Objet détecté: {distance}cm")
    
    # Luminosité
    light = get_last_sensor_value('light')
    if light and light < LIGHT_MIN:
        alerts.append(f"💡 Trop sombre: {light} lux")
    
    return alerts

def control_buzzer(state, reason=""):
    """Envoie commande MQTT pour contrôler le buzzer"""
    global buzzer_active, last_buzzer_time
    
    current_time = time.time()
    
    # Éviter spam
    if state == "ON" and (current_time - last_buzzer_time) < BUZZER_COOLDOWN:
        return
    
    try:
        import paho.mqtt.publish as publish
        publish.single(
            "server-room/buzzer/cmd",
            payload=state,
            hostname=MQTT_BROKER,
            port=MQTT_PORT,
            auth={'username': MQTT_USER, 'password': MQTT_PASS}
        )
        buzzer_active = (state == "ON")
        last_buzzer_time = current_time
        
        if state == "ON":
            print(f"🚨 BUZZER ACTIVÉ: {reason}")
        else:
            print(f"✅ BUZZER DÉSACTIVÉ")
            
    except Exception as e:
        print(f"❌ Erreur MQTT: {e}")

def main():
    print("🤖 Contrôleur de buzzer démarré")
    print(f"Seuils: Temp>{TEMP_MAX}°C, Humidity>{HUMIDITY_MAX}%, Distance<{DISTANCE_MIN}cm, Light<{LIGHT_MIN}lux")
    
    while True:
        try:
            alerts = check_alerts()
            
            if alerts:
                # Des alertes détectées → activer buzzer
                reason = " | ".join(alerts)
                if not buzzer_active:
                    control_buzzer("ON", reason)
                else:
                    print(f"⚠️ Alertes actives: {reason}")
            else:
                # Pas d'alerte → désactiver buzzer
                if buzzer_active:
                    control_buzzer("OFF")
            
            time.sleep(5)  # Vérifier toutes les 5 secondes
            
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du contrôleur")
            control_buzzer("OFF")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
