#include <SPI.h>
#include <Ethernet.h>
#include <PubSubClient.h>
#include <Ultrasonic.h>   // ← Librairie Grove officielle

// ======== ULTRASON GROVE ========
#define ULTRASONIC_PIN 2
Ultrasonic ultrasonic(ULTRASONIC_PIN);

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

// ======== LECTURE DISTANCE ========
float lireDistance() {
  long distance = ultrasonic.read();   // ← correction ici

  if (distance <= 0 || distance > 400) {
    return -1;
  }
  return distance;
}

// ======== CALLBACK MQTT ========
void callback(char* topic, byte* payload, unsigned int length) {
  String msg="";
  for (int i=0;i<length;i++) msg+=(char)payload[i];

  Serial.print("Message recu : ");
  Serial.println(msg);
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
  if (now - lastPublish >= publishInterval) {

    lastPublish = now;

    // ===== LUMINOSITE =====
    analog_lum = analogRead(capteur_lum);
    Serial.print("Luminosite = ");
    Serial.println(analog_lum);

    char lightStr[8];
    itoa(analog_lum, lightStr, 10);
    client.publish("server-room/light", lightStr);

    // ===== DISTANCE GROVE =====
    float distance = lireDistance();

    Serial.print("Distance = ");
    Serial.print(distance);
    Serial.println(" cm");

    char distStr[10];
    dtostrf(distance, 4, 2, distStr);
    client.publish("server-room/distance", distStr);
  }
}