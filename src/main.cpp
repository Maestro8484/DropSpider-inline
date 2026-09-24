// DropSpider - Mechanism A (In-Line Single-Axle Clutch Spool) - Rev C firmware
// Board: ESP32 DevKit V1 (30-pin). Driver: TMC2209 in STEP/DIR/EN standalone mode on an A4988-style carrier.
// Cycle: sensor edge -> finger out (free-fall) -> settle -> rewind -> finger in -> driver off -> lockout.
// Holding at the top costs zero power: the finger and ratchet hold, driver and servo are both off.

#include <Arduino.h>
#include <Preferences.h>
#include <ESP32Servo.h>
#include "config.h"

struct Settings {
  int servoLock, servoRel, lineMm, rpm, rewindDir, settleMs, rearmMs, armed;
} S;

Preferences prefs;
Servo pawl;
enum State { IDLE, LOCKOUT, WAIT_CLEAR } state = IDLE;
unsigned long stateSince = 0, highSince = 0, lowSince = 0;
bool lastSensor = false;
String rx;

// ---------------- settings ----------------
void loadSettings() {
  prefs.begin("dropspider", true);
  S.servoLock = prefs.getInt("lock", DEF_SERVO_LOCK);
  S.servoRel  = prefs.getInt("rel", DEF_SERVO_REL);
  S.lineMm    = prefs.getInt("line", DEF_LINE_MM);
  S.rpm       = prefs.getInt("rpm", DEF_RPM);
  S.rewindDir = prefs.getInt("dir", DEF_REWIND_DIR);
  S.settleMs  = prefs.getInt("settle", DEF_SETTLE_MS);
  S.rearmMs   = prefs.getInt("rearm", DEF_REARM_MS);
  S.armed     = prefs.getInt("armed", DEF_ARMED);
  prefs.end();
}

void saveSettings() {
  prefs.begin("dropspider", false);
  prefs.putInt("lock", S.servoLock); prefs.putInt("rel", S.servoRel); prefs.putInt("line", S.lineMm);
  prefs.putInt("rpm", S.rpm); prefs.putInt("dir", S.rewindDir); prefs.putInt("settle", S.settleMs);
  prefs.putInt("rearm", S.rearmMs); prefs.putInt("armed", S.armed);
  prefs.end();
}

void defaults() {
  S = { DEF_SERVO_LOCK, DEF_SERVO_REL, DEF_LINE_MM, DEF_RPM, DEF_REWIND_DIR, DEF_SETTLE_MS, DEF_REARM_MS, DEF_ARMED };
}

long rewindSteps() {
  const float circ = PI * BARREL_DIA_MM;
  float turns = (S.lineMm - SPOOL_TO_EYELET_MM) / circ + OVERSHOOT_TURNS;
  if (turns < 0.5f) turns = 0.5f;
  return (long)(turns * MOTOR_FULL_STEPS * MICROSTEPS);
}

// ---------------- actuators ----------------
void driverOn()  { digitalWrite(PIN_EN, LOW); delay(5); }
void driverOff() { digitalWrite(PIN_EN, HIGH); }

void servoTo(int deg, bool holdAfter) {
  if (!pawl.attached()) pawl.attach(PIN_SERVO, 500, 2400);
  pawl.write(constrain(deg, 0, 180));
  delay(SERVO_MOVE_MS);
  if (!holdAfter) pawl.detach();
}

// Signed step count. Positive = rewind direction.
void runSteps(long n) {
  if (n == 0) return;
  bool fwd = n > 0; n = labs(n);
  digitalWrite(PIN_DIR, fwd ? S.rewindDir : !S.rewindDir);
  delayMicroseconds(20);
  const float fullUs = 60000000.0f / ((float)S.rpm * MOTOR_FULL_STEPS * MICROSTEPS);
  for (long i = 0; i < n; i++) {
    float frac = 1.0f;
    long fromEnd = n - i;
    long r = min((long)i, fromEnd);
    if (r < RAMP_STEPS) frac = RAMP_START_FRAC + (1.0f - RAMP_START_FRAC) * ((float)r / RAMP_STEPS);
    digitalWrite(PIN_STEP, HIGH); delayMicroseconds(4);
    digitalWrite(PIN_STEP, LOW);
    delayMicroseconds((uint32_t)(fullUs / frac));
    if ((i & 1023) == 0) yield();
  }
}

// ---------------- cycle pieces ----------------
void releaseFinger() { servoTo(S.servoRel, true); }

void rewind() {
  driverOn();
  runSteps(rewindSteps());
  // driver stays on so the spool holds while the finger goes in
}

void lockFinger() {
  // finger in while the motor still holds, then let the spool back onto a tooth while the servo keeps pushing
  servoTo(S.servoLock, true);
  driverOff();
  delay(LOCK_SEAT_MS);
  pawl.detach();
}

void fullCycle(const char* why) {
  Serial.printf("[cycle] trigger: %s\n", why);
  digitalWrite(PIN_LED, HIGH);
  driverOff();
  releaseFinger();                 // spider free-falls here
  delay(S.settleMs);
  rewind();
  lockFinger();
  digitalWrite(PIN_LED, LOW);
  state = LOCKOUT; stateSince = millis();
  Serial.printf("[cycle] done, lockout %d ms\n", S.rearmMs);
}

