# 🌦️ Jemuran Otomatis Cerdas (SmartDry)

[![Lisensi MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-black?logo=flask)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-blue?logo=postgresql)](https://www.postgresql.org/)
[![Arduino](https://img.shields.io/badge/Arduino-C%2B%2B-00979D?logo=arduino)](https://www.arduino.cc/)

Sebuah sistem jemuran pakaian otomatis berbasis IoT yang dapat menarik jemuran secara mandiri saat terdeteksi hujan dan mengeluarkannya kembali saat cuaca kembali cerah. Dilengkapi dengan dashboard web modern untuk monitoring dan kontrol manual.

![Dashboard Aplikasi](https://i.ibb.co/L5YwYyV/smartdry-dashboard.png)
*(Tips: Ganti URL gambar di atas dengan screenshot aplikasi Anda sendiri setelah berjalan)*

---

## ✨ Fitur Utama

- **👕 Mode Otomatis**: Jemuran akan masuk/keluar secara otomatis berdasarkan data dari sensor hujan.
- **✋ Mode Manual**: Ambil alih kontrol kapan saja melalui dashboard web untuk menarik atau menghentikan motor.
- **📊 Dashboard Real-time**: Pantau status cuaca, mode operasi, dan posisi jemuran melalui visualisasi yang menarik dan informatif.
- **📜 Pencatatan Data (Logging)**: Setiap perubahan cuaca (hujan/cerah) dicatat ke dalam database PostgreSQL lengkap dengan timestamp.
- **🗑️ Manajemen Log**: Hapus data log yang tidak diinginkan, baik satu per satu, beberapa sekaligus, atau semua data.
- **📈 Statistik**: Lihat ringkasan data seperti jumlah record dan deteksi cuaca hari ini (fitur dari API `/stats`).
- **📱 Desain Responsif**: Tampilan dapat diakses dengan baik melalui perangkat desktop maupun mobile.

---

## 🏗️ Arsitektur Sistem

Sistem ini terdiri dari beberapa komponen utama yang saling berkomunikasi untuk menciptakan sistem yang cerdas dan otomatis.

```mermaid
graph TD
    subgraph "Perangkat Keras"
        A[Sensor Hujan] --> B(Mikrokontroler <br> Arduino UNO);
        M[Motor DC & Driver] <--> B;
    end

    subgraph "Perangkat Lunak"
        B -- "Kirim Status via Serial" --> C{Backend Server <br> (Flask + Python)};
        C <--> D[Database <br> (PostgreSQL)];
        C -- "Sajikan Data & Kontrol" --> F[Frontend <br> (Web Browser)];
    end

    subgraph "Pengguna"
         E[Pengguna] <--> F;
    end

    style B fill:#00979D,stroke:#fff,stroke-width:2px,color:#fff
    style C fill:#333,stroke:#fff,stroke-width:2px,color:#fff
    style D fill:#32658C,stroke:#fff,stroke-width:2px,color:#fff
```

---

## 🛠️ Teknologi yang Digunakan

| Kategori         | Teknologi                                                              |
| ---------------- | ---------------------------------------------------------------------- |
| **Backend** | Python, Flask, Psycopg2, PySerial, Flask-CORS                          |
| **Frontend** | HTML5, CSS3, JavaScript (Vanilla)                                      |
| **Database** | PostgreSQL                                                             |
| **Hardware** | Arduino UNO (atau sejenisnya), Sensor Hujan, Driver Motor L298N, Motor DC |
| **Protokol** | HTTP, Serial                                                           |

---

## 🚀 Panduan Instalasi

Ikuti langkah-langkah berikut untuk menjalankan proyek ini di lingkungan lokal Anda.

### 1. Prasyarat

Pastikan perangkat lunak berikut sudah terpasang:
- [Python](https://www.python.org/downloads/) (versi 3.9 atau lebih baru)
- [PostgreSQL](https://www.postgresql.org/download/) (versi 12 atau lebih baru)
- [Arduino IDE](https://www.arduino.cc/en/software)
- [Git](https://git-scm.com/downloads/)

### 2. Perangkat Keras
- Rangkai semua komponen perangkat keras (Arduino, sensor, driver motor) sesuai dengan skema Anda.
- Upload kode dari file `.ino` Anda ke board Arduino melalui Arduino IDE. Pastikan untuk memilih Board dan Port yang benar.

### 3. Konfigurasi Database
- Buka `psql` atau pgAdmin.
- Buat database baru dan pengguna baru (opsional, bisa juga menggunakan user `postgres`).
  ```sql
  CREATE DATABASE jemuran_otomatis;
  ```
- Hubungkan ke database yang baru dibuat dan buat tabel `rain_logs`.
  ```sql
  \c jemuran_otomatis;

  CREATE TABLE rain_logs (
      id SERIAL PRIMARY KEY,
      log_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
      is_raining BOOLEAN NOT NULL
  );
  ```

### 4. Konfigurasi Backend (Server)

```bash
# 1. Clone repositori ini
git clone [https://github.com/ferdiodwi/smart-dry.git](https://github.com/ferdiodwi/smart-dry.git)
cd smart-dry

# 2. Buat dan aktifkan virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. Install semua dependensi dari file requirements.txt
pip install -r requirements.txt

# 4. Konfigurasi app.py
#    Buka file app.py dan sesuaikan bagian konfigurasi:
#    - ARDUINO_PORT: Sesuaikan dengan port Arduino Anda (misal: 'COM3' atau '/dev/ttyUSB0').
#    - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS: Sesuaikan dengan konfigurasi PostgreSQL Anda.

# 5. Jalankan server Flask
python app.py
```

### 5. Akses Aplikasi
- Buka browser Anda dan kunjungi alamat `http://127.0.0.1:5000`.
- Aplikasi siap digunakan!

---

## 📡 Endpoint API

| Metode | Endpoint             | Deskripsi                                            |
| ------ | -------------------- | ---------------------------------------------------- |
| `GET`  | `/`                  | Menampilkan halaman utama (dashboard).               |
| `GET`  | `/data`              | Mengambil semua data log cuaca dari database.        |
| `GET`  | `/status`            | Mendapatkan status mode kontrol saat ini (AUTO/MANUAL). |
| `POST` | `/control`           | Mengirim perintah (ubah mode, kontrol motor).        |
| `POST` | `/delete_data`       | Menghapus satu data log berdasarkan ID.              |
| `POST` | `/delete_multiple`   | Menghapus beberapa data log berdasarkan array ID.    |
| `POST` | `/delete_all`        | Menghapus semua data log dari tabel.                 |
| `GET`  | `/stats`             | Mendapatkan statistik sederhana dari data log.       |

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah **Lisensi MIT**. Lihat file `LICENSE` untuk detail lebih lanjut.