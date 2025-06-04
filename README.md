**Tahap - Tahap Perubahan / Penyesuaian**

**Tahap Persiapan Thingsboard**
1. Siapkan Thingsboard bisa dengan referensi ini https://hub.docker.com/r/thingsboard/tb-postgres
2. Login ke Thingsboard sebagai user **Admin**
3. Tambahkan / buat **Tenant** beserta **User Tenant**, bisa dengan referensi ini https://thingsboard.io/docs/user-guide/ui/tenants/
4. Jika sudah memiliki / sudah membuat, login kembali ke Thingsboard dengan user **tenant**
5. Buat Device, bisa dengan referensi ini https://thingsboard.io/docs/user-guide/ui/devices/
6. Setelah terbuat klik dan pilih opsi **"Manage Credentials"**
7. Pada type **Access Token**, copy isinya dan geser ke type **MQTT Basic**. Kemudian paste pada kolom **Username**
8. Setelah itu Generate **Client ID** dan **Pass**

**Tahap Implementasi File .ino**
Pada file .ino terdapat kolom yang bisa di sesuaikan

`// Wi-Fi dan ThingsBoard`

`const char* ssid = "ssid"; ( ganti dengan wifi lokal )` 

`const char* password = "pass"; ( ganti dengan pass wifi )`

`const char* mqtt_server = "192.168.1.19" ( ganti dengan ip vm/thingsboard );`

`const int mqtt_port = 1883;`

`const char* client_id = "krs6fm4l8aie1fj8l6ll"; ( ganti dengan client id mu )`

`const char* user_name = "cmb2tz7hjlrhw70a2cna"; ( ganti dengan username thingsboard )`

`const char* mqtt_password = "sfm4va63axxbd3n9qzkl"; ( ganti dengan pass )`

**Tahap Implementasi FIle App.py**
Pada file App.py terdapat kolom yang bisa di sesuaikan

THINGSBOARD_URL = "http://181.17.0.133:8080" ( ganti dengan ip mu )
DEVICE_TOKEN = "bb05f420-1ffa-11f0-a0bc-33b4e39bb6f7" ( ganti )
USERNAME = "tenant@user.com" ( ganti dengan user tenant mu )
PASSWORD = "Passtenant" ( ganti dengan pass tenant usermu )

Panduan Konfigurasi dan Implementasi ThingsBoard
Selamat datang di panduan konfigurasi dan implementasi proyek berbasis ThingsBoard. Dokumen ini akan memandu Anda melalui tahap-tahap persiapan ThingsBoard, pengaturan file .ino, dan konfigurasi file App.py. Ikuti langkah-langkah berikut dengan cermat untuk memastikan setup berjalan lancar.

Tahap Persiapan ThingsBoard
Langkah-langkah ini akan membantu Anda menyiapkan platform ThingsBoard untuk proyek Anda.

Instalasi ThingsBoardSiapkan ThingsBoard menggunakan Docker. Referensi resmi tersedia di:Docker Hub ThingsBoard.

Login sebagai AdminMasuk ke ThingsBoard menggunakan akun Admin.

Membuat Tenant dan User TenantBuat Tenant baru dan User Tenant untuk mengelola perangkat. Lihat panduan resmi di:ThingsBoard Tenant Guide.

Login sebagai User TenantSetelah tenant dibuat, login kembali ke ThingsBoard menggunakan kredensial User Tenant.

Membuat Perangkat (Device)Tambahkan perangkat baru di ThingsBoard. Ikuti panduan resmi di:ThingsBoard Device Guide.

Konfigurasi Kredensial Perangkat  

Setelah perangkat dibuat, klik perangkat tersebut dan pilih opsi Manage Credentials.
Pada tipe Access Token, salin token yang ada.
Pindah ke tipe MQTT Basic, lalu tempel token ke kolom Username.
Generate Client ID dan Password untuk MQTT.




Tahap Implementasi File .ino
File .ino berisi konfigurasi untuk menghubungkan perangkat ke ThingsBoard melalui Wi-Fi dan MQTT. Sesuaikan parameter berikut:
// Wi-Fi dan ThingsBoard
const char* ssid = "your_wifi_ssid";        // Ganti dengan nama Wi-Fi lokal
const char* password = "your_wifi_password"; // Ganti dengan kata sandi Wi-Fi
const char* mqtt_server = "192.168.1.19";   // Ganti dengan IP ThingsBoard/VM
const int mqtt_port = 1883;                 // Port default MQTT
const char* client_id = "krs6fm4l8aie1fj8l6ll"; // Ganti dengan Client ID Anda
const char* user_name = "cmb2tz7hjlrhw70a2cna"; // Ganti dengan Username ThingsBoard
const char* mqtt_password = "sfm4va63axxbd3n9qzkl"; // Ganti dengan Password MQTT

Catatan: Pastikan IP server, Client ID, Username, dan Password sesuai dengan konfigurasi ThingsBoard Anda.

Tahap Implementasi File App.py
File App.py digunakan untuk mengintegrasikan aplikasi dengan ThingsBoard melalui API. Sesuaikan parameter berikut:
THINGSBOARD_URL = "http://181.17.0.133:8080"  # Ganti dengan IP ThingsBoard Anda
DEVICE_TOKEN = "bb05f420-1ffa-11f0-a0bc-33b4e39bb6f7"  # Ganti dengan Device Token
USERNAME = "tenant@user.com"  # Ganti dengan email User Tenant
PASSWORD = "Passtenant"  # Ganti dengan kata sandi User Tenant

Catatan:  

Pastikan URL menggunakan IP dan port yang benar.  
Gunakan kredensial tenant yang valid untuk autentikasi.


Tips Tambahan

Verifikasi Koneksi: Pastikan perangkat Anda terhubung ke jaringan Wi-Fi dan server ThingsBoard dapat dijangkau.
Keamanan: Simpan kredensial seperti Client ID, Username, dan Password dengan aman. Jangan hardcode dalam kode produksi.
Debugging: Jika terjadi error, periksa log di ThingsBoard atau gunakan alat seperti Mosquitto untuk memeriksa koneksi MQTT.


Kontribusi
Jika Anda ingin berkontribusi pada proyek ini, silakan fork repositori ini dan ajukan pull request. Pastikan untuk mengikuti panduan kontribusi di repositori.
Lisensi
Proyek ini dilisensikan di bawah MIT License.
