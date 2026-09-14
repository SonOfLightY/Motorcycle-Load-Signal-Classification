// Library
#include <WiFi.h>
#include <esp_now.h>
#include "esp_wifi.h"
#include <Preferences.h>
#include "HX711.h"
#include <math.h>

// Pin Komponen 
#define HX711_DT   41
#define HX711_SCK  42
#define TRIG_1 1
#define ECHO_1 2
#define TRIG_2 4
#define ECHO_2 5

// Objek Global
HX711 scale;
Preferences preferences;

/* MAC ADDRESS ESP32 LED P10 RECEIVER: 78:42:1C:6C:76:B4 */
uint8_t displayAddress[] = {0x78, 0x42, 0x1C, 0x6C, 0x76, 0xB4};

// STRUKTUR DATA ESP-NOW
typedef struct struct_message {
   int occupiedSlot;
   int totalSlot;
   char lastClass[16];
   char direction[12];
} struct_message;

struct_message parkingData;

// =====================================================
// KAPASITAS PARKIR
// =====================================================
const int TOTAL_SLOT = 200;
int occupiedSlot = 0;



// =====================================================
// PARAMETER PEMBACAAN SENSOR
// =====================================================
const unsigned long READ_INTERVAL_MS = 100;
unsigned long lastReadTime = 0;

// =====================================================
// PARAMETER BUFFER DAN BASELINE
// =====================================================
const int BASELINE_SAMPLE_COUNT = 10;
const int POST_CLEAR_SAMPLE_COUNT = 10;

long preEventRawBuffer[BASELINE_SAMPLE_COUNT];
unsigned long preEventTimeBuffer[BASELINE_SAMPLE_COUNT];

int preEventBufferIndex = 0;
int preEventBufferCount = 0;

long postClearRawBuffer[POST_CLEAR_SAMPLE_COUNT];
unsigned long postClearTimeBuffer[POST_CLEAR_SAMPLE_COUNT];

int postClearCount = 0;

// =====================================================
// PARAMETER THRESHOLD HASIL TRAINING
// =====================================================
const float GLOBAL_NOISE_THRESHOLD = 1941.597;
const float SIGMA_MULTIPLIER = 3.0;

float baselineMean = 0.0;
float baselineStd = 0.0;
float thresholdEvent = 0.0;

// =====================================================
// PARAMETER ULTRASONIK
// Objek dianggap terbaca jika 5 cm <= jarak < 100 cm
// =====================================================
const float ULTRASONIC_MIN_VALID_CM = 5.0;
const float ULTRASONIC_MAX_VALID_CM = 100.0;

const int ULTRASONIC_CLEAR_CONSECUTIVE = 3;
int ultrasonicClearCount = 0;

bool latestUltra1Active = false;
bool latestUltra2Active = false;

// =====================================================
// STATE SISTEM
// =====================================================
enum SystemState {
  STATE_IDLE,
  STATE_EVENT_WINDOW,
  STATE_POST_CLEAR_CAPTURE
};

SystemState systemState = STATE_IDLE;

// =====================================================
// DATA EVENT
// =====================================================
bool eventUltra1Seen = false;
bool eventUltra2Seen = false;

unsigned long eventUltra1Time = 0;
unsigned long eventUltra2Time = 0;
unsigned long eventWindowStartTime = 0;
unsigned long eventWindowClearTime = 0;

String eventDirection = "unknown";

float eventBaselineMean = 0.0;
float eventBaselineStd = 0.0;
float eventThreshold = 0.0;

bool eventLoadValid = false;

unsigned long firstAboveThresholdTime = 0;
unsigned long lastAboveThresholdTime = 0;

int featureSampleCount = 0;

double eventSumDelta = 0.0;
double eventSumSqDelta = 0.0;

float eventMinDelta = 0.0;
float eventMaxDelta = 0.0;

double eventSumIntervalMs = 0.0;
int eventIntervalCount = 0;

unsigned long eventPrevRawTime = 0;

int eventRawCount = 0;

const unsigned long MAX_EVENT_WINDOW_MS = 15000;
const unsigned long MAX_POST_CAPTURE_MS = 3000;
unsigned long postCaptureStartTime = 0;

// =====================================================
// PARAMETER SISTEM
// =====================================================
const bool INVERT_RAW = true;
const bool IGNORE_ZERO_RAW = true;

// =====================================================
// PROTOTYPE
// =====================================================
void setupEspNow();
void calculateStartupBaseline();
void sendParkingData(String classResult, String directionResult);
void handleSerialCommand();

