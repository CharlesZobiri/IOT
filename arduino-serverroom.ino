// Version Ethernet + MQTT pour Arduino UNO
// Alarme distance contrôlée par dashboard via MQTT

#include <SPI.h>
#include <Ethernet.h>
#include <PubSubClient.h>
#include <Ultrasonic.h>

// ======== ULTRASON GROVE ========
#define ULTRASONIC_PIN 2
Ultrasonic ultrasonic(ULTRASONIC_PIN);

// ======== BUZZER ========
#define BUZZER_PIN 6
bool alarmeActive = false;  // ← Contrôlé par MQTT uniquement

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
  String msg="";
  for (int i=0;i<length;i++) msg+=(char)payload[i];

  Serial.print("Message recu [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(msg);

  // 🔔 COMMANDE ALARME DISTANCE
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

  Serial.println("Initialisation Ethernet...");
  Ethernet.begin(mac, ip, gateway, gateway, subnet);
  delay(1500);

  Serial.print("IP Arduino : ");
  Serial.println(Ethernet.localIP());

  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  Serial.println("Arduino pret !");
}

// ======== LOOP ========
void loop() {

  Ethernet.maintain();

  if (!client.connected()) reconnect_mqtt();
  client.loop();

  unsigned long now = millis();

  // ✅ Vérifie la distance toutes les 1 seconde
  if (now - lastDistanceCheck >= distanceCheckInterval) {
    lastDistanceCheck = now;
    float distance = lireDistance();

    Serial.print("Distance = ");
    Serial.print(distance);
    Serial.print(" cm | Alarme = ");
    Serial.println(alarmeActive ? "ACTIVE" : "INACTIVE");

    // 🔔 Buzzer SEULEMENT si alarme activée ET distance < 50cm
    if (alarmeActive && distance > 0 && distance < 50) {
      tone(BUZZER_PIN, 2000);
      Serial.println("🚨 BUZZER ON (distance < 50cm)");
    } else {
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
  }
}
