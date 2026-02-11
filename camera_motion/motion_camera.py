import cv2
import time
from picamera2 import Picamera2

# Initialisation caméra
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)})
picam2.configure(config)
picam2.start()

time.sleep(2)  # chauffe caméra

# Variables détection
last_frame = None
last_photo_time = 0
DELAY_BETWEEN_PHOTOS = 5  # secondes
MOTION_THRESHOLD = 50000  # sensibilité mouvement

photo_count = 0

print("Détection de mouvement lancée...")

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
    for contour in contours:
        if cv2.contourArea(contour) > MOTION_THRESHOLD:
            motion_detected = True
            break

    # Si mouvement → prendre photo (avec délai mini 5s)
    current_time = time.time()
    if motion_detected and (current_time - last_photo_time) > DELAY_BETWEEN_PHOTOS:
        filename = f"photo_{photo_count}.jpg"
        cv2.imwrite(filename, frame)
        print(f"📸 Photo prise : {filename}")
        photo_count += 1
        last_photo_time = current_time

    last_frame = gray

    # Petite pause CPU
    time.sleep(0.1)