bool readHX711Raw(long &rawValue);
float readUltrasonicCM(int trigPin, int echoPin);
void updateUltrasonicState();

void pushPreEventRaw(long rawValue, unsigned long sampleTime);
void computePreEventBaseline();
void computePostClearBaseline(float &postMean, float &postStd);

void startEventWindow(unsigned long now);
void processEventRaw(long rawValue, unsigned long sampleTime);
void startPostClearCapture(unsigned long now);
void processPostClearRaw(long rawValue, unsigned long sampleTime);
void finishEventWindow();
void cancelEventWindow(String reason);

void resetEventData();
String getEventDirection();
String getStateName();

String predictDecisionTree(float meanDeltaRaw, float durationMs);
void updateOccupiedSlot(String prediction, String directionResult);

// =====================================================
// CALLBACK ESP-NOW SEND
// =====================================================
void onDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
  Serial.print("Status kirim ESP-NOW: ");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "BERHASIL" : "GAGAL");
}

// =====================================================
// BACA RAW HX711
// =====================================================
bool readHX711Raw(long &rawValue) {
  if (!scale.is_ready()) {
    return false;
  }

  long raw = scale.read();

  if (INVERT_RAW) {
    raw = raw * -1;
  }

  rawValue = raw;
  return true;
}

// =====================================================
// BACA ULTRASONIK
// =====================================================
float readUltrasonicCM(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000);

  if (duration == 0) {
    return -1;
  }

  float distance = duration * 0.0343 / 2.0;
  return distance;
}

// =====================================================
// UPDATE STATUS ULTRASONIK
// =====================================================
void updateUltrasonicState() {
  float distance1 = readUltrasonicCM(TRIG_1, ECHO_1);
  float distance2 = readUltrasonicCM(TRIG_2, ECHO_2);

  unsigned long now = millis();

  latestUltra1Active = distance1 >= ULTRASONIC_MIN_VALID_CM && distance1 < ULTRASONIC_MAX_VALID_CM;
  latestUltra2Active = distance2 >= ULTRASONIC_MIN_VALID_CM && distance2 < ULTRASONIC_MAX_VALID_CM;

  if (latestUltra1Active) {
    Serial.print("Ultrasonik 1 aktif, jarak: ");
    Serial.println(distance1);
  }

  if (latestUltra2Active) {
    Serial.print("Ultrasonik 2 aktif, jarak: ");
    Serial.println(distance2);
  }

  bool anyUltrasonicActive = latestUltra1Active || latestUltra2Active;
  bool bothUltrasonicClear = !latestUltra1Active && !latestUltra2Active;

  if (systemState == STATE_IDLE && anyUltrasonicActive) {
    startEventWindow(now);
  }

  if (systemState == STATE_EVENT_WINDOW) {
    if (latestUltra1Active && !eventUltra1Seen) {
      eventUltra1Seen = true;
      eventUltra1Time = now;
      Serial.println("Event mencatat Ultrasonik 1.");
    }

    if (latestUltra2Active && !eventUltra2Seen) {
      eventUltra2Seen = true;
      eventUltra2Time = now;
      Serial.println("Event mencatat Ultrasonik 2.");
    }

    if (eventDirection == "unknown") {
      eventDirection = getEventDirection();

      if (eventDirection != "unknown") {
        Serial.print("Arah event terbaca: ");
        Serial.println(eventDirection);
      }
    }

    if (bothUltrasonicClear) {
      ultrasonicClearCount++;
    } else {
      ultrasonicClearCount = 0;
    }

    if (ultrasonicClearCount >= ULTRASONIC_CLEAR_CONSECUTIVE) {
      startPostClearCapture(now);
    }
  }
}

// =====================================================
// SIMPAN 10 RAW TERAKHIR SAAT IDLE
// =====================================================
void pushPreEventRaw(long rawValue, unsigned long sampleTime) {
  preEventRawBuffer[preEventBufferIndex] = rawValue;
  preEventTimeBuffer[preEventBufferIndex] = sampleTime;

  preEventBufferIndex++;

  if (preEventBufferIndex >= BASELINE_SAMPLE_COUNT) {
    preEventBufferIndex = 0;
  }

  if (preEventBufferCount < BASELINE_SAMPLE_COUNT) {
    preEventBufferCount++;
  }
}

