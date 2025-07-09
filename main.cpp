/**
 * @file main.cpp
 * @brief Firmware untuk Sistem Jemuran Otomatis (Versi Perbaikan Logika)
 * @details
 * - Memperbaiki logika sensor hujan yang mungkin terbalik.
 * - Memperbaiki logika kontrol untuk relay tipe Active-LOW.
 */

#include <Arduino.h>

// --- Konfigurasi Pin ---
const int RAIN_SENSOR_PIN = A0;
const int RELAY_PIN = 7;

// --- Konfigurasi Logika ---
// Threshold untuk sensor hujan. Anda mungkin perlu mengkalibrasi nilai ini.
// Cara kalibrasi:
// 1. Buka Serial Monitor (di VS Code atau Arduino IDE).
// 2. Lihat angka yang muncul saat sensor benar-benar KERING (misal: 950).
// 3. Lihat angka yang muncul saat sensor BASAH (misal: 400).
// 4. Atur threshold di antara kedua nilai itu, misal 700.
const int RAIN_THRESHOLD = 700; 

bool autoMode = true; 

void setup() {
  Serial.begin(9600);
  pinMode(RELAY_PIN, OUTPUT);
  
  // =================================================================
  // PERBAIKAN 1: Logika Relay (Active-LOW)
  // Kondisi awal relay di-set ke HIGH, yang berarti "MATI" untuk relay active-low.
  // =================================================================
  digitalWrite(RELAY_PIN, HIGH); 
}

void loop() {
  // Mendengarkan Perintah dari Python
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "MODE_AUTO") {
      autoMode = true;
      Serial.println("ACK: Mode Otomatis Aktif");
    } else if (command == "MODE_MANUAL") {
      autoMode = false;
      Serial.println("ACK: Mode Manual Aktif");
    } else if (command == "MANUAL_ON") {
      if (!autoMode) {
        // PERBAIKAN 2: Logika Relay
        // Untuk menyalakan (ON), kirim sinyal LOW.
        digitalWrite(RELAY_PIN, LOW);
        Serial.println("ACK: Relay ON (Manual)");
      }
    } else if (command == "MANUAL_OFF") {
      if (!autoMode) {
        // PERBAIKAN 3: Logika Relay
        // Untuk mematikan (OFF), kirim sinyal HIGH.
        digitalWrite(RELAY_PIN, HIGH);
        Serial.println("ACK: Relay OFF (Manual)");
      }
    }
  }

  // Logika Mode Otomatis
  if (autoMode) {
    int rainValue = analogRead(RAIN_SENSOR_PIN);
    
    static unsigned long lastSendTime = 0;
    if (millis() - lastSendTime > 2000) {
      
      // =================================================================
      // PERBAIKAN 4: Logika Sensor
      // Kondisi '<' dibalik menjadi '>'. Jika ini masih salah, 
      // berarti wiring atau sensor Anda bermasalah, atau threshold perlu dikalibrasi.
      // Jika nilai sensor LEBIH BESAR dari threshold, anggap kering/cerah.
      // =================================================================
      if (rainValue > RAIN_THRESHOLD) {
        Serial.println("STATUS:CERAH");
        // Relay MATI saat cerah (kirim sinyal HIGH)
        digitalWrite(RELAY_PIN, HIGH);
      } else {
        Serial.println("STATUS:HUJAN");
        // Relay NYALA saat hujan (kirim sinyal LOW)
        digitalWrite(RELAY_PIN, LOW);
      }
      lastSendTime = millis();
    }
  }

  delay(100); 
}
