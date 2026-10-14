#include "console.h"
#include "config.h"
#include "settings.h"
#include "machine.h"
#include "radar.h"
#include <stdarg.h>

// ---------------------------------------------------------------- log

// The last LOG_LINES lines, numbered, so the web page can ask "anything after 57?"
static const int LOG_LINES = 60;
static String   ring[LOG_LINES];
static uint32_t seq = 0;                 // number of the newest line
static SemaphoreHandle_t logLock = nullptr;
static String  *captureTo = nullptr;     // set while a web command is running

void logf(const char *fmt, ...) {
  char buf[320];
  va_list ap; va_start(ap, fmt);
  vsnprintf(buf, sizeof buf, fmt, ap);
  va_end(ap);
  if (!logLock) logLock = xSemaphoreCreateMutex();
  xSemaphoreTake(logLock, portMAX_DELAY);
  Serial.println(buf);
  seq++;
  ring[seq % LOG_LINES] = buf;
  if (captureTo && xTaskGetCurrentTaskHandle() == xTaskGetHandle("loopTask")) { *captureTo += buf; *captureTo += "\n"; }
  xSemaphoreGive(logLock);
}

void logSnapshot() {
  if (!logLock) return;
  String t;
  xSemaphoreTake(logLock, portMAX_DELAY);
  uint32_t first = seq >= 40 ? seq - 39 : 1;
  for (uint32_t n = first; n <= seq; n++) { t += ring[n % LOG_LINES]; t += "\n"; }
  xSemaphoreGive(logLock);
  faultLogSave(t);
}

static void printLastLog() {
  String t = faultLogLoad();
  if (!t.length()) { logf("lastlog: nothing kept yet (it is kept at every fault)"); return; }
  logf("lastlog: the log lines up to the last fault, kept through power cuts:");
  int a = 0;
  while (a < (int)t.length()) {
    int b = t.indexOf('\n', a);
    if (b < 0) b = t.length();
    logf("  | %s", t.substring(a, b).c_str());
    a = b + 1;
  }
}

static String jsonEscape(const String &in) {
  String out; out.reserve(in.length() + 8);
  for (size_t i = 0; i < in.length(); i++) {
    char c = in[i];
    if (c == '"') out += "\\\"";
    else if (c == '\\') out += "\\\\";
    else if (c == '\n') out += "\\n";
    else if ((uint8_t)c >= 0x20) out += c;
  }
  return out;
}

String logJsonSince(uint32_t since, uint32_t &next) {
  if (!logLock) logLock = xSemaphoreCreateMutex();
  xSemaphoreTake(logLock, portMAX_DELAY);
  uint32_t first = since + 1;
  if (seq >= (uint32_t)LOG_LINES && first < seq - LOG_LINES + 1) first = seq - LOG_LINES + 1;
  String j;
  for (uint32_t n = first; n <= seq; n++) {
    if (j.length()) j += ",";
    j += "\"" + jsonEscape(ring[n % LOG_LINES]) + "\"";
  }
  next = seq;
  xSemaphoreGive(logLock);
  return j;
}

// ---------------------------------------------------------------- commands

static void printStatus() {
  MachineStatus m = machineStatus();
  logf("state=%s armed=%d sensor=%d(%s) limit=%s (closed %lu times since power-up) home=%s driver=%s servo=%s@%d | rewind steps=%ld last=%ld%s drops=%lu%s%s",
       m.state, m.armed, m.sensor, m.viaRadar ? "radar" : "OUT pin",
       m.limitFitted ? (m.limitRaw ? "pressed" : "open") : (m.limitRaw ? "not-fitted(pressed)" : "not-fitted(open)"),
       (unsigned long)m.limitCloses,
       m.home ? "yes" : "unknown",
       m.driverOn ? "on" : "off", m.servoAttached ? "on" : "off", m.servoDeg,
       m.rewindSteps, m.lastRewindSteps, m.lastRewindByLimit ? "(limit)" : "",
       (unsigned long)m.drops, m.fault[0] ? " | fault: " : "", m.fault);
  logf("settings: lock=%d rel=%d line=%dmm rpm=%d dir=%d settle=%dms rearm=%dms limit=%d liminv=%d"
       " | dropmm=%d droprpm=%d dropacc=%d dropdec=%d relms=%d",
       S.servoLock, S.servoRel, S.lineMm, S.rpm, S.rewindDir, S.settleMs, S.rearmMs, S.limitFitted, S.limitInverted,
       S.dropMm, S.dropRpm, S.dropAcc, S.dropDec, S.releaseMs);
}

