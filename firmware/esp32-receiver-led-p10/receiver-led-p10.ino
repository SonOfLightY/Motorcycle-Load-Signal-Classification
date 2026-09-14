#ifndef ARDUINO_ARCH_ESP32
#error "Pilih board ESP32 di Tools → Board. Kode ini hanya untuk ESP32."
#endif

#include <Arduino.h>
#include <SPI.h>
#include <WiFi.h>
#include <esp_now.h>
#include "esp_wifi.h"
#include <DMD32.h>
#include <string.h>

// =======================================================
// PANEL HUB12 P10 32x16
// =======================================================
#define DISPLAYS_ACROSS 1
#define DISPLAYS_DOWN   1

#define PANEL_W   (32 * DISPLAYS_ACROSS)
#define PANEL_H   (16 * DISPLAYS_DOWN)

// =======================================================
// PIN HUB12 KE ESP32
// =======================================================
#define PIN_MOSI 23
#define PIN_SCK  18
#define PIN_LAT   2
#define PIN_OE   22
#define PIN_A    19
#define PIN_B    21

DMD dmd(DISPLAYS_ACROSS, DISPLAYS_DOWN);

// =======================================================
// STRUKTUR DATA ESP-NOW
// HARUS SAMA DENGAN STRUKTUR DI ESP32-S3 PENGIRIM
// =======================================================
typedef struct struct_message {
  int occupiedSlot;
  int totalSlot;
  char lastClass[16];
  char direction[12];
} struct_message;

struct_message receivedData;

// =======================================================
// VARIABEL DISPLAY
// =======================================================
volatile bool hasNewData = false;

int shownOccupiedSlot = 0;
int shownTotalSlot = 200;

char shownClass[16] = "start";
char shownDirection[12] = "none";

// =======================================================
// FONT MINI 3x5
// Digunakan agar teks seperti 0/200 atau 200/200 muat di P10 32x16
// =======================================================
const byte FONT_3x5_DIGITS[10][5] = {
  {0b111, 0b101, 0b101, 0b101, 0b111},
  {0b010, 0b110, 0b010, 0b010, 0b111},
  {0b111, 0b001, 0b111, 0b100, 0b111},
  {0b111, 0b001, 0b111, 0b001, 0b111},
  {0b101, 0b101, 0b111, 0b001, 0b001},
  {0b111, 0b100, 0b111, 0b001, 0b111},
  {0b111, 0b100, 0b111, 0b101, 0b111},
  {0b111, 0b001, 0b001, 0b001, 0b001},
  {0b111, 0b101, 0b111, 0b101, 0b111},
  {0b111, 0b101, 0b111, 0b001, 0b111}
};

const byte FONT_3x5_SLASH[5] = {
  0b001,
  0b001,
  0b010,
  0b100,
  0b100
};

// =======================================================
// GAMBAR PIXEL AMAN
// =======================================================
void drawPixelSafe(int x, int y) {
  if (x < 0 || x >= PANEL_W || y < 0 || y >= PANEL_H) {
    return;
  }

  dmd.writePixel(x, y, GRAPHICS_NORMAL, 1);
}

// =======================================================
// GAMBAR KARAKTER MINI
// =======================================================
void drawTinyChar(int x, int y, char c) {
  if (c >= '0' && c <= '9') {
    int digit = c - '0';

    for (int row = 0; row < 5; row++) {
      byte pattern = FONT_3x5_DIGITS[digit][row];

      for (int col = 0; col < 3; col++) {
        if (pattern & (1 << (2 - col))) {
          drawPixelSafe(x + col, y + row);
        }
      }
    }
  } else if (c == '/') {
    for (int row = 0; row < 5; row++) {
      byte pattern = FONT_3x5_SLASH[row];

      for (int col = 0; col < 3; col++) {
        if (pattern & (1 << (2 - col))) {
          drawPixelSafe(x + col, y + row);
        }
      }
    }
  }
}

// =======================================================
// HITUNG LEBAR TEKS MINI
// =======================================================
int tinyTextWidth(const char *text) {
  int len = strlen(text);

  if (len == 0) {
    return 0;
  }

  return (len * 4) - 1;
}

