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
  
  char luxStr[8];
  dtostrf(lux, 4, 0, luxStr);
  client.publish("server-room/light", luxStr);
  Serial.print("Luminosite publiee: ");
  Serial.println(luxStr);

  // ===== Distance =====
  float distance = distanceSensor.measureDistanceCm();
  
  if (distance > 0 && distance < 400) {
    char distStr[8];
    dtostrf(distance, 4, 2, distStr);
    client.publish("server-room/distance", distStr);
    Serial.print("Distance publiee: ");
    Serial.println(distStr);
  }

  delay(10000); // 10 secondes
}
