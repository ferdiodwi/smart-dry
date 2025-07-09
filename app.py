import serial
import psycopg2
import threading
import time
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# ==============================================================================
# --- KONFIGURASI (WAJIB DISESUAIKAN) ---
# ==============================================================================

# Ganti dengan port serial Arduino Anda.
# Di Windows biasanya 'COM3', 'COM4', dst.
# Di Linux/macOS biasanya '/dev/ttyACM0' atau '/dev/ttyUSB0'.
ARDUINO_PORT = '/dev/ttyUSB0'  # <-- GANTI INI!

# Pastikan baud rate sama dengan yang ada di kode Arduino (Serial.begin(9600))
BAUD_RATE = 9600

# Konfigurasi koneksi ke database PostgreSQL Anda
DB_HOST = "localhost"
DB_NAME = "jemuran_otomatis"
DB_USER = "postgres"
DB_PASS = "123"  # <-- GANTI DENGAN PASSWORD POSTGRESQL ANDA!

# ==============================================================================
# --- INISIALISASI APLIKASI ---
# ==============================================================================

app = Flask(__name__)
CORS(app)  # Izinkan permintaan dari halaman web

# Variabel global untuk menampung koneksi serial dan status
arduino = None
current_control_mode = "AUTO"

# Fungsi untuk membuat koneksi ke database
def get_db_connection():
    """Membuat koneksi baru ke database PostgreSQL."""
    conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    return conn

# Fungsi untuk mencoba terhubung ke Arduino
def connect_to_arduino():
    """Mencoba membuat koneksi serial ke Arduino."""
    global arduino
    try:
        arduino = serial.Serial(port=ARDUINO_PORT, baudrate=BAUD_RATE, timeout=1)
        time.sleep(2)  # Beri waktu agar koneksi stabil setelah dibuka
        print(f"Berhasil terhubung ke Arduino di port {ARDUINO_PORT}")
        return True
    except serial.SerialException as e:
        print(f"Gagal terhubung ke Arduino di port {ARDUINO_PORT}. Error: {e}")
        print("Aplikasi akan terus mencoba terhubung di latar belakang.")
        arduino = None
        return False

# ==============================================================================
# --- THREAD UNTUK KOMUNIKASI DENGAN ARDUINO ---
# ==============================================================================

def arduino_listener():
    """
    Berjalan di thread terpisah untuk terus menerus mendengarkan data dari Arduino
    tanpa memblokir server web.
    """
    global arduino

    while True:
        if arduino and arduino.is_open:
            try:
                if arduino.in_waiting > 0:
                    line = arduino.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line and line.startswith("STATUS:"):
                        status_str = line.split(":")[1]
                        is_raining_now = (status_str == "HUJAN")
                        
                        # =====================================================
                        # PERUBAHAN DI SINI: Kondisi 'if' dihapus
                        # Kode ini akan langsung menyimpan ke DB setiap menerima status
                        # =====================================================
                        try:
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute("INSERT INTO rain_logs (is_raining) VALUES (%s)", (is_raining_now,))
                            conn.commit()
                            cur.close()
                            conn.close()
                            print(f"DATABASE LOG: Status '{'HUJAN' if is_raining_now else 'CERAH'}' berhasil disimpan.")
                        except Exception as e:
                            print(f"Error saat menyimpan log ke database: {e}")

            except serial.SerialException as e:
                print(f"Koneksi serial ke Arduino terputus: {e}")
                arduino.close()
                arduino = None
            except Exception as e:
                print(f"Error saat memproses data dari Arduino: {e}")
        else:
            print("Mencoba menghubungkan kembali ke Arduino...")
            connect_to_arduino()
            time.sleep(5)
        
        time.sleep(0.1)

# ==============================================================================
# --- RUTE API & HALAMAN WEB (FLASK) ---
# ==============================================================================

@app.route('/')
def index():
    """Menyajikan halaman web utama (index.html)."""
    return render_template('index.html')

