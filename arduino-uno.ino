// Version Ethernet + MQTT pour Arduino UNO
// Contrôle buzzer via 2 modes:
// 1. server-room/buzzer/cmd → Contrôle direct ON/OFF
// 2. server-room/alarm/cmd → Alarme distance < 50cm

#include <SPI.h>
#include <Ethernet.h>
#include <PubSubClient.h>
#include <Ultrasonic.h>

// ======== ULTRASON GROVE ========
#define ULTRASONIC_PIN 2
Ultrasonic ultrasonic(ULTRASONIC_PIN);

// ======== BUZZER ========
#define BUZZER_PIN 6
bool alarmeActive = false;     // Alarme distance via alarm/cmd
bool buzzerForce = false;      // Contrôle direct via buzzer/cmd

// ======== LUMINOSITE ========
const int capteur_lum = A0;
int analog_lum;

// ======== RESEAU ETHERNET ========
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(10,160,24,100);
IPAddress gateway(10,160,24,1);
IPAddress subnet(255,255,252,0);

// ======== MQTT ========
const char* mqtt_server = "10.160.24.188";
const int mqtt_port = 1883;
const char* mqtt_user = "arduino";
const char* mqtt_pass = "arduinopass";

EthernetClient ethClient;
PubSubClient client(ethClient);

unsigned long lastPublish = 0;
const long publishInterval = 10000; // 10 sec

unsigned long lastDistanceCheck = 0;
const long distanceCheckInterval = 1000; // 1 sec

// ======== LECTURE DISTANCE ========
float lireDistance() {
  long distance = ultrasonic.read();
  if (distance <= 0 || distance > 400) return -1;
  return distance;
}

// ======== CALLBACK MQTT ========
void callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  
  // Nettoyer les espaces/retours à la ligne
  msg.trim();

  Serial.print("Message recu [");
  Serial.print(topic);
  Serial.print("]: '");
  Serial.print(msg);
  Serial.print("' (length=");
  Serial.print(length);
  Serial.println(")");
  
  // Debug: afficher chaque caractère
  Serial.print("Bytes: ");
  for (int i = 0; i < length; i++) {
    Serial.print((int)payload[i]);
    Serial.print(" ");
  }
  Serial.println();

  // 🔔 COMMANDE BUZZER DIRECT (priorité haute)
  if (String(topic) == "server-room/buzzer/cmd") {
    
    // Comparer avec trim() et ignorer la casse
    msg.toUpperCase();
    
    if (msg == "ON") {
      buzzerForce = true;
      tone(BUZZER_PIN, 2000);
      Serial.println("🔔 BUZZER FORCE ON");
    }
    else if (msg == "OFF") {
      buzzerForce = false;
      noTone(BUZZER_PIN);
      Serial.println("🔕 BUZZER FORCE OFF");
    }
    else {
      Serial.print("⚠️ Commande inconnue: '");
      Serial.print(msg);
      Serial.println("'");
    }
  }

  // 🚨 COMMANDE ALARME DISTANCE
  if (String(topic) == "server-room/alarm/cmd") {
    
    msg.toUpperCase();
    
    if (msg == "ON") {
      alarmeActive = true;
      Serial.println("✅ ALARME DISTANCE ACTIVEE");
    }
    else if (msg == "OFF") {
      alarmeActive = false;
      // Éteindre le buzzer seulement si pas en mode force
      if (!buzzerForce) {
        noTone(BUZZER_PIN);
      }
      Serial.println("❌ ALARME DISTANCE DESACTIVEE");
    }
    else {
      Serial.print("⚠️ Commande alarme inconnue: '");
      Serial.print(msg);
      Serial.println("'");
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
      client.subscribe("server-room/buzzer/cmd");
      Serial.println("Abonne a: alarm/cmd, buzzer/cmd");
    } else {
      Serial.print("Erreur rc=");
      Serial.print(client.state());
      Serial.println(" retry 5s");
      delay(5000);
    }
  }
}

// ======== SETUP ========
void setup() {
  Serial.begin(9600);

  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  Serial.println("=== Arduino Server Room ===");
  Serial.println("Initialisation Ethernet...");
  Ethernet.begin(mac, ip, gateway, gateway, subnet);
  delay(1500);

  Serial.print("IP Arduino: ");
  Serial.println(Ethernet.localIP());

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  Serial.println("Arduino pret!");
  Serial.println("Modes buzzer:");
  Serial.println("  1. buzzer/cmd → Force ON/OFF");
  Serial.println("  2. alarm/cmd → Auto si distance < 50cm");
}

// ======== LOOP ========
void loop() {

  Ethernet.maintain();

  if (!client.connected()) reconnect_mqtt();
  client.loop();

  unsigned long now = millis();

  // ✅ Gestion alarme distance toutes les 1 seconde
  if (now - lastDistanceCheck >= distanceCheckInterval) {
    lastDistanceCheck = now;
    float distance = lireDistance();

    Serial.print("Distance = ");
    Serial.print(distance);
    Serial.print(" cm | Alarme = ");
    Serial.print(alarmeActive ? "ON" : "OFF");
    Serial.print(" | Buzzer Force = ");
    Serial.println(buzzerForce ? "ON" : "OFF");

    // 🔔 Logique du buzzer (priorité: force > alarme distance)
    if (buzzerForce) {
      // Mode force activé → buzzer reste ON quoi qu'il arrive
      tone(BUZZER_PIN, 2000);
    }
    else if (alarmeActive && distance > 0 && distance < 50) {
      // Alarme distance activée ET objet proche
      tone(BUZZER_PIN, 2000);
      Serial.println("  🚨 ALARME: Objet detecte!");
    }
    else {
      // Aucune condition → éteindre
      noTone(BUZZER_PIN);
    }
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
    
    Serial.println("--- Cycle publication termine ---");
  }
}