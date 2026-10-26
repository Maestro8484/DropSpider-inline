#include "settings.h"
#include "config.h"
#include <Preferences.h>

Settings S;
static Settings savedCopy;             // what flash holds, for the page's unsaved marks
static uint32_t boots = 0;

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
  { "limit",   "limFit", &S.limitFitted,   0,    1,      DEF_LIMIT_FITTED },
  { "liminv",  "limInv", &S.limitInverted, 0,    1,      DEF_LIMIT_INVERTED },
  { "dropmm",  "dropMm", &S.dropMm,        100,  2930,   DEF_DROP_MM },      // also <= dropMmMax()
  { "droprpm", "dropRpm",&S.dropRpm,       100,  900,    DEF_DROP_RPM },
  { "dropacc", "dropAcc",&S.dropAcc,       20000, 400000, DEF_DROP_ACC },
  { "dropdec", "dropDec",&S.dropDec,       10000, 200000, DEF_DROP_DEC },
  { "relms",   "relMs",  &S.releaseMs,     100,  600,    DEF_RELEASE_MS },
  { "sensor",  "sensor", &S.sensor,        2410, 4002,   DEF_SENSOR },        // only 2410 or 4002
  { "approach","apprch", &S.approach,      10,   150,    DEF_APPROACH },
  { "leadms",  "leadMs", &S.leadMs,        200,  2000,   DEF_LEAD_MS },
  { "firecm",  "fireCm", &S.fireCm,        0,    1100,   DEF_FIRE_CM },       // 0 = off
  { "clearcm", "clearCm",&S.clearCm,       50,   1100,   DEF_CLEAR_CM },
  { "clearms", "clearMs",&S.clearMs,       0,    600000, DEF_CLEAR_MS },      // 0 = wait for clear
  { "active",  "active", &S.active,        0,    1,      DEF_ACTIVE },        // 0 = deactivated: never arms, through power cycles
  { "radarinv","radInv", &S.radarInv,      0,    1,      DEF_RADAR_INV },
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
  S.armed = DEF_ARMED;
}

void settingsBegin() {
  if (!lock) lock = xSemaphoreCreateMutex();
  Guard g;
  prefs.begin(STORE, false);
  for (size_t i = 0; i < N; i++) *ROWS[i].ptr = prefs.getInt(ROWS[i].key, ROWS[i].def);
  // Armed is never saved: every power-up arms on its own (owner 2026-10-13: "it needs to
  // default to being armed and ready even with power cycled"). disarm, and the disarm
  // that every bench move does, hold only until the next power cycle. The home guard in
  // machine.cpp still stops a power-up with the spider down on a fault instead of arming.
  // The one exception is the saved off switch (owner 2026-10-25): deactivated from the
  // page, it never arms, power cycle or not, until activated from the page again.
  S.armed = S.active ? DEF_ARMED : 0;
  savedCopy = S;
  boots = prefs.getULong("boots", 0) + 1;
  prefs.putULong("boots", boots);
}

void settingsSave() {
  Guard g;
  for (size_t i = 0; i < N; i++) prefs.putInt(ROWS[i].key, *ROWS[i].ptr);
  savedCopy = S;
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
    if (name == "sensor" && v != 2410 && v != 4002) { why = "4002 (C4002 over serial) or 2410 (OUT pin only)"; return false; }
    // The drop and the line limit each other: the spider must stop short of the knot.
    if (name == "dropmm" && v > dropMmMax()) {
      why = String("allowed 100 to ") + dropMmMax() + " with line " + S.lineMm + " mm";
      return false;
    }
    if (name == "line" && S.dropMm > v - SPOOL_TO_EYELET_MM - DROP_KNOT_MARGIN_MM) {
      why = String("dropmm ") + S.dropMm + " would reach the knot: set dropmm to " +
            (long)(v - SPOOL_TO_EYELET_MM - DROP_KNOT_MARGIN_MM) + " or less first";
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

String settingsStockJson() {
  String j;
  for (size_t i = 0; i < N; i++) {
    if (i) j += ",";
    j += "\"" + String(ROWS[i].name) + "\":" + String(ROWS[i].def);
  }
  return j;
}

// Each row's pointer is into S; the same offset into savedCopy is the saved value.
static int savedValue(size_t i) {
  return *(const int *)((const char *)&savedCopy + ((const char *)ROWS[i].ptr - (const char *)&S));
}

String settingsUnsavedJson() {
  String j;
  for (size_t i = 0; i < N; i++) {
    if (*ROWS[i].ptr == savedValue(i)) continue;
    if (j.length()) j += ",";
    j += "\"" + String(ROWS[i].name) + "\"";
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

String ipSaved() { Guard g; return prefs.getString("ip", ""); }
void ipSave(const String &ip) { Guard g; prefs.putString("ip", ip); }

int dropMmMax() { return S.lineMm - (int)SPOOL_TO_EYELET_MM - DROP_KNOT_MARGIN_MM; }

void faultLogSave(const String &text) { Guard g; prefs.putString("lastlog", text.length() > 3900 ? text.substring(text.length() - 3900) : text); }
String faultLogLoad() { Guard g; return prefs.getString("lastlog", ""); }

bool homeSaved() { Guard g; return prefs.getBool("home", false); }
void homeSave(bool home) {
  Guard g;
  if (prefs.getBool("home", false) != home) prefs.putBool("home", home);
}

uint32_t dropCount()     { Guard g; return prefs.getULong("drops", 0); }
void     dropCountBump() { Guard g; prefs.putULong("drops", prefs.getULong("drops", 0) + 1); }

uint32_t bootCount() { return boots; }

size_t cyclesLoad(void *buf, size_t max) { Guard g; return prefs.getBytes("cycles", buf, max); }
void   cyclesSave(const void *buf, size_t n) { Guard g; prefs.putBytes("cycles", buf, n); }