// =====================================================
// HITUNG BASELINE DARI 10 RAW SEBELUM ULTRASONIK AKTIF
// =====================================================
void computePreEventBaseline() {
  if (preEventBufferCount <= 0) {
    eventBaselineMean = baselineMean;
    eventBaselineStd = baselineStd;
    eventThreshold = thresholdEvent;
    return;
  }

  double sum = 0.0;

  for (int i = 0; i < preEventBufferCount; i++) {
    sum += preEventRawBuffer[i];
  }

  eventBaselineMean = sum / preEventBufferCount;

  double sumSq = 0.0;

  for (int i = 0; i < preEventBufferCount; i++) {
    double diff = preEventRawBuffer[i] - eventBaselineMean;
    sumSq += diff * diff;
  }

  eventBaselineStd = sqrt(sumSq / preEventBufferCount);

  float localThreshold = SIGMA_MULTIPLIER * eventBaselineStd;

  if (localThreshold > GLOBAL_NOISE_THRESHOLD) {
    eventThreshold = localThreshold;
  } else {
    eventThreshold = GLOBAL_NOISE_THRESHOLD;
  }

  baselineMean = eventBaselineMean;
  baselineStd = eventBaselineStd;
  thresholdEvent = eventThreshold;
}

// =====================================================
// HITUNG BASELINE AKHIR DARI 10 RAW SETELAH ULTRASONIK CLEAR
// =====================================================
void computePostClearBaseline(float &postMean, float &postStd) {
  if (postClearCount <= 0) {
    postMean = baselineMean;
    postStd = baselineStd;
    return;
  }

  double sum = 0.0;

  for (int i = 0; i < postClearCount; i++) {
    sum += postClearRawBuffer[i];
  }

  postMean = sum / postClearCount;

  double sumSq = 0.0;

  for (int i = 0; i < postClearCount; i++) {
    double diff = postClearRawBuffer[i] - postMean;
    sumSq += diff * diff;
  }

  postStd = sqrt(sumSq / postClearCount);
}

// =====================================================
// MULAI EVENT WINDOW SAAT ULTRASONIK PERTAMA AKTIF
// =====================================================
void startEventWindow(unsigned long now) {
  resetEventData();

  systemState = STATE_EVENT_WINDOW;
  eventWindowStartTime = now;

  computePreEventBaseline();

  if (latestUltra1Active) {
    eventUltra1Seen = true;
    eventUltra1Time = now;
  }

  if (latestUltra2Active) {
    eventUltra2Seen = true;
    eventUltra2Time = now;
  }

  eventDirection = getEventDirection();

  Serial.println();
  Serial.println("======================================");
  Serial.println(">>> EVENT WINDOW DIMULAI OLEH ULTRASONIK");
  Serial.println("======================================");

  Serial.print("Baseline awal event : ");
  Serial.println(eventBaselineMean, 2);

  Serial.print("Std baseline awal   : ");
  Serial.println(eventBaselineStd, 2);

  Serial.print("Threshold event     : ");
  Serial.println(eventThreshold, 2);

  Serial.print("Arah awal           : ");
  Serial.println(eventDirection);

  Serial.println("======================================");
}

// =====================================================
// PROSES RAW LOAD CELL SELAMA EVENT WINDOW
// =====================================================
void processEventRaw(long rawValue, unsigned long sampleTime) {
  float delta = fabs((float)rawValue - eventBaselineMean);

  eventRawCount++;

  if (eventRawCount > 1) {
    unsigned long interval = sampleTime - eventPrevRawTime;
    eventSumIntervalMs += interval;
    eventIntervalCount++;
  }

  eventPrevRawTime = sampleTime;

  bool aboveThreshold = delta > eventThreshold;

  if (aboveThreshold) {
    if (!eventLoadValid) {
      eventLoadValid = true;
      firstAboveThresholdTime = sampleTime;

      eventMinDelta = delta;
      eventMaxDelta = delta;

      Serial.println("Load cell valid: delta pertama kali melewati threshold.");
    }

    lastAboveThresholdTime = sampleTime;

    if (delta < eventMinDelta) {
      eventMinDelta = delta;
    }

    if (delta > eventMaxDelta) {
      eventMaxDelta = delta;
    }

    eventSumDelta += delta;
    eventSumSqDelta += (double)delta * (double)delta;
    featureSampleCount++;
  }

  Serial.print("raw=");
  Serial.print(rawValue);

  Serial.print(", baselineEvent=");
  Serial.print(eventBaselineMean, 2);

  Serial.print(", delta=");
  Serial.print(delta, 2);

  Serial.print(", threshold=");
  Serial.print(eventThreshold, 2);

  Serial.print(", above=");
  Serial.print(aboveThreshold ? "YES" : "NO");

  Serial.print(", state=");
  Serial.println(getStateName());
}

