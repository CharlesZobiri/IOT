#!/usr/bin/env python3
"""
Détection de mouvement avec Pi Camera v1 (ov5647)
Publie sur MQTT et sauvegarde photos
"""

import cv2
import time
import os
from datetime import datetime
import paho.mqtt.publish as publish
from picamera2 import Picamera2

# ======== CONFIGURATION MQTT ========
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USER = "admin"
MQTT_PASS = "adminpass"
MQTT_TOPIC = "server-room/motion"

# ======== CONFIGURATION DETECTION ========
DELAY_BETWEEN_PHOTOS = 5      # secondes entre photos
DELAY_BETWEEN_MQTT = 2        # secondes entre publications MQTT
MOTION_THRESHOLD = 50000      # sensibilité (plus petit = plus sensible)

# ======== DOSSIER PHOTOS ========
PHOTO_DIR = "/home/dev/IOT/camera_motion/photos"
os.makedirs(PHOTO_DIR, exist_ok=True)

# ======== INITIALISATION CAMERA ========
print("=" * 60)
print("🎥 Initialisation Pi Camera v1 (ov5647)")
print("=" * 60)

picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
picam2.configure(config)
picam2.start()
time.sleep(2)  # Chauffe caméra

print("✅ Caméra prête")
print(f"📁 Photos → {PHOTO_DIR}")
print(f"🔔 Seuil détection: {MOTION_THRESHOLD}")
print(f"📡 MQTT: {MQTT_BROKER} → {MQTT_TOPIC}")
print("=" * 60)

# Variables
last_frame = None
last_photo_time = 0
last_mqtt_time = 0
photo_count = 0

try:
    while True:
        # Capture image
        frame = picam2.capture_array()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if last_frame is None:
            last_frame = gray
            continue

        # Différence entre frames
        frame_diff = cv2.absdiff(last_frame, gray)
        thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Calcul zone de mouvement
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        max_contour_area = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > max_contour_area:
                max_contour_area = area
            if area > MOTION_THRESHOLD:
                motion_detected = True

        current_time = time.time()

        # Si mouvement détecté
        if motion_detected:
            
            # 📸 Prendre photo (avec délai minimum)
            if (current_time - last_photo_time) > DELAY_BETWEEN_PHOTOS:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{PHOTO_DIR}/motion_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 Photo: motion_{timestamp}.jpg (aire={max_contour_area:.0f})")
                photo_count += 1
                last_photo_time = current_time

            # 📡 Publier sur MQTT (avec délai minimum)
            if (current_time - last_mqtt_time) > DELAY_BETWEEN_MQTT:
                try:
                    publish.single(
                        MQTT_TOPIC,
                        payload="1",
                        hostname=MQTT_BROKER,
                        port=MQTT_PORT,
                        auth={'username': MQTT_USER, 'password': MQTT_PASS}
                    )
                    print(f"📡 MQTT: {MQTT_TOPIC} = 1")
                    last_mqtt_time = current_time
                except Exception as e:
                    print(f"❌ Erreur MQTT: {e}")

        last_frame = gray
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n" + "=" * 60)
    print("🛑 Arrêt détection mouvement")
    print(f"📊 Total photos prises: {photo_count}")
    print("=" * 60)
    picam2.stop()
except Exception as e:
    print(f"❌ Erreur: {e}")
    picam2.stop()