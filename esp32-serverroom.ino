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
    char tempStr[8];
    dtostrf(temp, 4, 2, tempStr);
    client.publish("server-room/temperature", tempStr);
    Serial.print("Temperature publiee: ");
    Serial.println(tempStr);

    // Humidité
    char humStr[8];
    dtostrf(hum, 4, 2, humStr);
    client.publish("server-room/humidity", humStr);
    Serial.print("Humidite publiee: ");
    Serial.println(humStr);
  }

  delay(10000); // 10 secondes
}
