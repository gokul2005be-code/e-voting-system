
#include <LiquidCrystal.h>
#include <EEPROM.h>

// ---------- Config ----------
#define MAX_VOTERS  10
const uint8_t NUM_VOTERS = 9;

// LCD pins (RS, E, D4, D5, D6, D7)
LiquidCrystal lcd(7, 6, 5, 4, 3, 2);

// Buttons
const uint8_t BTN_A = A0;
const uint8_t BTN_B = A1;
const uint8_t BTN_C = A2;
const uint8_t BTN_N = A3;

// ---------- LED + BUZZER (ADDED) ----------
#define LED_A 8
#define LED_B 9
#define LED_C 10
#define LED_N 11
#define BUZZER 12
// ---------------------------------------

// Debounce
const unsigned long DEBOUNCE_MS = 50;
const unsigned long VOTE_WINDOW_MS = 20000UL;

// EEPROM layout
const int EEPROM_MAGIC_ADDR = 0;
const uint8_t EEPROM_MAGIC = 0x5A;
const int EEPROM_VOTED_START = 1;
const int EEPROM_COUNTS_START = EEPROM_VOTED_START + MAX_VOTERS;

// Demo database
const char *voterID[NUM_VOTERS]   = {"1234","5678","9012","3344","4455","6677","5555","2345","3452"};
const char *voterName[NUM_VOTERS] = {"GOKUL","RAJ","ARUN","VARUN","THARUN","VINOTH","KISHORE","BALA","KAVI"};

// Runtime variables
bool votedFlags[MAX_VOTERS];
int countA = 0, countB = 0, countC = 0, countN = 0;

bool voting = false;
int voterIndex = -1;
unsigned long voteStartMs = 0;
bool voteTaken = false;

// Button debounce struct
struct BtnState {
  uint8_t pin;
  bool lastState;
  unsigned long lastChangeMs;
} btnA, btnB, btnC, btnN;

// ---------------- BUTTON SETUP ----------------
void setupButtons() {
  pinMode(BTN_A, INPUT_PULLUP);
  pinMode(BTN_B, INPUT_PULLUP);
  pinMode(BTN_C, INPUT_PULLUP);
  pinMode(BTN_N, INPUT_PULLUP);

  btnA = { BTN_A, digitalRead(BTN_A), 0 };
  btnB = { BTN_B, digitalRead(BTN_B), 0 };
  btnC = { BTN_C, digitalRead(BTN_C), 0 };
  btnN = { BTN_N, digitalRead(BTN_N), 0 };
}

void updateButton(BtnState &b) {
  bool cur = digitalRead(b.pin);
  if (cur != b.lastState) {
    if (millis() - b.lastChangeMs > DEBOUNCE_MS) {
      b.lastChangeMs = millis();
      b.lastState = cur;
    }
  }
}

// ---------------- EEPROM ----------------
void eepromSaveAll() {
  EEPROM.update(EEPROM_MAGIC_ADDR, EEPROM_MAGIC);
  for (int i = 0; i < MAX_VOTERS; i++)
    EEPROM.update(EEPROM_VOTED_START + i, votedFlags[i] ? 1 : 0);

  int addr = EEPROM_COUNTS_START;
  EEPROM.put(addr, countA); addr += sizeof(countA);
  EEPROM.put(addr, countB); addr += sizeof(countB);
  EEPROM.put(addr, countC); addr += sizeof(countC);
  EEPROM.put(addr, countN);
}

void eepromLoadAll() {
  if (EEPROM.read(EEPROM_MAGIC_ADDR) != EEPROM_MAGIC) {
    for (int i = 0; i < MAX_VOTERS; i++) votedFlags[i] = false;
    countA = countB = countC = countN = 0;
    eepromSaveAll();
    return;
  }
  for (int i = 0; i < MAX_VOTERS; i++)
    votedFlags[i] = EEPROM.read(EEPROM_VOTED_START + i);

  int addr = EEPROM_COUNTS_START;
  EEPROM.get(addr, countA); addr += sizeof(countA);
  EEPROM.get(addr, countB); addr += sizeof(countB);
  EEPROM.get(addr, countC); addr += sizeof(countC);
  EEPROM.get(addr, countN);
}

// ---------------- HELPERS ----------------
void showLCD(const char *l1, const char *l2 = "") {
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print(l1);
  lcd.setCursor(0,1);
  lcd.print(l2);
}

int findVoterIndex(const char* vid, const char* name) {
  for (int i = 0; i < NUM_VOTERS; i++)
    if (strcmp(voterID[i], vid) == 0 && strcmp(voterName[i], name) == 0)
      return i;
  return -1;
}

// ---------------- VOTE FLOW ----------------
void startVotingForIndex(int idx) {
  voting = true;
  voterIndex = idx;
  voteStartMs = millis();
  voteTaken = false;
  showLCD("VOTE NOW", "SELECT PARTY");
}

// *************** MODIFIED FUNCTION ***************
void recordVoteAndPersist(char party, const char *partyName) {

  voting = false;
  voteTaken = true;

  int ledPin = -1;

  if (party == 'A') { countA++; ledPin = LED_A; }
  else if (party == 'B') { countB++; ledPin = LED_B; }
  else if (party == 'C') { countC++; ledPin = LED_C; }
  else if (party == 'N') { countN++; ledPin = LED_N; }

  if (ledPin != -1) digitalWrite(ledPin, HIGH);

  votedFlags[voterIndex] = true;
  eepromSaveAll();

  showLCD("VOTED FOR", partyName);

  tone(BUZZER, 1000, 300);   // buzzer beep
  delay(300);

  while (digitalRead(BTN_A) == LOW || digitalRead(BTN_B) == LOW ||
         digitalRead(BTN_C) == LOW || digitalRead(BTN_N) == LOW);

  if (ledPin != -1) digitalWrite(ledPin, LOW);

  delay(1500);
  showLCD("SCAN QR CODE", "");
  voterIndex = -1;
}

// ---------------- SETUP ----------------
void setup() {
  Serial.begin(9600);
  delay(200);

  lcd.begin(16,2);

  // LED + BUZZER setup
  pinMode(LED_A, OUTPUT);
  pinMode(LED_B, OUTPUT);
  pinMode(LED_C, OUTPUT);
  pinMode(LED_N, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  setupButtons();
  eepromLoadAll();

  showLCD("E-VOTING SYS", "SCAN QR CODE");
}

// ---------------- LOOP ----------------
void loop() {

  if (!voting && Serial.available()) {
    String data = Serial.readStringUntil('\n');
    int idP = data.indexOf("VID:");
    int nmP = data.indexOf("NAME:");
    if (idP != -1 && nmP != -1) {
      String id = data.substring(idP + 4, data.indexOf(";", idP));
      String nm = data.substring(nmP + 5);
      int idx = findVoterIndex(id.c_str(), nm.c_str());
      if (idx >= 0 && !votedFlags[idx]) startVotingForIndex(idx);
      else showLCD("ALREADY VOTED", "");
    }
  }

  if (voting && !voteTaken) {
    updateButton(btnA);
    updateButton(btnB);
    updateButton(btnC);
    updateButton(btnN);

    if (btnA.lastState == LOW) recordVoteAndPersist('A', "PARTY A");
    else if (btnB.lastState == LOW) recordVoteAndPersist('B', "PARTY B");
    else if (btnC.lastState == LOW) recordVoteAndPersist('C', "PARTY C");
    else if (btnN.lastState == LOW) recordVoteAndPersist('N', "NOTA");
  }
}