// One log line per help line: a log line holds 320 characters at most.
static const char *const HELP[] = {
  "commands:",
  "  status | help | arm | disarm | save | defaults | clear",
  "  drop            full cycle now (unload + finger out, powered drop, settle, rewind, lock)",
  "  rel             unload + finger out only; motor stays on holding the spider",
  "  lock            finger in, seat move onto a tooth, then driver off",
  "  rewind          rewind (finger out first); at the limit switch it eases off 1/8 turn and locks",
  "  teach           spider hanging where a drop should stop: wind up to the switch, count it, save it as dropmm (page: Set drop length here)",
  "  rehome          bring it home from anywhere: lower 1/2 turn, wind slowly to the switch, clear the fault, re-arm (same as 3 fast presses of the switch; 5 presses within 4 s = sleep or wake)",
  "  lastlog         the log lines up to the last fault, kept through a power cut",
  "  jog <steps>     signed microsteps, 1600 = one turn, + = rewind direction; finger out first; driver stays on",
  "  stop            halt everything now, leave the motor as it is",
  "  off             driver off and servo off",
  "  servo <deg>     move the finger live (for finding angles)",
  "  setlock <deg> | setrel <deg> | line <mm> | rpm <n> | dir <0|1> | settle <ms> | rearm <ms>",
  "  limit <0|1>     limit switch fitted | liminv <0|1> switch reads backwards",
  "  dropmm <mm>     how far the spider drops (100 to line - 70)",
  "  droprpm <n>     drop top speed, 100 to 900 | relms <ms> finger travel before the drop, 100 to 600",
  "  dropacc <n> | dropdec <n>   drop start and stop rates, microsteps/s^2 (100000 is about 1 g)",
  "  wifi            show network state | ip <address>   fixed network address, saved; ip none = the router picks; restart   restart the board",
  "  radar   what the C4002 sees now and whether it would fire | radar probe   find its wire",
  "  radar range [closest farthest]  the sensor's own detect range, cm (set closest past the hanging spider) | radar version",
  "  radar out <1|2|3>  what its OUT pin goes high on: 1 motion, 2 presence, 3 either | radar reset   its factory settings",
  "  radar raw       the last 96 bytes heard from the sensor, as hex | radar baud   find its speed; set it back to 115200 if it moved",
  "  radar cmd r|w <cmd> [hex]  one protocol command by hand, e.g. radar cmd r 82 01 (software version)",
  "  radar res [80|20]  the sensor's range step | radar calib <delay s> <listen s>  it learns the empty room | radar delay [s]  how long it keeps a person after losing them",
  "  radar sens motion|presence [low|mid|high]  the sensor's own sensitivity for the moving and the still reading",
  "  sensor 4002|2410  4002 = C4002 over serial, OUT pin if silent; 2410 = OUT pin on GPIO33 only | approach cm/s | leadms ms",
  "  firecm <cm>     fire when someone approaching is within this distance, 0 = off | radarinv 0|1   direction word reads backwards",
  "  clearcm <cm>    the doorway is clear when nobody moving reads within this distance (re-arm after a scare), 50 to 1100",
  "  clearms <ms>    re-arm anyway after waiting this long for the doorway to clear, 0 = wait for clear | clear   also skips the lockout and the wait",
  "  (settings change immediately; 'save' keeps them after power loss)",
  "  motion commands disarm the sensor; 'arm' when bench work is done",
};