// =====================================================
// MULAI AMBIL 10 RAW SETELAH ULTRASONIK CLEAR
// =====================================================
void startPostClearCapture(unsigned long now) {
  systemState = STATE_POST_CLEAR_CAPTURE;
  postCaptureStartTime = now;
  eventWindowClearTime = now;
  postClearCount = 0;

  Serial.println();
  Serial.println(">>> ULTRASONIK CLEAR");
  Serial.println("Mulai mengambil 10 raw setelah clear untuk baseline akhir.");
}

// =====================================================
// PROSES 10 RAW SETELAH ULTRASONIK CLEAR
// =====================================================
void processPostClearRaw(long rawValue, unsigned long sampleTime) {
  if (postClearCount < POST_CLEAR_SAMPLE_COUNT) {
    postClearRawBuffer[postClearCount] = rawValue;
    postClearTimeBuffer[postClearCount] = sampleTime;

    postClearCount++;

    Serial.print("Post-clear raw ");
    Serial.print(postClearCount);
    Serial.print("/");
    Serial.print(POST_CLEAR_SAMPLE_COUNT);
    Serial.print(" : ");
    Serial.println(rawValue);
  }

  if (postClearCount >= POST_CLEAR_SAMPLE_COUNT) {
    finishEventWindow();
  }
}

// =====================================================
// BATALKAN EVENT WINDOW
// =====================================================
void cancelEventWindow(String reason) {
  Serial.println();
  Serial.println("======================================");
  Serial.println("EVENT DIBATALKAN");
  Serial.println("======================================");
  Serial.print("Penyebab: ");
  Serial.println(reason);
  Serial.println("Objek tidak diklasifikasikan.");
  Serial.println("======================================");

  sendParkingData("invalid", "none");

  resetEventData();
  systemState = STATE_IDLE;
}