@app.route('/data', methods=['GET'])
def get_data():
    """API untuk mengambil 20 data log terakhir dari database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, TO_CHAR(log_time, 'DD Mon YYYY, HH24:MI:SS'), is_raining FROM rain_logs ORDER BY id DESC")
        logs = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """API untuk mendapatkan status mode kontrol saat ini."""
    return jsonify({"mode": current_control_mode})

@app.route('/control', methods=['POST'])
def control_jemuran():
    """API untuk mengirim perintah kontrol ke Arduino."""
    global current_control_mode
    data = request.get_json()
    command = None

    if 'mode' in data:
        mode = data['mode'].upper()
        if mode in ['AUTO', 'MANUAL']:
            command = f"MODE_{mode}\n"
            current_control_mode = mode
    
    elif 'action' in data and current_control_mode == 'MANUAL':
        action = data['action'].upper()
        if action in ['ON', 'OFF']:
            command = f"MANUAL_{action}\n"

    if command and arduino and arduino.is_open:
        try:
            arduino.write(command.encode('utf-8'))
            return jsonify({"status": "success", "command_sent": command.strip()})
        except Exception as e:
            return jsonify({"status": "error", "message": f"Gagal mengirim ke Arduino: {e}"}), 500
            
    elif not (arduino and arduino.is_open):
        return jsonify({"status": "error", "message": "Perintah tidak dikirim. Arduino tidak terhubung."}), 400

    return jsonify({"status": "failed", "message": "Perintah tidak valid atau tidak dalam mode manual."}), 400

@app.route('/delete_data', methods=['POST'])
def delete_data():
    """API untuk menghapus data log berdasarkan ID."""
    data = request.get_json()
    log_id = data.get('id')
    
    if not log_id:
        return jsonify({"status": "error", "message": "ID log tidak diberikan"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM rain_logs WHERE id = %s", (log_id,))
        conn.commit()
        deleted_rows = cur.rowcount
        cur.close()
        conn.close()
        
        if deleted_rows > 0:
            return jsonify({"status": "success", "deleted_id": log_id})
        else:
            return jsonify({"status": "error", "message": f"Log dengan ID {log_id} tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_multiple', methods=['POST'])
def delete_multiple():
    """API untuk menghapus beberapa data log berdasarkan array ID."""
    data = request.get_json()
    ids = data.get('ids', [])
    
    if not ids or not isinstance(ids, list):
        return jsonify({"status": "error", "message": "Array ID tidak valid"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Gunakan parameterized query untuk keamanan
        placeholders = ','.join(['%s'] * len(ids))
        query = f"DELETE FROM rain_logs WHERE id IN ({placeholders})"
        cur.execute(query, ids)
        
        deleted_rows = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "status": "success", 
            "deleted_count": deleted_rows,
            "deleted_ids": ids
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_all', methods=['POST'])
def delete_all():
    """API untuk menghapus semua data log."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Hitung jumlah record sebelum dihapus
        cur.execute("SELECT COUNT(*) FROM rain_logs")
        total_records = cur.fetchone()[0]
        
        # Hapus semua data
        cur.execute("DELETE FROM rain_logs")
        
        # Reset sequence untuk auto-increment
        cur.execute("ALTER SEQUENCE rain_logs_id_seq RESTART WITH 1")
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "status": "success", 
            "deleted_count": total_records,
            "message": f"Semua {total_records} record berhasil dihapus"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """API untuk mendapatkan statistik data."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Total records
        cur.execute("SELECT COUNT(*) FROM rain_logs")
        total_records = cur.fetchone()[0]
        
        # Records hari ini
        cur.execute("SELECT COUNT(*) FROM rain_logs WHERE DATE(log_time) = CURRENT_DATE")
        today_records = cur.fetchone()[0]
        
        # Jumlah status hujan dan cerah hari ini
        cur.execute("""
            SELECT 
                SUM(CASE WHEN is_raining = true THEN 1 ELSE 0 END) as hujan_count,
                SUM(CASE WHEN is_raining = false THEN 1 ELSE 0 END) as cerah_count
            FROM rain_logs 
            WHERE DATE(log_time) = CURRENT_DATE
        """)
        weather_stats = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return jsonify({
            "total_records": total_records,
            "today_records": today_records,
            "today_weather": {
                "hujan": weather_stats[0] or 0,
                "cerah": weather_stats[1] or 0
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==============================================================================
# --- EKSEKUSI UTAMA ---
# ==============================================================================

if __name__ == '__main__':
    connect_to_arduino()
    
    listener_thread = threading.Thread(target=arduino_listener, daemon=True)
    listener_thread.start()
    
    print("Server Flask berjalan di http://127.0.0.1:5000")
    print("Versi ini akan mencatat data ke database secara terus-menerus.")
    print("Fitur baru: Delete multiple, Delete all, dan Statistics API")
    print("Pastikan Anda sudah menutup Serial Monitor di VS Code!")
    app.run(host='0.0.0.0', port=5000)