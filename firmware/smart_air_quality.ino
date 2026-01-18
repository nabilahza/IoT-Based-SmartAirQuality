#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

// ================== PIN DEFINITIONS ==================
#define MQ135_PIN A1
#define GREEN_LED 4
#define YELLOW_LED 5
#define RED_LED 6
#define FAN_RELAY 38

// ================== WIFI ==================
const char* ssid = "AndroidAP121F";
const char* password = "wifipassword";

// ================== MQTT (TLS) ==================
const char* mqttServer = "34.10.35.179";
const int mqttPort = 8883;
const char* mqttUser = "esp32_airquality";
const char* mqttPass = "admin@123";
const char* mqttTopic = "airquality/room1";

// ================== CA CERTIFICATE ==================
const char* ca_cert = R"EOF(
-----BEGIN CERTIFICATE-----
Add CA certificate here
-----END CERTIFICATE-----
)EOF";

// ================== OBJECTS ==================
WiFiClientSecure espClient;
PubSubClient client(espClient);

// ================== MQTT RECONNECT ==================
void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT... ");
    if (client.connect("ESP32-AirQuality", mqttUser, mqttPass)) {
      Serial.println("CONNECTED ");
    } else {
      Serial.print("FAILED (rc=");
      Serial.print(client.state());
      Serial.println(")");
      delay(3000);
    }
  }
}

// ================== SETUP ==================
void setup() {
  Serial.begin(115200);
  delay(2000);

  pinMode(GREEN_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(FAN_RELAY, OUTPUT);

  // -------- WiFi --------
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n WiFi connected");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // -------- MQTT --------
  espClient.setCACert(ca_cert);
  client.setServer(mqttServer, mqttPort);
  reconnect();
}

// ================== LOOP ==================
void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  // -------- READ SENSOR --------
  int gas = analogRead(MQ135_PIN);
  String level;
  String fanStatus = "OFF";
  String ledStatus = "OFF";

  // -------- GAS LEVEL LOGIC --------
  if (gas < 1200) {
    level = "Good";
  }
  else if (gas < 1500) {
    level = "Moderate";
  }
  else if (gas < 1800) {
    level = "Unhealthy";
  }
  else {
    level = "Hazardous";
  }

  // -------- RESET OUTPUTS --------
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(RED_LED, LOW);
  digitalWrite(FAN_RELAY, LOW);

  // -------- ACTUATORS --------
  if (level == "Good") {
    digitalWrite(GREEN_LED, HIGH);
    ledStatus = "GREEN";
  }
  else if (level == "Moderate") {
    digitalWrite(YELLOW_LED, HIGH);
    digitalWrite(FAN_RELAY, HIGH);
    ledStatus = "YELLOW";
    fanStatus = "ON";
  }
  else {
    digitalWrite(RED_LED, HIGH);
    digitalWrite(FAN_RELAY, HIGH);
    ledStatus = "RED";
    fanStatus = "ON";
  }

  // -------- JSON PAYLOAD --------
  String payload = "{";
  payload += "\"gas\":" + String(gas) + ",";
  payload += "\"sensor_id\":\"esp32\",";
  payload += "\"level\":\"" + level + "\",";
  payload += "\"fan\":\"" + fanStatus + "\",";
  payload += "\"led\":\"" + ledStatus + "\"";
  payload += "}";

  // -------- SEND TO CLOUD --------
  Serial.println("Sending data to cloud:");
  Serial.println(payload);

  bool sent = client.publish(mqttTopic, payload.c_str());

  if (sent) {
    Serial.println("Data sent successfully\n");
  } else {
    Serial.println("Failed to send data\n");
  }

  delay(5000);
}