// =====================================================
// SELESAIKAN EVENT WINDOW DAN KLASIFIKASI
// =====================================================
void finishEventWindow() {
  float postBaselineMean = 0.0;
  float postBaselineStd = 0.0;

  computePostClearBaseline(postBaselineMean, postBaselineStd);

  float postDeltaFromStartBaseline = fabs(postBaselineMean - eventBaselineMean);

  Serial.println();
  Serial.println("======================================");
  Serial.println("EVENT WINDOW SELESAI");
  Serial.println("======================================");

  Serial.print("Baseline awal        : ");
  Serial.println(eventBaselineMean, 2);

  Serial.print("Baseline akhir       : ");
  Serial.println(postBaselineMean, 2);

  Serial.print("Delta baseline akhir : ");
  Serial.println(postDeltaFromStartBaseline, 2);

  Serial.print("Threshold event      : ");
  Serial.println(eventThreshold, 2);

  if (postDeltaFromStartBaseline <= eventThreshold) {
    Serial.println("Status akhir         : stabil / kembali di bawah threshold");
  } else {
    Serial.println("Status akhir         : ada offset sisa, baseline akhir disimpan sebagai referensi baru");
  }

  if (!eventLoadValid || featureSampleCount <= 0) {
    Serial.println();
    Serial.println("EVENT TIDAK VALID");
    Serial.println("Penyebab: Ultrasonik mendeteksi objek, tetapi load cell tidak melewati threshold.");
    Serial.println("Objek dianggap tidak menginjak platform atau bukan objek valid.");

    baselineMean = postBaselineMean;
    baselineStd = postBaselineStd;

    float localThreshold = SIGMA_MULTIPLIER * baselineStd;

    if (localThreshold > GLOBAL_NOISE_THRESHOLD) {
      thresholdEvent = localThreshold;
    } else {
      thresholdEvent = GLOBAL_NOISE_THRESHOLD;
    }

    for (int i = 0; i < postClearCount; i++) {
      pushPreEventRaw(postClearRawBuffer[i], postClearTimeBuffer[i]);
    }

    sendParkingData("invalid", "none");

    resetEventData();
    systemState = STATE_IDLE;
    return;
  }

  float meanDeltaRaw = eventSumDelta / featureSampleCount;

  double varianceDeltaRaw = (eventSumSqDelta / featureSampleCount) - ((double)meanDeltaRaw * (double)meanDeltaRaw);

  if (varianceDeltaRaw < 0) {
    varianceDeltaRaw = 0;
  }

  float stdDeltaRaw = sqrt(varianceDeltaRaw);
  float rangeDeltaRaw = eventMaxDelta - eventMinDelta;

  float averageIntervalMs = READ_INTERVAL_MS;

  if (eventIntervalCount > 0) {
    averageIntervalMs = eventSumIntervalMs / eventIntervalCount;
  }

  float durationMs = (lastAboveThresholdTime - firstAboveThresholdTime) + averageIntervalMs;

  String prediction = predictDecisionTree(meanDeltaRaw, durationMs);
  String directionResult = eventDirection;

  Serial.println();
  Serial.println("======================================");
  Serial.println("HASIL EVENT");
  Serial.println("======================================");

  Serial.print("eventRawCount        : ");
  Serial.println(eventRawCount);

  Serial.print("featureSampleCount   : ");
  Serial.println(featureSampleCount);

  Serial.print("mean_delta_raw       : ");
  Serial.println(meanDeltaRaw, 2);

  Serial.print("max_delta_raw        : ");
  Serial.println(eventMaxDelta, 2);

  Serial.print("min_delta_raw        : ");
  Serial.println(eventMinDelta, 2);

  Serial.print("variance_delta_raw   : ");
  Serial.printf("%.2f\n", varianceDeltaRaw);

  Serial.print("std_delta_raw        : ");
  Serial.println(stdDeltaRaw, 2);

  Serial.print("range_delta_raw      : ");
  Serial.println(rangeDeltaRaw, 2);

  Serial.print("avg_interval_ms      : ");
  Serial.println(averageIntervalMs, 2);

  Serial.print("duration_ms          : ");
  Serial.println(durationMs, 2);

  Serial.print("Prediksi             : ");
  Serial.println(prediction);

  Serial.print("Arah                 : ");
  Serial.println(directionResult);

  Serial.print("Jumlah terisi sebelum: ");
  Serial.print(occupiedSlot);
  Serial.print("/");
  Serial.println(TOTAL_SLOT);

  updateOccupiedSlot(prediction, directionResult);

  Serial.print("Jumlah terisi sekarang: ");
  Serial.print(occupiedSlot);
  Serial.print("/");
  Serial.println(TOTAL_SLOT);

  Serial.println("======================================");

  sendParkingData(prediction, directionResult);

  baselineMean = postBaselineMean;
  baselineStd = postBaselineStd;

  float localThreshold = SIGMA_MULTIPLIER * baselineStd;

  if (localThreshold > GLOBAL_NOISE_THRESHOLD) {
    thresholdEvent = localThreshold;
  } else {
    thresholdEvent = GLOBAL_NOISE_THRESHOLD;
  }

  for (int i = 0; i < postClearCount; i++) {
    pushPreEventRaw(postClearRawBuffer[i], postClearTimeBuffer[i]);
  }

  resetEventData();
  systemState = STATE_IDLE;
}

// =====================================================
// RESET DATA EVENT
// =====================================================
void resetEventData() {
  eventUltra1Seen = false;
  eventUltra2Seen = false;

  eventUltra1Time = 0;
  eventUltra2Time = 0;
  eventWindowStartTime = 0;
  eventWindowClearTime = 0;

  eventDirection = "unknown";

  eventBaselineMean = 0.0;
  eventBaselineStd = 0.0;
  eventThreshold = GLOBAL_NOISE_THRESHOLD;

  eventLoadValid = false;

  firstAboveThresholdTime = 0;
  lastAboveThresholdTime = 0;

  featureSampleCount = 0;

  eventSumDelta = 0.0;
  eventSumSqDelta = 0.0;

  eventMinDelta = 0.0;
  eventMaxDelta = 0.0;

  eventSumIntervalMs = 0.0;
  eventIntervalCount = 0;

  eventPrevRawTime = 0;
  eventRawCount = 0;

  postClearCount = 0;
  ultrasonicClearCount = 0;

  latestUltra1Active = false;
  latestUltra2Active = false;
}

// =====================================================
// TENTUKAN ARAH EVENT
// Jika arah terbalik saat uji nyata,
// tukar return "masuk" dan "keluar".
// =====================================================
String getEventDirection() {
  if (eventUltra1Seen && eventUltra2Seen) {
    if (eventUltra1Time < eventUltra2Time) {
      return "masuk";
    }

    if (eventUltra2Time < eventUltra1Time) {
      return "keluar";
    }
  }

  return "unknown";
}

