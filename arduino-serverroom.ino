// ======== CALLBACK MQTT ========
void callback(char* topic, byte* payload, unsigned int length) {
  String msg="";
  for (int i=0;i<length;i++) msg+=(char)payload[i];

  Serial.print("Message recu [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(msg);

  // 🔔 COMMANDE BUZZER DIRECT
  if (String(topic) == "server-room/buzzer/cmd") {
    if (msg == "ON") {
      tone(BUZZER_PIN, 2000);
      Serial.println("🚨 BUZZER ACTIVE");
    }
    else if (msg == "OFF") {
      noTone(BUZZER_PIN);
      Serial.println("✅ BUZZER DESACTIVE");
    }
  }

  // 🔔 COMMANDE ALARME DISTANCE (ancienne logique)
  if (String(topic) == "server-room/alarm/cmd") {
    if (msg == "ON") {
      alarmeActive = true;
      Serial.println("✅ ALARME DISTANCE ACTIVEE");
    }
    else if (msg == "OFF") {
      alarmeActive = false;
      noTone(BUZZER_PIN);
      Serial.println("❌ ALARME DISTANCE DESACTIVEE");
    }
  }
}

// ======== RECONNEXION MQTT ========
void reconnect_mqtt() {
  while (!client.connected()) {
    Serial.print("Connexion MQTT...");
    if (client.connect("Arduino-IOT", mqtt_user, mqtt_pass)) {
      Serial.println("OK");
      client.subscribe("server-room/alarm/cmd");
      client.subscribe("server-room/buzzer/cmd");  // ← NOUVEAU
    } else {
      Serial.print("Erreur rc=");
      Serial.print(client.state());
      Serial.println(" retry 5s");
      delay(5000);
    }
  }
}

// ======== LOOP ========
void loop() {

  Ethernet.maintain();

  if (!client.connected()) reconnect_mqtt();
  client.loop();

  unsigned long now = millis();

  // ✅ Vérifie la distance toutes les 1 seconde SEULEMENT pour l'alarme distance
  if (now - lastDistanceCheck >= distanceCheckInterval) {
    lastDistanceCheck = now;
    float distance = lireDistance();

    Serial.print("Distance = ");
    Serial.print(distance);
    Serial.print(" cm | Alarme = ");
    Serial.println(alarmeActive ? "ACTIVE" : "INACTIVE");

    // 🔔 Buzzer SEULEMENT si alarme distance activée ET distance < 50cm
    if (alarmeActive && distance > 0 && distance < 50) {
      tone(BUZZER_PIN, 2000);
      Serial.println("🚨 ALARME DISTANCE: BUZZER ON");
    } else if (alarmeActive) {
      // Si alarme active mais distance > 50cm, éteindre
      noTone(BUZZER_PIN);
    }
    // Note: si alarmeActive == false, le buzzer peut être contrôlé par buzzer/cmd
  }

  // 📡 Publication MQTT toutes les 10 secondes
  if (now - lastPublish >= publishInterval) {
    lastPublish = now;

    // ===== LUMINOSITE =====
    analog_lum = analogRead(capteur_lum);
    Serial.print("Luminosite = ");
    Serial.println(analog_lum);

    char lightStr[8];
    itoa(analog_lum, lightStr, 10);
    client.publish("server-room/light", lightStr);

    // ===== DISTANCE =====
    float distance = lireDistance();
    Serial.print("Distance (publication) = ");
    Serial.print(distance);
    Serial.println(" cm");

    char distStr[10];
    dtostrf(distance, 4, 2, distStr);
    client.publish("server-room/distance", distStr);
  }
}
