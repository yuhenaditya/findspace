#include <WiFi.h>
#include <PubSubClient.h>
#include "Arduino.h"
#include "DFRobotDFPlayerMini.h"

// Wi-Fi dan ThingsBoard
const char* ssid = "ssid";
const char* password = "pass";
const char* mqtt_server = "192.168.1.19";
const int mqtt_port = 1883;
const char* client_id = "krs6fm4l8aie1fj8l6ll";
const char* user_name = "cmb2tz7hjlrhw70a2cna";
const char* mqtt_password = "sfm4va63axxbd3n9qzkl";

// Pin sensor ultrasonik, RGB LED, dan DFPlayer
#define TRIG_PIN 12       // Sensor ultrasonik trigger
#define ECHO_PIN 14       // Sensor ultrasonik echo
#define LED_RED_PIN 13    // RGB LED - Red pin
#define LED_GREEN_PIN 25  // RGB LED - Green pin
#define LED_BLUE_PIN 26   // RGB LED - Blue pin

// Pin untuk DFPlayer (Serial2 pada ESP32)
#define DFPLAYER_RX 16  // GPIO16 untuk RX
#define DFPLAYER_TX 17  // GPIO17 untuk TX

#define MAX_DISTANCE 400  // Maksimal jarak deteksi ultrasonik (cm)

WiFiClient espClient;
PubSubClient client(espClient);
HardwareSerial mySerial(2);  // Serial2 untuk DFPlayer
DFRobotDFPlayerMini myDFPlayer;

// Variabel untuk jarak dan status
long duration;
float distance;
bool slot_occupied;
bool slot_booked = false;
const float threshold = 8.0;  // Jarak threshold (cm)
bool wasPlaying = false;      // Status untuk melacak apakah audio sedang diputar
unsigned long lastPlayTime = 0; // Waktu terakhir memutar audio
const unsigned long playDuration = 23000; // Durasi MP3 (23 detik dalam milidetik)

// Variabel untuk mengatur waktu pengiriman data
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 1000;  // Interval pengiriman data: 1 detik

void setup() {
  Serial.begin(115200);

  // Setup pin sensor
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // Setup pin RGB LED
  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_BLUE_PIN, OUTPUT);
  // Inisialisasi RGB LED ke kondisi OFF (untuk common cathode: semua LOW)
  digitalWrite(LED_RED_PIN, LOW);
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_BLUE_PIN, LOW);

  // Inisialisasi DFPlayer dengan Serial2
  mySerial.begin(9600, SERIAL_8N1, DFPLAYER_RX, DFPLAYER_TX);
  delay(1000);  // Delay untuk memastikan DFPlayer siap

  Serial.println("DFPlayer Mini Demo");
  Serial.println("Initializing DFPlayer ...");

  // Inisialisasi DFPlayer
  if (!myDFPlayer.begin(mySerial, true, 1000)) {
    Serial.println("Unable to begin:");
    Serial.println("1. Please recheck the connection!");
    Serial.println("2. Please insert the SD card!");
    while (true)
      ;  // Hentikan jika gagal
  }

  Serial.println("DFPlayer Mini online.");
  myDFPlayer.volume(20);  // Set volume ke 20 (sesuaikan 0-30)

  // Koneksi Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  // Koneksi MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void reconnect() {
  while (!client.connected()) {
    Serial.println("Connecting to MQTT...");
    if (client.connect(client_id, user_name, mqtt_password)) {
      Serial.println("Connected to MQTT");
      client.subscribe("v1/devices/me/attributes");
    } else {
      Serial.print("Failed, rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println("Message received: " + message);

  // Parsing pesan dari ThingsBoard untuk slot B2
  if (message.indexOf("lamp1") != -1 || message.indexOf("slot1_booked") != -1) {
    slot_booked = (message.indexOf("slot1_booked\":true") != -1);
    updateRGBLED();  // Update RGB LED berdasarkan status terbaru
  }
}

float readDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH);
  float distance = duration * 0.034 / 2;
  if (distance > MAX_DISTANCE) distance = MAX_DISTANCE;
  return distance;
}

void updateRGBLED() {
  // Matikan semua warna terlebih dahulu
  digitalWrite(LED_RED_PIN, LOW);
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_BLUE_PIN, LOW);

  // Logika warna:
  // - Merah: slot terisi (slot_occupied = true)
  // - Biru: slot dibooking tapi tidak terisi (slot_booked = true && !slot_occupied)
  // - Hijau: slot kosong dan tidak dibooking (!slot_occupied && !slot_booked)
  if (slot_occupied) {
    digitalWrite(LED_RED_PIN, HIGH);  // Merah untuk occupied
    Serial.println("RGB LED: Red (Occupied)");
  } else if (slot_booked) {
    digitalWrite(LED_BLUE_PIN, HIGH);  // Biru untuk booked
    Serial.println("RGB LED: Blue (Booked)");
  } else {
    digitalWrite(LED_GREEN_PIN, HIGH);  // Hijau untuk empty
    Serial.println("RGB LED: Green (Empty)");
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Kirim data setiap 1 detik
  unsigned long currentTime = millis();
  if (currentTime - lastSendTime >= sendInterval) {
    distance = readDistance(TRIG_PIN, ECHO_PIN);
    slot_occupied = (distance < threshold);

    // Kontrol DFPlayer
    int currentState = myDFPlayer.readState();  // 0=stop, 1=playing, 2=paused
    if (slot_booked && slot_occupied) {
      // Cek apakah audio harus dimulai atau diulang
      if (!wasPlaying || currentState == 0 || (currentTime - lastPlayTime >= playDuration)) {
        myDFPlayer.play(1);                    // Memutar file 0001.mp3 dari awal
        wasPlaying = true;
        lastPlayTime = currentTime;            // Perbarui waktu pemutaran terakhir
        Serial.println("Playing audio from start...");
      }
    } else {
      if (currentState != 0) {  // Hentikan jika kondisi tidak terpenuhi
        myDFPlayer.stop();
        wasPlaying = false;
        Serial.println("Stopping audio...");
      }
    }

    // Update RGB LED berdasarkan status
    updateRGBLED();

    // Kirim data ke ThingsBoard
    String payload = "{\"slot1_distance\":" + String(distance) + ",\"slot1_occupied\":" + String(slot_occupied) + ",\"slot1_booked\":" + String(slot_booked) + "}";
    client.publish("v1/devices/me/telemetry", payload.c_str());

    Serial.println("Data sent: " + payload);
    lastSendTime = currentTime;
  }
}
