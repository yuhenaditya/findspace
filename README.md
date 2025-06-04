# README

Proyek berbasis ThingsBoard. Dokumen ini akan menjelaskan panduan untuk setup ThingsBoard, pengaturan file `.ino`, dan konfigurasi file `App.py`. Ikuti langkah-langkah berikut dengan cermat untuk memastikan setup berjalan lancar.

---

## Tahap Persiapan ThingsBoard

Langkah-langkah ini akan membantu Anda menyiapkan platform ThingsBoard untuk proyek Anda.

- **Instalasi ThingsBoard**  
  Siapkan ThingsBoard menggunakan Docker. Referensi resmi tersedia di: [Docker Hub ThingsBoard](https://hub.docker.com/r/thingsboard/tb-postgres).

- **Login sebagai Admin**  
  Masuk ke ThingsBoard menggunakan akun Admin.

- **Membuat Tenant dan User Tenant**  
  Buat Tenant baru dan User Tenant untuk mengelola perangkat. Lihat panduan resmi di: [ThingsBoard Tenant Guide](https://thingsboard.io/docs/user-guide/ui/tenants/).

- **Login sebagai User Tenant**  
  Setelah tenant dibuat, login kembali ke ThingsBoard menggunakan kredensial User Tenant.

- **Membuat Perangkat (Device)**  
  Tambahkan perangkat baru di ThingsBoard. Ikuti panduan resmi di: [ThingsBoard Device Guide](https://thingsboard.io/docs/user-guide/ui/devices/).

- **Konfigurasi Kredensial Perangkat**  
  - Setelah perangkat dibuat, klik perangkat tersebut dan pilih opsi **Manage Credentials**.
  - Pada tipe **Access Token**, salin token yang ada.
  - Pindah ke tipe **MQTT Basic**, lalu tempel token ke kolom **Username**.
  - Generate **Client ID** dan **Password** untuk MQTT.

---

## Tahap Implementasi File `.ino`

File `.ino` berisi konfigurasi untuk menghubungkan perangkat ke ThingsBoard melalui Wi-Fi dan MQTT. Sesuaikan parameter berikut:

```
// Wi-Fi dan ThingsBoard
const char* ssid = "your_wifi_ssid";        ( Ganti dengan nama Wi-Fi lokal )
const char* password = "your_wifi_password"; ( Ganti dengan kata sandi Wi-Fi )
const char* mqtt_server = "192.168.1.19";   ( Ganti dengan IP ThingsBoard/VM )
const int mqtt_port = 1883;                 ( Port default MQTT )
const char* client_id = "krs6fm4l8aie1fj8l6ll"; ( Ganti dengan Client ID Anda )
const char* user_name = "cmb2tz7hjlrhw70a2cna"; ( Ganti dengan Username ThingsBoard )
const char* mqtt_password = "sfm4va63axxbd3n9qzkl"; ( Ganti dengan Password MQTT. )
```

## Tahap Implementasi File `App.py`
File `App.py` digunakan untuk mengintegrasikan aplikasi dengan ThingsBoard melalui API. Sesuaikan parameter berikut:
```
THINGSBOARD_URL = "http://181.17.0.133:8080"  ( Ganti dengan IP ThingsBoard Anda )
DEVICE_TOKEN = "bb05f420-1ffa-11f0-a0bc-33b4e39bb6f7"  ( Ganti dengan Device Token )
USERNAME = "tenant@user.com"  ( Ganti dengan email User Tenant )
PASSWORD = "Passtenant"  ( Ganti dengan kata sandi User Tenant )
```

# Panduan Tambahan (Opsional)

Panduan ini digunakan jika ingin merubah posisi terisi pada web, atau menambahkan sensor baru.

---

## Menambah atau Mengubah Penggunaan Slot

Saat ini, slot yang digunakan adalah **A1**. Namun, Anda dapat menambah atau mengubahnya untuk slot **A2**, **A3**, atau **A4**. Kunci perubahan ini terletak pada file `.ino`, di mana Anda bisa melakukan penyesuaian sesuai kebutuhan.

### Bagian Callback

Fungsi `callback` digunakan untuk memproses pesan yang diterima dari ThingsBoard. Berikut adalah contoh kode yang dapat disesuaikan:

```cpp
void callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println("Message received: " + message);

  // Parsing pesan dari ThingsBoard untuk slot tertentu
  if (message.indexOf("lamp1") != -1 || message.indexOf("slot1_booked") != -1) {
    slot_booked = (message.indexOf("slot1_booked\":true") != -1);
    updateRGBLED();  // Update RGB LED berdasarkan status terbaru
  }
}
```

**Penyesuaian**:
Dalam kode di atas, string "lamp1", "slot1_booked", dan "slot1_booked\":true" dapat diganti dengan angka 2, 3, atau 4 sesuai slot yang Anda inginkan (misalnya, "lamp2", "slot2_booked", dll.).

### Bagian Loop

Bagian loop digunakan untuk mengirim data telemetry ke ThingsBoard. Berikut contoh kodenya:

```
String payload = "{\"slot1_distance\":" + String(distance) + ",\"slot1_occupied\":" + String(slot_occupied) + ",\"slot1_booked\":" + String(slot_booked) + "}";
client.publish("v1/devices/me/telemetry", payload.c_str());
```

**Penyesuaian:**
Dalam payload di atas, "slot1_distance", "slot1_occupied", dan "slot1_booked" dapat diganti dengan angka 2, 3, atau 4 sesuai slot yang Anda pilih (misalnya, "slot2_distance", "slot2_occupied", dll.).

### Membuat Data Dummy

Jika diperlukan untuk menampilkan variasi data di antarmuka web (seperti status terisi atau kosong), Anda dapat menggunakan data dummy dengan perintah `mosquitto_pub`. Ini berguna untuk menguji atau mensimulasikan kondisi slot tanpa perangkat nyata.

Berikut contoh perintah untuk mengirim data dummy:

```
mosquitto_pub -d -q 1 -h 192.168.18.195 -p 1883 -t v1/devices/me/telemetry -i "your_client_id" -u "your_username" -P "your_password" -m "{\"slot4_distance\":12.5,\"slot4_occupied\":true,\"slot4_booked\":false}"
```

**Penjelasan Parameter:**

-d: Aktifkan mode debug untuk melihat detail proses.

-q 1: Tetapkan kualitas layanan (QoS) ke 1.

-h 192.168.18.195: Host atau IP server MQTT (ganti dengan IP server Anda).

-p 1883: Port MQTT (default adalah 1883, sesuaikan jika berbeda).

-t v1/devices/me/telemetry: Topik untuk mengirim data telemetry ke ThingsBoard.

-i "your_client_id": ID klien (ganti dengan Client ID Anda).

-u "your_username": Nama pengguna MQTT (ganti dengan username Anda).

-P "your_password": Kata sandi MQTT (ganti dengan password Anda).

-m "{\"slot4_distance\":12.5,\"slot4_occupied\":true,\"slot4_booked\":false}": Payload data dummy dalam format JSON, menunjukkan jarak 12.5 cm, slot terisi 
(true), dan tidak dipesan (false).

**Penyesuaian:**
Perintah di atas akan mensimulasikan slot 4 sebagai terisi. Anda dapat mengganti angka "4" dalam "slot4_distance", "slot4_occupied", dan "slot4_booked" dengan angka lain (misalnya, 1, 2, atau 3) sesuai slot yang ingin Anda uji.
Sesuaikan nilai distance, occupied, dan booked dalam payload sesuai kebutuhan (misalnya, "slot4_distance\":15.0" atau "slot4_occupied\":false").