static void printRadar() {
  RadarStats r = radarStats();
  if (!r.frames) { logf("radar: no result frames yet (%lu bytes heard on RX2): check the C4002's 5 V, its TX wire to RX2 (GPIO16) and its RX wire to TX2 (GPIO17)", (unsigned long)r.bytes); return; }
  logf("radar: %s, %.1f frames/s, last %lu ms ago | frames %lu, bad %lu | version %s, detect range %u to %u cm",
       r.talking ? "talking" : "SILENT", r.fps, (unsigned long)r.ageMs, (unsigned long)r.frames, (unsigned long)r.bad,
       r.version.length() ? r.version.c_str() : "?", r.closest, r.farthest);
  if (!r.talking) return;
  const RadarReading &d = r.r;
  if (d.state == 0) logf("  nobody in view");
  if (d.state == 2 || d.state == 3) logf("  moving: %d cm away, %d cm/s, %s%s, energy %u%s", d.mdist, d.speed,
                         d.dir == 2 ? "approaching" : d.dir == 0 ? "going away" : "no direction", S.radarInv ? " (word swapped by radarinv 1)" : "", d.menergy,
                         d.etaMs ? (String(", arrives in ") + d.etaMs + " ms").c_str() : "");
  if (d.state == 1 || d.state == 3 || (d.state == 2 && d.pdist > 0)) logf("  still: %d cm away, energy %u", d.pdist, d.penergy);
  logf("  rule (approach %d cm/s, firecm %d, leadms %d): %s%s", S.approach, S.fireCm, S.leadMs, d.fire ? "PASSES" : "does not pass",
       r.fireRun >= 2 ? ", two in a row: WOULD FIRE" : "");
  if (r.why.length()) logf("  last drop fired by the sensor: %s, %lu s ago", r.why.c_str(), (unsigned long)(r.whyAgoMs / 1000));
}

static void printHelp() {
  for (const char *l : HELP) logf("%s", l);
}

extern String webWhereAmI();

static void motion(Action a, long arg, TriggerSource src) {
  String why;
  if (!machineRequest(a, arg, src, why)) logf("refused: %s", why.c_str());
}

