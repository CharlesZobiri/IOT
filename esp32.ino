#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

#define DHTPIN 18
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "ServerRoom-IoT";
const char* password = "iot2026secure";
const char* mqtt_server = "192.168.4.1";
const int mqtt_port = 1883;
const char* mqtt_user = "esp32";
const char* mqtt_pass = "esp32pass";

WiFiClient espClient;
PubSubClient client(espClient);

unsigned long lastPublish = 0;
const long publishInterval = 10000;

void setup_wifi() {
  Serial.println("Connexion WiFi...");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi OK - IP: " + WiFi.localIP().toString());
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("MQTT...");
    if (client.connect("ESP32-DHT11", mqtt_user, mqtt_pass)) {
      Serial.println("OK");
    } else {
      Serial.println("ECHEC");
      delay(2000);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Recu: ");
  Serial.println(topic);
}

void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("\n=== ESP32 DHT11 ===");
  
  dht.begin();
  delay(2000);  // Laisser le DHT11 s'initialiser
  Serial.println("DHT11 pret");
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setBufferSize(512);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  unsigned long now = millis();
  if (now - lastPublish >= publishInterval) {
    lastPublish = now;
    
    float temp = dht.readTemperature();
    float hum = dht.readHumidity();
    
    Serial.print("\n[");
    Serial.print(millis() / 1000);
    Serial.print("s] Temp: ");
    Serial.print(temp);
    Serial.print("C | Hum: ");
    Serial.print(hum);
    Serial.println("%");
    
    if (isnan(temp) || isnan(hum)) {
      Serial.println("=> DHT11 erreur lecture!");
      return;
    }
    
    char tempStr[10];
    char humStr[10];
    snprintf(tempStr, sizeof(tempStr), "%.2f", temp);
    snprintf(humStr, sizeof(humStr), "%.2f", hum);
    
    // Publication température
    Serial.print("=> Pub temp...");
    if (client.publish("server-room/temperature", tempStr)) {
      Serial.println("OK");
    } else {
      Serial.println("ECHEC");
    }
    
    client.loop();
    delay(500);  // Délai important entre les deux publications
    
    // Publication humidité
    Serial.print("=> Pub hum...");
    if (client.publish("server-room/humidity", humStr)) {
      Serial.println("OK");
    } else {
      Serial.println("ECHEC");
    }
  }
}