// =====================================================
// NAMA STATE UNTUK SERIAL MONITOR
// =====================================================
String getStateName() {
  if (systemState == STATE_IDLE) {
    return "IDLE";
  }

  if (systemState == STATE_EVENT_WINDOW) {
    return "EVENT_WINDOW";
  }

  if (systemState == STATE_POST_CLEAR_CAPTURE) {
    return "POST_CLEAR_CAPTURE";
  }

  return "UNKNOWN";
}

// =====================================================
// DECISION TREE HASIL COLAB
// =====================================================
String predictDecisionTree(float meanDeltaRaw, float durationMs) {
  Serial.println();
  Serial.println("RULE DECISION TREE");

  if (meanDeltaRaw <= 265535.88) {
    Serial.println("mean_delta_raw <= 265535.88");

    if (durationMs <= 2375.50) {
      Serial.println("duration_ms <= 2375.50");
      Serial.println("Rule result: motor");
      return "motor";
    } else {
      Serial.println("duration_ms > 2375.50");

      if (durationMs <= 2675.00) {
        Serial.println("duration_ms <= 2675.00");
        Serial.println("Rule result: non_motor");
        return "non_motor";
      } else {
        Serial.println("duration_ms > 2675.00");
        Serial.println("Rule result: motor");
        return "motor";
      }
    }
  } else {
    Serial.println("mean_delta_raw > 265535.88");

    if (durationMs <= 849.00) {
      Serial.println("duration_ms <= 849.00");
      Serial.println("Rule result: motor");
      return "motor";
    } else {
      Serial.println("duration_ms > 849.00");
      Serial.println("Rule result: non_motor");
      return "non_motor";
    }
  }
}

// =====================================================
// UPDATE JUMLAH SLOT TERISI
// =====================================================
void updateOccupiedSlot(String prediction, String directionResult) {
  if (prediction != "motor") {
    Serial.println("Objek non_motor, jumlah terisi tidak berubah.");
    return;
  }

  if (directionResult == "masuk") {
    if (occupiedSlot < TOTAL_SLOT) {
      occupiedSlot++;
      Serial.println("Motor masuk, jumlah terisi bertambah.");
    } else {
      Serial.println("Parkiran sudah penuh, jumlah terisi tidak ditambah.");
    }
  } else if (directionResult == "keluar") {
    if (occupiedSlot > 0) {
      occupiedSlot--;
      Serial.println("Motor keluar, jumlah terisi berkurang.");
    } else {
      Serial.println("Parkiran sudah kosong, jumlah terisi tidak dikurangi.");
    }
  } else {
    Serial.println("Arah unknown, jumlah terisi tidak berubah.");
    return;
  }

  preferences.putInt("occupied", occupiedSlot);
}

// =====================================================
// KIRIM DATA KE ESP32 LED P10
// =====================================================
void sendParkingData(String classResult, String directionResult) {
  parkingData.occupiedSlot = occupiedSlot;
  parkingData.totalSlot = TOTAL_SLOT;

  classResult.toCharArray(parkingData.lastClass, sizeof(parkingData.lastClass));
  directionResult.toCharArray(parkingData.direction, sizeof(parkingData.direction));

  Serial.println();
  Serial.println("======================================");
  Serial.println("KIRIM DATA KE ESP32 LED P10");
  Serial.println("======================================");

  Serial.print("Occupied Slot  : ");
  Serial.println(occupiedSlot);

  Serial.print("Total Slot     : ");
  Serial.println(parkingData.totalSlot);

  Serial.print("Display        : ");
  Serial.print(parkingData.occupiedSlot);
  Serial.print("/");
  Serial.println(parkingData.totalSlot);

  Serial.print("Last Class     : ");
  Serial.println(parkingData.lastClass);

  Serial.print("Direction      : ");
  Serial.println(parkingData.direction);

  esp_err_t result = esp_now_send(
    displayAddress,
    (uint8_t *) &parkingData,
    sizeof(parkingData)
  );

  if (result == ESP_OK) {
    Serial.println("esp_now_send() berhasil dipanggil.");
  } else {
    Serial.print("esp_now_send() gagal dipanggil. Kode error: ");
    Serial.println(result);
  }

  Serial.println("======================================");
}