// =======================================================
// RENDER JUMLAH TERISI KE LED P10
// Format tampilan: occupiedSlot/totalSlot
// Contoh: 0/200, 1/200, 200/200
// =======================================================
void renderCapacity(int occupiedSlot, int totalSlot) {
  char text[16];

  snprintf(text, sizeof(text), "%d/%d", occupiedSlot, totalSlot);

  dmd.clearScreen(true);

  int textW = tinyTextWidth(text);
  int x = (PANEL_W - textW) / 2;
  int y = 5;

  if (x < 0) {
    x = 0;
  }

  for (int i = 0; i < strlen(text); i++) {
    drawTinyChar(x + (i * 4), y, text[i]);
  }
}

// =======================================================
// CALLBACK RECEIVE ESP-NOW
// =======================================================
void onDataRecv(const esp_now_recv_info_t *info, const uint8_t *incomingData, int len) {
  if (len != sizeof(receivedData)) {
    Serial.println("Ukuran data tidak sesuai, data diabaikan.");
    Serial.print("Len diterima : ");
    Serial.println(len);
    Serial.print("Len standar  : ");
    Serial.println(sizeof(receivedData));
    return;
  }

  memcpy(&receivedData, incomingData, sizeof(receivedData));

  shownOccupiedSlot = receivedData.occupiedSlot;
  shownTotalSlot = receivedData.totalSlot;

  strncpy(shownClass, receivedData.lastClass, sizeof(shownClass));
  shownClass[sizeof(shownClass) - 1] = '\0';

  strncpy(shownDirection, receivedData.direction, sizeof(shownDirection));
  shownDirection[sizeof(shownDirection) - 1] = '\0';

  hasNewData = true;

  Serial.println();
  Serial.println("======================================");
  Serial.println("DATA DITERIMA DARI ESP32-S3");
  Serial.println("======================================");

  Serial.print("Occupied Slot  : ");
  Serial.println(shownOccupiedSlot);

  Serial.print("Total Slot     : ");
  Serial.println(shownTotalSlot);

  Serial.print("Display        : ");
  Serial.print(shownOccupiedSlot);
  Serial.print("/");
  Serial.println(shownTotalSlot);

  Serial.print("Last Class     : ");
  Serial.println(shownClass);

  Serial.print("Direction      : ");
  Serial.println(shownDirection);

  Serial.println("======================================");
}

// =======================================================
// SETUP ESP-NOW
// =======================================================
void setupEspNow() {
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);

  esp_wifi_set_channel(1, WIFI_SECOND_CHAN_NONE);

  Serial.print("MAC Address ESP32 LED P10 Receiver: ");
  Serial.println(WiFi.macAddress());

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW gagal diinisialisasi.");
    return;
  }

  esp_now_register_recv_cb(onDataRecv);

  Serial.println("ESP-NOW receiver siap.");
  Serial.println("Gunakan MAC ini pada kode ESP32-S3:");
  Serial.println(WiFi.macAddress());
}

// =======================================================
// SETUP LED P10
// =======================================================
void setupP10() {
  SPI.end();
  SPI.begin(PIN_SCK, -1, PIN_MOSI, PIN_LAT);

  pinMode(PIN_LAT, OUTPUT);
  pinMode(PIN_OE, OUTPUT);
  pinMode(PIN_A, OUTPUT);
  pinMode(PIN_B, OUTPUT);

  dmd.clearScreen(true);

  renderCapacity(shownOccupiedSlot, shownTotalSlot);
}

// =======================================================
// SETUP UTAMA
// =======================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("======================================");
  Serial.println("ESP32 LED P10 RECEIVER NODE FINAL");
  Serial.println("ESP-NOW + LED P10 Display");
  Serial.println("Mode tampilan: jumlah terisi / total slot");
  Serial.println("======================================");

  setupP10();
  setupEspNow();

  Serial.println();
  Serial.println("Tampilan awal:");
  Serial.print(shownOccupiedSlot);
  Serial.print("/");
  Serial.println(shownTotalSlot);
}

// =======================================================
// LOOP UTAMA
// =======================================================
void loop() {
  dmd.scanDisplayBySPI();

  if (hasNewData) {
    hasNewData = false;

    renderCapacity(shownOccupiedSlot, shownTotalSlot);

    Serial.print("Update LED P10: ");
    Serial.print(shownOccupiedSlot);
    Serial.print("/");
    Serial.println(shownTotalSlot);
  }

  delayMicroseconds(500);
}
