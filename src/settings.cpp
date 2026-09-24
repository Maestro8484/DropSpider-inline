#include "settings.h"
#include "config.h"
#include <Preferences.h>

Settings S;

// Preferences (the ESP32 flash key store) is not safe to use from two tasks at
// once, and the machine task bumps the drop count while the web page may be
// saving a setting. One lock guards every touch.
static Preferences prefs;
static const char *STORE = "dropspider";
static SemaphoreHandle_t lock = nullptr;

struct Guard {
  Guard()  { if (lock) xSemaphoreTake(lock, portMAX_DELAY); }
  ~Guard() { if (lock) xSemaphoreGive(lock); }
};

// One row per tunable. name = console command and web field, key = flash key
// (kept identical to the Rev C handoff firmware so saved values carry over).
struct Row { const char *name; const char *key; int *ptr; long lo; long hi; int def; };

static const Row ROWS[] = {
  { "setlock", "lock",   &S.servoLock,     0,    180,    DEF_SERVO_LOCK },
  { "setrel",  "rel",    &S.servoRel,      0,    180,    DEF_SERVO_REL },
  { "line",    "line",   &S.lineMm,        100,  3000,   DEF_LINE_MM },
  { "rpm",     "rpm",    &S.rpm,           30,   600,    DEF_RPM },
  { "dir",     "dir",    &S.rewindDir,     0,    1,      DEF_REWIND_DIR },
  { "settle",  "settle", &S.settleMs,      0,    60000,  DEF_SETTLE_MS },
  { "rearm",   "rearm",  &S.rearmMs,       0,    600000, DEF_REARM_MS },
  { "armed",   "armed",  &S.armed,         0,    1,      DEF_ARMED },
  { "limit",   "limFit", &S.limitFitted,   0,    1,      DEF_LIMIT_FITTED },
  { "liminv",  "limInv", &S.limitInverted, 0,    1,      DEF_LIMIT_INVERTED },
};
static const size_t N = sizeof(ROWS) / sizeof(ROWS[0]);

bool parseLong(const String &s, long &out) {
  if (s.length() == 0 || s.length() > 10) return false;
  size_t i = 0;
  bool neg = false;
  if (s[0] == '-' || s[0] == '+') { neg = s[0] == '-'; i = 1; }
  if (i >= s.length()) return false;
  long n = 0;
  for (; i < s.length(); i++) {
    if (s[i] < '0' || s[i] > '9') return false;
    n = n * 10 + (s[i] - '0');
  }
  out = neg ? -n : n;
  return true;
}

void settingsDefaults() {
  for (size_t i = 0; i < N; i++) *ROWS[i].ptr = ROWS[i].def;
}

void settingsBegin() {
  if (!lock) lock = xSemaphoreCreateMutex();
  Guard g;
  prefs.begin(STORE, false);
  for (size_t i = 0; i < N; i++) *ROWS[i].ptr = prefs.getInt(ROWS[i].key, ROWS[i].def);
}

void settingsSave() {
  Guard g;
  for (size_t i = 0; i < N; i++) prefs.putInt(ROWS[i].key, *ROWS[i].ptr);
}

bool settingsIsName(const String &name) {
  for (size_t i = 0; i < N; i++) if (name == ROWS[i].name) return true;
  return false;
}

bool settingsSet(const String &name, const String &value, String &why) {
  for (size_t i = 0; i < N; i++) {
    if (name != ROWS[i].name) continue;
    long v;
    if (!parseLong(value, v)) { why = "not a whole number"; return false; }
    if (v < ROWS[i].lo || v > ROWS[i].hi) {
      why = String("allowed ") + ROWS[i].lo + " to " + ROWS[i].hi;
      return false;
    }
    *ROWS[i].ptr = (int)v;
    return true;
  }
  why = "unknown setting";
  return false;
}

String settingsJson() {
  String j;
  for (size_t i = 0; i < N; i++) {
    if (i) j += ",";
    j += "\"" + String(ROWS[i].name) + "\":" + String(*ROWS[i].ptr);
  }
  return j;
}

String wifiSavedSsid() { Guard g; return prefs.getString("ssid", ""); }
String wifiSavedPass() { Guard g; return prefs.getString("pass", ""); }
void wifiSave(const String &ssid, const String &pass) {
  Guard g;
  prefs.putString("ssid", ssid);
  prefs.putString("pass", pass);
}

uint32_t dropCount()     { Guard g; return prefs.getULong("drops", 0); }
void     dropCountBump() { Guard g; prefs.putULong("drops", prefs.getULong("drops", 0) + 1); }
