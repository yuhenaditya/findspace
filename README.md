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
1. Pada file .ino terdapat kolom
   `// Wi-Fi dan ThingsBoard
const char* ssid = "ssid";
const char* password = "pass";
const char* mqtt_server = "192.168.1.19";
const int mqtt_port = 1883;
const char* client_id = "krs6fm4l8aie1fj8l6ll";
const char* user_name = "cmb2tz7hjlrhw70a2cna";
const char* mqtt_password = "sfm4va63axxbd3n9qzkl";`
