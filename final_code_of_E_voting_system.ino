#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <EEPROM.h>

// ---------------- LCD ----------------
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ---------------- Buttons ----------------
#define BTN_A A0
#define BTN_B A1
#define BTN_C A2
#define BTN_N A3

// ---------------- LEDs ----------------
#define LED_A 8
#define LED_B 9
#define LED_C 10
#define LED_N 11

// ---------------- Buzzer ----------------
#define BUZZER 12

// ---------------- VOTER DATABASE ----------------
#define NUM_VOTERS 9

const char* voterID[NUM_VOTERS] = {
  "1234","5678","9012","3344","4455","6677","5555","2345","3452"
};

const char* voterName[NUM_VOTERS] = {
  "GOKUL","RAJ","ARUN","VARUN","THARUN","VINOTH","KISHORE","BALA","KAVI"
};

// EEPROM layout
#define EEPROM_MAGIC 0x5A
#define EEPROM_MAGIC_ADDR 0
#define EEPROM_VOTED_START 1   // 1 + voterIndex

int activeVoter = -1;
bool votingEnabled = false;

// ---------------- SETUP ----------------
void setup() {
  Serial.begin(9600);

  pinMode(BTN_A, INPUT_PULLUP);
  pinMode(BTN_B, INPUT_PULLUP);
  pinMode(BTN_C, INPUT_PULLUP);
  pinMode(BTN_N, INPUT_PULLUP);

  pinMode(LED_A, OUTPUT);
  pinMode(LED_B, OUTPUT);
  pinMode(LED_C, OUTPUT);
  pinMode(LED_N, OUTPUT);

  pinMode(BUZZER, OUTPUT);

  lcd.init();
  lcd.backlight();
  lcd.clear();

  initEEPROM();

  lcd.setCursor(0,0);
  lcd.print("E-VOTING SYS");
  lcd.setCursor(0,1);
  lcd.print("SCAN QR CODE");
}

// ---------------- LOOP ----------------
void loop() {

  // ---- Receive QR data from Python ----
  if (!votingEnabled && Serial.available()) {
    String data = Serial.readStringUntil('\n');
    data.trim();

    int idP = data.indexOf("VID:");
    int nmP = data.indexOf("NAME:");

    if (idP != -1 && nmP != -1) {
      String id = data.substring(idP + 4, data.indexOf(";", idP));
      String name = data.substring(nmP + 5);

      int idx = findVoter(id.c_str(), name.c_str());

      if (idx == -1) {
        showMessage("INVALID VOTER", "");
      }
      else if (EEPROM.read(EEPROM_VOTED_START + idx) == 1) {
        showMessage("ALREADY VOTED", "");
      }
      else {
        activeVoter = idx;
        votingEnabled = true;
        showMessage("VOTE NOW", "SELECT PARTY");
      }
    }
  }

  // ---- Voting ----
  if (votingEnabled) {
    if (digitalRead(BTN_A) == LOW) castVote("PARTY A", LED_A);
    else if (digitalRead(BTN_B) == LOW) castVote("PARTY B", LED_B);
    else if (digitalRead(BTN_C) == LOW) castVote("PARTY C", LED_C);
    else if (digitalRead(BTN_N) == LOW) castVote("NOTA", LED_N);
  }
}

// ---------------- FUNCTIONS ----------------

void castVote(const char* party, int ledPin) {

  EEPROM.update(EEPROM_VOTED_START + activeVoter, 1);

  digitalWrite(ledPin, HIGH);

  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("VOTED FOR");
  lcd.setCursor(0,1);
  lcd.print(party);

  tone(BUZZER, 1000, 300);
  delay(300);

  while (
    digitalRead(BTN_A) == LOW ||
    digitalRead(BTN_B) == LOW ||
    digitalRead(BTN_C) == LOW ||
    digitalRead(BTN_N) == LOW
  );

  digitalWrite(ledPin, LOW);

  delay(1500);

  votingEnabled = false;
  activeVoter = -1;

  showMessage("E-VOTING SYS ", "SCAN QR CODE");
}

int findVoter(const char* id, const char* name) {
  for (int i = 0; i < NUM_VOTERS; i++) {
    if (strcmp(voterID[i], id) == 0 &&
        strcmp(voterName[i], name) == 0)
      return i;
  }
  return -1;
}

void initEEPROM() {
  if (EEPROM.read(EEPROM_MAGIC_ADDR) != EEPROM_MAGIC) {
    EEPROM.update(EEPROM_MAGIC_ADDR, EEPROM_MAGIC);
    for (int i = 0; i < NUM_VOTERS; i++) {
      EEPROM.update(EEPROM_VOTED_START + i, 0);
    }
  }
}

void showMessage(const char* l1, const char* l2) {
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print(l1);
  lcd.setCursor(0,1);
  lcd.print(l2);
  delay(1500);
}