void consoleRun(const String &raw, String *capture) {
  String line = raw; line.trim();
  if (!line.length()) return;

  if (capture) captureTo = capture;
  logf("> %s", line.c_str());

  int sp = line.indexOf(' ');
  String cmd = sp < 0 ? line : line.substring(0, sp);
  String argS = sp < 0 ? "" : line.substring(sp + 1); argS.trim();
  cmd.toLowerCase();
  long arg = 0;
  bool hasArg = parseLong(argS, arg);
  TriggerSource src = capture ? TRIG_WEB : TRIG_CONSOLE;

  if      (cmd == "help")     printHelp();
  else if (cmd == "status")   printStatus();
  else if (cmd == "arm")      { S.armed = 1; logf("armed (every power-up arms on its own)"); }
  else if (cmd == "disarm")   { S.armed = 0; logf("disarmed until the next power cycle"); }
  else if (cmd == "save")     { settingsSave(); logf("saved"); }
  else if (cmd == "defaults") { settingsDefaults(); logf("defaults loaded (not saved)"); printStatus(); }
  else if (cmd == "clear")    motion(ACT_CLEAR, 0, src);
  else if (cmd == "drop")     motion(ACT_DROP, 0, src);
  else if (cmd == "rel")      motion(ACT_REL, 0, src);
  else if (cmd == "lock")     motion(ACT_LOCK, 0, src);
  else if (cmd == "rewind")   motion(ACT_REWIND, 0, src);
  else if (cmd == "teach")    motion(ACT_TEACH, 0, src);
  else if (cmd == "rehome")   motion(ACT_REHOME, 0, src);
  else if (cmd == "lastlog")  printLastLog();
  else if (cmd == "stop")     motion(ACT_STOP, 0, src);
  else if (cmd == "off")      motion(ACT_OFF, 0, src);
  else if (cmd == "jog" || cmd == "servo") {
    if (!hasArg) logf("refused: %s needs a whole number, e.g. %s", cmd.c_str(), cmd == "jog" ? "jog 1600" : "servo 90");
    else motion(cmd == "jog" ? ACT_JOG : ACT_SERVO, arg, src);
  }
  else if (cmd == "wifi")     logf("%s", webWhereAmI().c_str());
  else if (cmd == "ip") {
    if (!argS.length()) { String f = ipSaved(); logf(f.length() ? "fixed address %s (restart to use a change)" : "no fixed address: the router picks", f.c_str()); }
    else if (argS == "none") { ipSave(""); logf("fixed address cleared: the router picks after the next restart"); }
    else { IPAddress a; if (!a.fromString(argS)) logf("refused: not an address, e.g. ip 192.168.1.138"); else { ipSave(argS); logf("fixed address %s saved: send restart to use it", argS.c_str()); } }
  }
  else if (cmd == "restart") {
    if (machineStatus().busy) logf("refused: a move is running");
    else { logf("restarting"); delay(200); machineSafeStop(); ESP.restart(); }
  }
  else if (cmd == "radar")    {
    String sub = argS, rest; int sp2 = argS.indexOf(' ');
    if (sp2 >= 0) { sub = argS.substring(0, sp2); rest = argS.substring(sp2 + 1); rest.trim(); }
    bool talks = sub == "reset" || sub == "baud" || sub == "cmd" || sub == "range" || sub == "out" || sub == "version" ||
                 sub == "res" || sub == "calib" || sub == "sens" || sub == "delay";
    if (talks && machineStatus().busy) logf("refused: a move is running");
    else if (sub == "baud") radarBaud();
    else if (sub == "cmd") radarCmd(rest);
    else if (sub == "reset") radarReset();
    else if (sub == "version") radarVersion();
    else if (sub == "range") {
      long a = -1, b = -1; int sp3 = rest.indexOf(' ');
      if (rest.length() && !(sp3 > 0 && parseLong(rest.substring(0, sp3), a) && parseLong(rest.substring(sp3 + 1), b))) logf("radar range: closest then farthest in cm, e.g. radar range 60 600; alone = read it");
      else radarRange((int)a, (int)b);
    }
    else if (sub == "out") { long m = 0; if (rest.length() && !parseLong(rest, m)) logf("radar out: 1 motion, 2 presence, 3 either; alone = read it"); else radarOut((int)m); }
    else if (sub == "res") { long m = -1; if (rest.length() && !(parseLong(rest, m) && (m == 20 || m == 80))) logf("radar res: 80 or 20; alone = read it"); else radarRes(m < 0 ? -1 : (m == 20 ? 1 : 0)); }
    else if (sub == "calib") { long a = -1, b = -1; int sp3 = rest.indexOf(' '); if (!(sp3 > 0 && parseLong(rest.substring(0, sp3), a) && parseLong(rest.substring(sp3 + 1), b))) logf("radar calib: delay seconds then listen seconds, e.g. radar calib 10 30"); else radarCalib((int)a, (int)b); }
    else if (sub == "delay") { long s = -1; if (rest.length() && !parseLong(rest, s)) logf("radar delay: seconds; alone = read it"); else radarDelay((int)s); }
    else if (sub == "sens") {
      String g = rest, lv; int sp3 = rest.indexOf(' '); if (sp3 > 0) { g = rest.substring(0, sp3); lv = rest.substring(sp3 + 1); lv.trim(); }
      int gate = g == "motion" ? 0 : g == "presence" ? 1 : -1, grp = lv == "low" ? 0 : lv == "mid" ? 1 : lv == "high" ? 2 : lv.length() ? 9 : -1;
      if (gate < 0 || grp == 9) logf("radar sens: motion or presence, then low, mid or high; without a level = read it");
      else radarSens(gate, grp);
    }
    else if (sub == "raw") radarRaw();
    else if (sub == "probe") radarProbe();
    else if (sub.length()) logf("radar: alone, or probe, raw, baud, version, range, res, calib, sens, delay, out, reset, cmd");
    if (!sub.length() || sub == "probe" || sub == "baud" || sub == "reset") printRadar();
  }
  else if (settingsIsName(cmd)) {
    MachineStatus m = machineStatus();
    String why;
    if ((cmd == "dir" || cmd == "rpm" || cmd.startsWith("drop")) && m.motorRunning) logf("refused: motor is running");
    else if (!settingsSet(cmd, argS, why)) logf("refused: %s %s", cmd.c_str(), why.c_str());
    else printStatus();
  }
  else logf("unknown, type help");

  if (capture) captureTo = nullptr;
}

void consolePollSerial() {
  static String rx;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') { consoleRun(rx); rx = ""; }
    else if (rx.length() < 120) rx += c;
  }
}