// =====================================================
// SERIAL COMMAND
// SET 20    -> set jumlah terisi menjadi 20
// SHOW      -> tampilkan status
// RESET     -> set jumlah terisi menjadi 0
// BASELINE  -> baseline ulang manual saat kosong
// =====================================================
void handleSerialCommand() {
  if (!Serial.available()) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command.length() == 0) {
    return;
  }

  command.toUpperCase();

  if (command.startsWith("SET ")) {
    String valueText = command.substring(4);
    valueText.trim();

    int newValue = valueText.toInt();

    if (newValue < 0) {
      newValue = 0;
    }

    if (newValue > TOTAL_SLOT) {
      newValue = TOTAL_SLOT;
    }

    occupiedSlot = newValue;
    preferences.putInt("occupied", occupiedSlot);

    Serial.println();
    Serial.println("======================================");
    Serial.println("JUMLAH TERISI DIPERBARUI MANUAL");
    Serial.println("======================================");
    Serial.print("Occupied Slot baru : ");
    Serial.print(occupiedSlot);
    Serial.print("/");
    Serial.println(TOTAL_SLOT);
    Serial.println("Data sudah disimpan ke memori.");
    Serial.println("======================================");

    sendParkingData("manual", "set");
    return;
  }

  if (command == "SHOW") {
    Serial.println();
    Serial.println("======================================");
    Serial.println("STATUS SAAT INI");
    Serial.println("======================================");

    Serial.print("State         : ");
    Serial.println(getStateName());

    Serial.print("Occupied Slot : ");
    Serial.print(occupiedSlot);
    Serial.print("/");
    Serial.println(TOTAL_SLOT);

    Serial.print("baselineMean  : ");
    Serial.println(baselineMean, 2);

    Serial.print("baselineStd   : ");
    Serial.println(baselineStd, 2);

    Serial.print("threshold     : ");
    Serial.println(thresholdEvent, 2);

    Serial.print("preBufferCount: ");
    Serial.println(preEventBufferCount);

    Serial.println("======================================");
    return;
  }

  if (command == "RESET") {
    occupiedSlot = 0;
    preferences.putInt("occupied", occupiedSlot);

    Serial.println();
    Serial.println("======================================");
    Serial.println("JUMLAH TERISI DIRESET KE 0");
    Serial.println("======================================");

    sendParkingData("manual", "reset");
    return;
  }

  if (command == "BASELINE") {
    Serial.println();
    Serial.println("Baseline ulang manual dimulai.");
    Serial.println("Pastikan platform benar-benar kosong.");

    calculateStartupBaseline();
    return;
  }

  Serial.println();
  Serial.println("Perintah tidak dikenal.");
  Serial.println("Gunakan:");
  Serial.println("SET 20    -> mengatur jumlah terisi menjadi 20");
  Serial.println("SHOW      -> melihat status");
  Serial.println("RESET     -> mengatur jumlah terisi menjadi 0");
  Serial.println("BASELINE  -> baseline ulang manual saat platform kosong");
}

// =====================================================
// BASELINE AWAL SAAT STARTUP
// =====================================================
void calculateStartupBaseline() {
  Serial.println();
  Serial.println("======================================");
  Serial.println("KALIBRASI BASELINE STARTUP");
  Serial.println("Pastikan platform load cell kosong.");
  Serial.println("Mengambil 10 sampel baseline...");
  Serial.println("======================================");

  preEventBufferIndex = 0;
  preEventBufferCount = 0;

  long rawValues[BASELINE_SAMPLE_COUNT];
  int count = 0;

  while (count < BASELINE_SAMPLE_COUNT) {
    handleSerialCommand();

    long rawValue;

    if (readHX711Raw(rawValue)) {
      if (IGNORE_ZERO_RAW && rawValue == 0) {
        Serial.println("Baseline raw = 0, dilewati.");
      } else {
        rawValues[count] = rawValue;
        pushPreEventRaw(rawValue, millis());

        Serial.print("Baseline sample ");
        Serial.print(count + 1);
        Serial.print(" : ");
        Serial.println(rawValue);

        count++;
      }
    } else {
      Serial.println("HX711 belum siap saat baseline.");
    }

    delay(READ_INTERVAL_MS);
  }

  double sum = 0.0;

  for (int i = 0; i < BASELINE_SAMPLE_COUNT; i++) {
    sum += rawValues[i];
  }

  baselineMean = sum / BASELINE_SAMPLE_COUNT;

  double sumSq = 0.0;

  for (int i = 0; i < BASELINE_SAMPLE_COUNT; i++) {
    double diff = rawValues[i] - baselineMean;
    sumSq += diff * diff;
  }

  baselineStd = sqrt(sumSq / BASELINE_SAMPLE_COUNT);

  float localThreshold = SIGMA_MULTIPLIER * baselineStd;

  if (localThreshold > GLOBAL_NOISE_THRESHOLD) {
    thresholdEvent = localThreshold;
  } else {
    thresholdEvent = GLOBAL_NOISE_THRESHOLD;
  }

  Serial.println();
  Serial.println("HASIL BASELINE STARTUP");
  Serial.print("baselineMean    : ");
  Serial.println(baselineMean, 2);

  Serial.print("baselineStd     : ");
  Serial.println(baselineStd, 2);

  Serial.print("globalThreshold : ");
  Serial.println(GLOBAL_NOISE_THRESHOLD, 2);

  Serial.print("thresholdEvent  : ");
  Serial.println(thresholdEvent, 2);

  Serial.println("======================================");
  Serial.println("Sistem siap mendeteksi kendaraan.");
}