// ---------------- serial console ----------------
void printStatus() {
  Serial.printf("armed=%d state=%d sensor=%d | lock=%d rel=%d line=%dmm rpm=%d dir=%d settle=%dms rearm=%dms | rewind steps=%ld\n",
                S.armed, state, digitalRead(PIN_SENSOR), S.servoLock, S.servoRel, S.lineMm, S.rpm, S.rewindDir,
                S.settleMs, S.rearmMs, rewindSteps());
}

void printHelp() {
  Serial.println(
    "commands:\n"
    "  status | help | arm | disarm | save | defaults\n"
    "  drop            full cycle now (release, settle, rewind, lock)\n"
    "  rel             finger out only (spider drops, no rewind)\n"
    "  lock            finger in only, then driver off\n"
    "  rewind          rewind only (driver stays on until 'lock')\n"
    "  jog <steps>     signed microsteps, + = rewind direction; driver stays on\n"
    "  off             driver off and servo off\n"
    "  servo <deg>     move finger live (for finding angles)\n"
    "  setlock <deg> | setrel <deg> | line <mm> | rpm <n> | dir <0|1> | settle <ms> | rearm <ms>\n"
    "  (settings change immediately; 'save' keeps them after power loss)");
}

void handle(String line) {
  line.trim(); if (!line.length()) return;
  int sp = line.indexOf(' ');
  String cmd = sp < 0 ? line : line.substring(0, sp);
  long arg = sp < 0 ? 0 : line.substring(sp + 1).toInt();
  cmd.toLowerCase();
  if      (cmd == "help")     printHelp();
  else if (cmd == "status")   printStatus();
  else if (cmd == "arm")      { S.armed = 1; Serial.println("armed"); }
  else if (cmd == "disarm")   { S.armed = 0; Serial.println("disarmed"); }
  else if (cmd == "save")     { saveSettings(); Serial.println("saved"); }
  else if (cmd == "defaults") { defaults(); Serial.println("defaults loaded (not saved)"); }
  else if (cmd == "drop")     fullCycle("console");
  else if (cmd == "rel")      { driverOff(); releaseFinger(); pawl.detach(); }
  else if (cmd == "lock")     lockFinger();
  else if (cmd == "rewind")   rewind();
  else if (cmd == "jog")      { driverOn(); runSteps(arg); }
  else if (cmd == "off")      { driverOff(); pawl.detach(); }
  else if (cmd == "servo")    servoTo(arg, true);
  else if (cmd == "setlock")  S.servoLock = arg;
  else if (cmd == "setrel")   S.servoRel = arg;
  else if (cmd == "line")     S.lineMm = arg;
  else if (cmd == "rpm")      S.rpm = constrain(arg, 30, 600);
  else if (cmd == "dir")      S.rewindDir = arg ? 1 : 0;
  else if (cmd == "settle")   S.settleMs = arg;
  else if (cmd == "rearm")    S.rearmMs = arg;
  else Serial.println("unknown, type help");
  if (cmd.startsWith("set") || cmd == "line" || cmd == "rpm" || cmd == "dir" || cmd == "settle" || cmd == "rearm") printStatus();
}

// ---------------- main ----------------
void setup() {
  pinMode(PIN_EN, OUTPUT); driverOff();                // coils off first thing
  pinMode(PIN_STEP, OUTPUT); pinMode(PIN_DIR, OUTPUT);
  pinMode(PIN_SENSOR, INPUT_PULLDOWN);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  pinMode(PIN_LED, OUTPUT);
  Serial.begin(115200);
  ESP32PWM::allocateTimer(0);
  pawl.setPeriodHertz(50);
  loadSettings();
  // Assume the spider is up. Seat the finger; never auto-rewind at boot.
  servoTo(S.servoLock, true); delay(300); pawl.detach();
  Serial.println("\nDropSpider Mechanism A Rev C ready. Type help.");
  printStatus();
  state = WAIT_CLEAR; stateSince = millis(); lowSince = millis();
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') { handle(rx); rx = ""; } else rx += c;
  }

  unsigned long now = millis();
  bool s = digitalRead(PIN_SENSOR) == HIGH;
  if (s && !lastSensor) highSince = now;
  if (!s && lastSensor) lowSince = now;
  lastSensor = s;

  // status LED: slow blink armed and ready, off otherwise
  digitalWrite(PIN_LED, (S.armed && state == IDLE) ? ((now / 1000) % 2) : LOW);

  if (digitalRead(PIN_BUTTON) == LOW) { delay(30); if (digitalRead(PIN_BUTTON) == LOW) { fullCycle("BOOT button"); while (digitalRead(PIN_BUTTON) == LOW) delay(10); } }

  switch (state) {
    case LOCKOUT:
      if (now - stateSince >= (unsigned long)S.rearmMs) { state = WAIT_CLEAR; stateSince = now; }
      break;
    case WAIT_CLEAR:  // someone still standing there: wait until the doorway is empty
      if (!s && now - lowSince >= CLEAR_BEFORE_REARM) { state = IDLE; Serial.println("[armed] doorway clear"); }
      break;
    case IDLE:
      if (S.armed && s && now - highSince >= TRIGGER_DEBOUNCE_MS) fullCycle("sensor");
      break;
  }
  delay(5);
}
