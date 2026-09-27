#include "console.h"
#include "config.h"
#include "settings.h"
#include "machine.h"
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
  logf("state=%s armed=%d sensor=%d limit=%s home=%s driver=%s servo=%s@%d | rewind steps=%ld last=%ld%s drops=%lu%s%s",
       m.state, m.armed, m.sensor,
       m.limitFitted ? (m.limitRaw ? "pressed" : "open") : (m.limitRaw ? "not-fitted(pressed)" : "not-fitted(open)"),
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
  "  rewind          rewind only (driver stays on until 'lock'); stops at the limit switch",
  "  jog <steps>     signed microsteps, 1600 = one turn, + = rewind direction; driver stays on",
  "  stop            halt everything now, leave the motor as it is",
  "  off             driver off and servo off",
  "  servo <deg>     move the finger live (for finding angles)",
  "  setlock <deg> | setrel <deg> | line <mm> | rpm <n> | dir <0|1> | settle <ms> | rearm <ms>",
  "  limit <0|1>     limit switch fitted | liminv <0|1> switch reads backwards",
  "  dropmm <mm>     how far the spider drops (100 to line - 70)",
  "  droprpm <n>     drop top speed, 100 to 900 | relms <ms> finger travel before the drop, 100 to 600",
  "  dropacc <n> | dropdec <n>   drop start and stop rates, microsteps/s^2 (100000 is about 1 g)",
  "  wifi            show network state",
  "  (settings change immediately; 'save' keeps them after power loss)",
  "  motion commands disarm the sensor; 'arm' when bench work is done",
};

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
  else if (cmd == "arm")      { S.armed = 1; logf("armed (send save to keep it after power loss)"); }
  else if (cmd == "disarm")   { S.armed = 0; logf("disarmed"); }
  else if (cmd == "save")     { settingsSave(); logf("saved"); }
  else if (cmd == "defaults") { settingsDefaults(); logf("defaults loaded (not saved)"); printStatus(); }
  else if (cmd == "clear")    motion(ACT_CLEAR, 0, src);
  else if (cmd == "drop")     motion(ACT_DROP, 0, src);
  else if (cmd == "rel")      motion(ACT_REL, 0, src);
  else if (cmd == "lock")     motion(ACT_LOCK, 0, src);
  else if (cmd == "rewind")   motion(ACT_REWIND, 0, src);
  else if (cmd == "stop")     motion(ACT_STOP, 0, src);
  else if (cmd == "off")      motion(ACT_OFF, 0, src);
  else if (cmd == "jog" || cmd == "servo") {
    if (!hasArg) logf("refused: %s needs a whole number, e.g. %s", cmd.c_str(), cmd == "jog" ? "jog 1600" : "servo 90");
    else motion(cmd == "jog" ? ACT_JOG : ACT_SERVO, arg, src);
  }
  else if (cmd == "wifi")     logf("%s", webWhereAmI().c_str());
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