// =====================================================
// SETUP ESP-NOW
// =====================================================
void setupEspNow() {
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);

  esp_wifi_set_channel(1, WIFI_SECOND_CHAN_NONE);

  Serial.print("MAC Address ESP32-S3 Sender: ");
  Serial.println(WiFi.macAddress());

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW gagal diinisialisasi.");
    return;
  }

  esp_now_register_send_cb(onDataSent);

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, displayAddress, 6);
  peerInfo.channel = 1;
  peerInfo.encrypt = false;

  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Gagal menambahkan peer ESP32 LED P10.");
    return;
  }

  Serial.println("ESP-NOW siap.");
  Serial.println("Receiver MAC: 78:42:1C:6C:76:B4");
}

// =====================================================
// SETUP UTAMA
// =====================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("======================================");
  Serial.println("ESP32-S3 SENSOR NODE");
  Serial.println("Ultrasonic-Guided Event Segmentation");
  Serial.println("Load Cell Validation + Decision Tree");
  Serial.println("======================================");

  scale.begin(HX711_DT, HX711_SCK);

  pinMode(TRIG_1, OUTPUT);
  pinMode(ECHO_1, INPUT);

  pinMode(TRIG_2, OUTPUT);
  pinMode(ECHO_2, INPUT);

  preferences.begin("parking", false);
  occupiedSlot = preferences.getInt("occupied", 0);

  Serial.print("Jumlah terisi awal dari memori: ");
  Serial.print(occupiedSlot);
  Serial.print("/");
  Serial.println(TOTAL_SLOT);

  setupEspNow();

  resetEventData();

  calculateStartupBaseline();

  sendParkingData("start", "none");
}

// =====================================================
// LOOP UTAMA
// =====================================================
void loop() {
  handleSerialCommand();

  if (millis() - lastReadTime < READ_INTERVAL_MS) {
    return;
  }

  lastReadTime = millis();

  updateUltrasonicState();

  if (systemState == STATE_EVENT_WINDOW) {
    if (millis() - eventWindowStartTime > MAX_EVENT_WINDOW_MS) {
      cancelEventWindow("Event window terlalu lama, kemungkinan ultrasonik tersangkut atau objek berhenti.");
      return;
    }
  }

  if (systemState == STATE_POST_CLEAR_CAPTURE) {
    if (millis() - postCaptureStartTime > MAX_POST_CAPTURE_MS) {
      cancelEventWindow("Gagal mengambil 10 raw setelah ultrasonic clear dalam batas waktu.");
      return;
    }
  }

  long rawValue;

  if (!readHX711Raw(rawValue)) {
    Serial.println("HX711 belum siap, data dilewati.");
    return;
  }

  if (IGNORE_ZERO_RAW && rawValue == 0) {
    Serial.println("Raw = 0, data dilewati.");
    return;
  }

  unsigned long sampleTime = millis();

  if (systemState == STATE_IDLE) {
    pushPreEventRaw(rawValue, sampleTime);

    Serial.print("raw=");
    Serial.print(rawValue);

    Serial.print(", baseline=");
    Serial.print(baselineMean, 2);

    Serial.print(", threshold=");
    Serial.print(thresholdEvent, 2);

    Serial.print(", preBufferCount=");
    Serial.print(preEventBufferCount);

    Serial.print(", state=");
    Serial.println(getStateName());

    return;
  }

  if (systemState == STATE_EVENT_WINDOW) {
    processEventRaw(rawValue, sampleTime);
    return;
  }

  if (systemState == STATE_POST_CLEAR_CAPTURE) {
    processPostClearRaw(rawValue, sampleTime);
    return;
  }
}
