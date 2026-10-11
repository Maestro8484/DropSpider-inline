#include "radar.h"
#include "config.h"
#include "console.h"
#include "settings.h"
#include <soc/gpio_reg.h>

// DFRobot Fermion C4002 (SEN0691). Protocol read 2026-10-07 and again 2026-10-10
// from DFRobot's own code (all MIT): the DFRobot_C4002 Arduino library, its Python
// port, and the dfrobot_c4002 ESPHome component in DFRobot's fork of ESPHome
// (github.com/cdjq/esphome, branch dev). DFRobot publishes no protocol sheet and
// the wiki has no frame table. None of that code is linked: the Arduino library's
// receive call blocks up to 100 ms whenever the sensor is quiet, reads eight bytes
// blind so a stream split across reads never lines up again, and takes a result
// frame for a command reply. The frame layout below is the same.
//
// Every packet, both directions:
//   FA F5 AA A5 | total length lo, hi | 00 | type | cmd | code | data length lo, hi | data | checksum lo, hi
// total length counts every byte including the checksum; data length counts cmd,
// code and itself (4) plus the data bytes; the checksum is the 16-bit sum of every
// byte before it. type: 00 write request, 01 read request, 02 write reply, 03 read
// reply, 04 notification. code in a reply: 01 = ok. The sensor sends type 04 cmd 60
// (a detection result) every report period once one is set. Its data is 18 bytes,
// packed, as the Python port and the ESPHome component read it byte by byte:
//   0 status (0 nobody, 1 someone still, 2 someone moving)
//   1-2 light, tenths of a lux          3-6 presence gate bits    7-8 presence countdown, s
//   9-10 still person distance, cm      11 still energy 0-99
//   12-13 moving person distance, cm    14-15 moving speed, cm/s, signed
//   16 moving energy 0-99               17 direction (0 away, 1 none, 2 approaching, per both code enums)
// The Arduino library instead copies the bytes over a C struct with padding (20
// bytes); the ESPHome component has that copy commented out and decodes packed,
// which reads as the fix. The count seen is logged once; 18 is right.
// Default speed 115200 (the library's setBaudrate example and the ESPHome yaml).

static const uint8_t HEAD[4] = {0xFA, 0xF5, 0xAA, 0xA5};
enum { T_WRITE = 0, T_READ = 1, T_WRITE_REPLY = 2, T_READ_REPLY = 3, T_NOTE = 4 };
enum { CMD_RESTART = 0x00, CMD_FACTORY_USER = 0x02, NOTE_CALIB = 0x03, CMD_BAUD = 0x21, CMD_RESULT = 0x60, CMD_CALIB = 0x60,
       CMD_RES = 0x66, CMD_FACTORY = 0x80, CMD_VERSION = 0x82, CMD_PERIOD = 0x83, CMD_DELAY = 0x84, CMD_RANGE = 0x86,
       CMD_SENS = 0x87, CMD_OUT_MODE = 0xA0 };

static uint8_t buf[64];
static int have = 0;

static RadarReading rd;                 // the latest decoded result
static uint8_t raw[96];                 // the last bytes heard, newest last, for 'radar raw'
static uint32_t rawN = 0;               // bytes ever written into raw
static uint32_t lastGood = 0, frames = 0, bad = 0, bytes = 0;
static uint32_t fpsFrom = 0, fpsCount = 0;
static float fps = 0;
static volatile int fireRun = 0;        // consecutive readings that passed the rule (read by the machine task)
static volatile bool clearNow = false;  // nobody near (read by the machine task)
static volatile uint32_t goodAt = 0;    // = lastGood, for the machine task
static int rxPin = PIN_RADAR_RX, txPin = PIN_RADAR_TX;
static uint32_t begunAt = 0;
static bool autoProbed = false, setUp = false;
static uint32_t setupAt = 0;            // when first contact was last tried
static int setupFails = 0;              // tries in a row with no answer (the log speaks on the first only)
static int layoutSeen = 0;              // data bytes in the first result frame, logged once
static bool stateWarned = false;        // an unknown status byte, logged once
static uint16_t rangeClosest = 0, rangeFarthest = 0;
static String version;
static int resMode = -1, sensM = -1, sensP = -1, delaySec = -1;   // the sensor's own settings, as last read
static int calibLeft = 0;             // seconds left of a room calibration, from its countdown notes
static bool quietReads = false;       // true while setupSensor reads the sensor's settings, so the reads do not log
static char why[112] = "";              // what the last radar-fired drop saw, for the page
static volatile uint32_t whyAt = 0;

// The last command reply seen, for whoever is waiting on one.
static struct { bool fresh; uint8_t type, cmd, code; uint8_t data[48]; int n; } reply;

static uint16_t le16(const uint8_t *p) { return (uint16_t)(p[0] | (p[1] << 8)); }

// The trigger rule, one reading: someone moving, coming closer, at least 'approach'
// cm/s, and either within 'firecm' (proximity, the owner's rule 2026-10-10: on a 2 m
// overhead mount the slant distance floors near the head and the speed toward the
// sensor fades as a person comes under it, so distance / speed never got small at a
// slow pace) or distance / speed under 'leadms' (a fast walker fires early). Two in a
// row fire (radarFire).
// 'radarinv' swaps approaching and away: DFRobot's code enums say 2 = approaching,
// its Home Assistant tutorial says 0; the bench (S2) settles it without a rebuild.
static void judge() {
  bool moving = rd.state == 2 || rd.state == 3;    // 3 (both) is in the Arduino library's enum, never seen
  bool still  = rd.state == 1 || rd.state == 3;
  if (rd.state > 3 && !stateWarned) { stateWarned = true; logf("[radar] status byte %u is not one DFRobot's code knows (0 nobody, 1 still, 2 moving): treated as nobody", rd.state); }
  rd.dir = rd.dirRaw;
  if (S.radarInv && rd.dirRaw != 1) rd.dir = rd.dirRaw == 2 ? 0 : 2;
  int sp = abs((int)rd.speed);
  rd.etaMs = (moving && rd.dir == 2 && sp > 0 && rd.mdist > 0) ? (int)((long)rd.mdist * 1000 / sp) : 0;
  bool toward = moving && rd.dir == 2 && sp >= S.approach && rd.mdist > 0;
  rd.fire = toward && ((S.fireCm && rd.mdist <= S.fireCm) || (rd.etaMs > 0 && rd.etaMs <= S.leadMs));
  fireRun = rd.fire ? fireRun + 1 : 0;
  // Only a moving person holds the re-arm (owner 2026-10-11: "it needs to have a better
  // self-resetting clear fault function"). A still reading can never fire the rule, which
  // wants someone approaching, and on the bench it held the device for 44 s at 25 to 70 cm.
  (void)still;
  int near = (moving && rd.mdist > 0) ? rd.mdist : 0;   // the nearest moving person, cm; 0 = nobody
  clearNow = near == 0 || near > S.clearCm;
}

static void result(const uint8_t *d, int n) {
  if (n < 18) { bad++; return; }
  if (!layoutSeen) {
    layoutSeen = n;
    logf("[radar] result frames carry %d data bytes%s", n,
         n == 18 ? ", as DFRobot's decoders read them" : " (18 expected: if the readings look wrong, 'radar raw' shows the bytes)");
  }
  rd.state = d[0];
  rd.light = le16(d + 1);  rd.pdist = (int16_t)le16(d + 9);  rd.penergy = d[11];
  rd.mdist = (int16_t)le16(d + 12); rd.speed = (int16_t)le16(d + 14); rd.menergy = d[16]; rd.dirRaw = d[17];
  uint32_t now = millis();
  if (lastGood && now - lastGood > RADAR_RUN_GAP_MS) fireRun = 0;   // "two in a row" means consecutive frames, not across a gap
  judge();
  frames++; fpsCount++;
  lastGood = now; goodAt = now;
}

// A whole packet is in buf: check it, then hand it to the result decoder or park it as a reply.
static void packetDone(int len) {
  uint16_t sum = 0;
  for (int i = 0; i < len - 2; i++) sum += buf[i];
  if (sum != le16(buf + len - 2)) { bad++; return; }
  uint8_t type = buf[7], cmd = buf[8], code = buf[9];
  int dataLen = le16(buf + 10), n = dataLen - 4;
  if (n < 0 || 12 + n > len - 2) { bad++; return; }
  if (type == T_NOTE) {
    if (cmd == CMD_RESULT) result(buf + 12, n);
    else if (cmd == NOTE_CALIB && n >= 2) {        // the sensor counting down a room calibration
      int left = le16(buf + 12);
      if (left != calibLeft) { calibLeft = left; if (left == 0 || left % 5 == 0) logf("[radar] room calibration: %d s left%s", left, left ? "" : ", done"); }
    }
    return;
  }
  reply.type = type; reply.cmd = cmd; reply.code = code;
  reply.n = n < (int)sizeof reply.data ? n : (int)sizeof reply.data;
  memcpy(reply.data, buf + 12, reply.n);
  reply.fresh = true;
}

// Feed one byte to the packet finder.
static void feed(uint8_t c) {
  bytes++;
  raw[rawN++ % sizeof raw] = c;
  if (have < 4) {                       // still looking for FA F5 AA A5
    if (c == HEAD[have]) buf[have++] = c;
    else if (c == HEAD[0]) { buf[0] = c; have = 1; }
    else have = 0;
    return;
  }
  buf[have++] = c;
  if (have == 6) {
    int len = le16(buf + 4);
    if (len < 14 || len > (int)sizeof buf) { bad++; have = 0; return; }
  }
  if (have >= 6 && have == le16(buf + 4)) { packetDone(have); have = 0; }
}

static void pump() { while (Serial2.available()) feed(Serial2.read()); }

static void listen(int rx, int tx) {
  rxPin = rx; txPin = tx;
  Serial2.setRxBufferSize(1024);
  Serial2.begin(RADAR_BAUD, SERIAL_8N1, rx, tx);
  have = 0;
  begunAt = millis();
}

void radarBegin() { listen(PIN_RADAR_RX, PIN_RADAR_TX); }

// ---------------------------------------------------------------- commands

static String hex(const uint8_t *p, int n) {
  String s;
  char b[4];
  for (int i = 0; i < n; i++) { snprintf(b, sizeof b, "%02X ", p[i]); s += b; }
  return s;
}

static void sendPacket(uint8_t type, uint8_t cmd, const uint8_t *d, int n) {
  uint8_t p[64];
  int len = 12 + n + 2;
  memcpy(p, HEAD, 4);
  p[4] = len & 0xFF; p[5] = len >> 8; p[6] = 0; p[7] = type;
  p[8] = cmd; p[9] = 0; p[10] = (4 + n) & 0xFF; p[11] = (4 + n) >> 8;
  if (n) memcpy(p + 12, d, n);
  uint16_t sum = 0;
  for (int i = 0; i < len - 2; i++) sum += p[i];
  p[len - 2] = sum & 0xFF; p[len - 1] = sum >> 8;
  Serial2.write(p, len);
  Serial2.flush();
}

// Send one command and wait for its reply, result frames still decoded meanwhile.
// True when the sensor answered ok; the reply's data stays in 'reply'.
static bool command(uint8_t type, uint8_t cmd, const uint8_t *d, int n, uint32_t waitMs = 300) {
  reply.fresh = false;
  sendPacket(type, cmd, d, n);
  uint32_t t0 = millis();
  while (millis() - t0 < waitMs) {
    pump();
    if (reply.fresh && reply.cmd == cmd && reply.type != T_NOTE) return reply.code == 1;
    delay(1);
  }
  return false;
}

static const char *codeName(uint8_t c) {
  switch (c) {
    case 1: return "ok"; case 2: return "no such command"; case 3: return "bad checksum"; case 4: return "busy";
    case 5: return "bad value"; case 6: return "bad length"; case 7: return "internal error";
  }
  return "no reply";
}

// The outcome of the last command as a word, for a log line.
static const char *outcome(bool ok) { return codeName(ok ? 1 : (reply.fresh ? reply.code : 0)); }

// The reply's data as printable text (a version string), safe inside JSON.
static String replyText() {
  String s;
  for (int i = 0; i < reply.n; i++) { char c = reply.data[i]; if (c >= 0x20 && c < 0x7F && c != '"' && c != '\\') s += c; }
  return s;
}

// First contact, 1.5 s after boot (the sensor takes a moment to wake): report
// every 0.1 s, then its version and detect range for the page. No answer: tried
// again every RADAR_RETRY_MS while no frames arrive (the sensor may boot slower
// than the board, or lose power on its own); the pin fallback carries the trigger
// meanwhile. The log speaks on the first failure and on success.
static void setupSensor() {
  setupAt = millis();
  uint8_t period = RADAR_REPORT_TENTHS;
  bool ok = command(T_WRITE, CMD_PERIOD, &period, 1);
  if (!ok) {
    if (setupFails++ == 0)
      logf("[radar] no answer from the C4002 on GPIO%d/%d at %lu baud (%s): asking again every %d s. Check its 5 V and that TX and RX are crossed; 'radar baud' and 'radar probe' look further",
           rxPin, txPin, (unsigned long)RADAR_BAUD, outcome(ok), RADAR_RETRY_MS / 1000);
    return;
  }
  setupFails = 0;
  uint8_t sw = 1;
  if (command(T_READ, CMD_VERSION, &sw, 1)) version = replyText();
  if (command(T_READ, CMD_RANGE, nullptr, 0) && reply.n >= 4) { rangeClosest = le16(reply.data); rangeFarthest = le16(reply.data + 2); }
  quietReads = true; radarRes(-1); radarSens(0, -1); radarSens(1, -1); radarDelay(-1); quietReads = false;
  logf("[radar] C4002 answers: reporting every %d ms, version %s, detect range %u to %u cm",
       RADAR_REPORT_TENTHS * 100, version.length() ? version.c_str() : "?", rangeClosest, rangeFarthest);
}

void radarPoll() {
  pump();
  uint32_t now = millis();
  if (!setUp && now - begunAt > 1500) { setUp = true; setupSensor(); }
  else if (setUp && S.sensor == 4002 && !radarTalking() && now - setupAt >= RADAR_RETRY_MS) setupSensor();
  // Nothing at all heard 3 s after starting: look for the signal once by itself.
  if (!autoProbed && !bytes && now - begunAt > 3000) { autoProbed = true; logf("[radar] nothing heard on RX2 in 3 s, looking for the signal"); radarProbe(); return; }
  if (now - fpsFrom >= 1000) { fps = fpsCount * 1000.0f / (now - fpsFrom); fpsCount = 0; fpsFrom = now; }
}

bool radarTalking() { uint32_t g = goodAt; return g && millis() - g < RADAR_SILENT_MS; }
bool radarFire()    { return radarTalking() && fireRun >= 2; }
bool radarClear()   { return radarTalking() && clearNow; }

// Called by the machine task the moment a drop starts on the sensor: keep what the
// radar saw, in words, for the page's "last drop fired by the radar" row.
void radarMarkFire(bool viaLink) {
  if (viaLink) {
    RadarReading r = rd;
    snprintf(why, sizeof why, "%d cm away, %d cm/s %s, %d ms before arrival, two readings in a row",
             r.mdist, abs((int)r.speed), r.dir == 2 ? "approaching" : r.dir == 0 ? "going away" : "no direction", r.etaMs);
  } else {
    snprintf(why, sizeof why, "OUT pin high on GPIO33 (serial link %s)", S.sensor == 4002 ? "silent" : "not used, sensor 2410");
  }
  whyAt = millis();
}

// Where is the sensor's signal? Its TX idles high and sends a burst every report
// period, so the pin it is on flips many times in 400 ms while sitting mostly high.
// Only pins this firmware does not use are read, as plain inputs (pulled down where
// the chip can, so a loose pin reads quiet). If the signal is found, listen there:
// on GPIO17 that means the TX and RX wires are swapped, and the firmware swaps them.
static const int PROBE_PINS[] = {16, 17, 4, 5, 12, 14, 15, 18, 19, 21, 22, 23, 34, 35, 36, 39};

int radarProbe() {
  Serial2.end();
  const int N = sizeof PROBE_PINS / sizeof PROBE_PINS[0];
  uint32_t edges[N] = {0}, highs[N] = {0}, samples = 0;
  for (int i = 0; i < N; i++) pinMode(PROBE_PINS[i], PROBE_PINS[i] >= 34 ? INPUT : INPUT_PULLDOWN);
  delay(5);
  uint64_t prev = ((uint64_t)REG_READ(GPIO_IN1_REG) << 32) | REG_READ(GPIO_IN_REG);
  uint32_t t0 = millis();
  while (millis() - t0 < 400) {
    uint64_t now = ((uint64_t)REG_READ(GPIO_IN1_REG) << 32) | REG_READ(GPIO_IN_REG);
    uint64_t diff = now ^ prev;
    for (int i = 0; i < N; i++) {
      uint64_t b = 1ULL << PROBE_PINS[i];
      if (diff & b) edges[i]++;
      if (now & b) highs[i]++;
    }
    prev = now; samples++;
  }
  int found = -1;
  for (int i = 0; i < N; i++) {
    bool mostlyHigh = highs[i] * 10 > samples * 8;
    if (edges[i] >= 100 && mostlyHigh && found < 0) found = PROBE_PINS[i];
    if (edges[i]) logf("[radar] GPIO%d: %lu changes, high %d%% of the time%s", PROBE_PINS[i], (unsigned long)edges[i],
                       (int)(highs[i] * 100 / samples), found == PROBE_PINS[i] ? "  <- sensor signal" : "");
  }
  if (found < 0) {
    logf("[radar] no signal on any free pin: the sensor has no 5 V, is not reporting yet (it reports only once asked), or its TX wire reaches no pin");
    listen(PIN_RADAR_RX, PIN_RADAR_TX);
  } else if (found == PIN_RADAR_RX) {
    logf("[radar] signal on GPIO%d (RX2), where it belongs", found);
    listen(PIN_RADAR_RX, PIN_RADAR_TX);
  } else {
    int tx = found == PIN_RADAR_TX ? PIN_RADAR_RX : PIN_RADAR_TX;
    logf("[radar] signal on GPIO%d, not RX2: listening there%s", found,
         found == PIN_RADAR_TX ? " (the TX and RX wires are swapped at the board; fine as is, or swap them back)" : "");
    listen(found, tx);
  }
  setUp = false;                        // first contact again on the new pins
  return found;
}

// Show the last bytes heard on RX2, oldest first.
void radarRaw() {
  uint32_t n = rawN < sizeof raw ? rawN : sizeof raw;
  if (!n) { logf("[radar] raw: nothing heard yet"); return; }
  uint8_t out[sizeof raw];
  for (uint32_t i = 0; i < n; i++) out[i] = raw[(rawN - n + i) % sizeof raw];
  logf("[radar] raw: last %lu of %lu bytes heard (FA F5 AA A5 starts a packet; its 8th byte 04 = a result, 02 or 03 = a reply):", (unsigned long)n, (unsigned long)rawN);
  for (uint32_t i = 0; i < n; i += 24) logf("  %s", hex(out + i, (n - i) < 24 ? (n - i) : 24).c_str());
}

// Try each speed the sensor knows; the one where a detect-range read answers is
// its speed. If it is not RADAR_BAUD, set RADAR_BAUD (takes effect after a restart).
static const uint32_t BAUDS[] = {115200, 57600, 230400, 460800, 500000, 921600, 1000000};
void radarBaud() {
  uint32_t found = 0;
  for (uint32_t b : BAUDS) {
    Serial2.end();
    Serial2.begin(b, SERIAL_8N1, rxPin, txPin);
    delay(20);
    while (Serial2.available()) Serial2.read();
    have = 0;
    bool ok = command(T_READ, CMD_RANGE, nullptr, 0, 200);
    logf("[radar] %lu baud: %s%s", (unsigned long)b, ok ? "answers" : "nothing", ok ? "  <- it is here" : "");
    if (ok) { found = b; break; }
  }
  if (!found) {
    logf("[radar] no speed answers: the sensor is off, still booting, or its RX wire (GPIO%d) is open", txPin);
    listen(rxPin, txPin);
    return;
  }
  if (found == RADAR_BAUD) { logf("[radar] speed is already %lu; nothing changed", (unsigned long)found); listen(rxPin, txPin); setUp = false; return; }
  uint32_t want = RADAR_BAUD;
  uint8_t v[4] = {(uint8_t)want, (uint8_t)(want >> 8), (uint8_t)(want >> 16), (uint8_t)(want >> 24)}, zero = 0;
  logf("[radar] set speed %lu: %s", (unsigned long)want, outcome(command(T_WRITE, CMD_BAUD, v, 4)));
  logf("[radar] restart: %s", outcome(command(T_WRITE, CMD_RESTART, &zero, 1)));
  listen(rxPin, txPin);
  setUp = false;                        // first contact again at the new speed
}

void radarVersion() {
  uint8_t which = 1;
  for (int k = 0; k < 2; k++, which = 0) {
    bool ok = command(T_READ, CMD_VERSION, &which, 1);
    if (ok) {
      String s = replyText();
      if (which == 1) version = s;
      logf("[radar] %s version: %s", which == 1 ? "software" : "hardware", s.c_str());
    } else logf("[radar] %s version: %s", which == 1 ? "software" : "hardware", outcome(ok));
  }
}

// The sensor's own detect range, cm, 0 to 1100. Set the closest value past the
// hanging spider so the sensor never reports it; kept by the sensor, not by us.
void radarRange(int closest, int farthest) {
  if (closest >= 0 && farthest >= 0) {
    if (closest > farthest || farthest > 1100) { logf("radar range: closest then farthest, 0 to 1100 cm, e.g. radar range 60 600"); return; }
    uint8_t v[4] = {(uint8_t)closest, (uint8_t)(closest >> 8), (uint8_t)farthest, (uint8_t)(farthest >> 8)};
    bool set = command(T_WRITE, CMD_RANGE, v, 4);
    logf("[radar] set detect range %d to %d cm: %s", closest, farthest, outcome(set));
    // Bench 2026-10-10: the sensor answers ok but keeps reporting the old range until it
    // restarts (a reading at 230 cm stayed through a 0 to 200 set, and went with the restart).
    if (set) {
      uint8_t zero = 0;
      logf("[radar] restarting the sensor so the range takes effect: %s", outcome(command(T_WRITE, CMD_RESTART, &zero, 1)));
      delay(1500);
      pump();
    }
  }
  bool ok = command(T_READ, CMD_RANGE, nullptr, 0);
  if (ok && reply.n >= 4) {
    rangeClosest = le16(reply.data); rangeFarthest = le16(reply.data + 2);
    logf("[radar] detect range now %u to %u cm", rangeClosest, rangeFarthest);
  } else logf("[radar] detect range: %s", outcome(ok));
}

// The OUT pin's rule, kept by the sensor: 1 = high on motion, 2 = high on presence, 3 = either.
void radarOut(int mode) {
  if (mode) {
    if (mode < 1 || mode > 3) { logf("radar out: 1 motion, 2 presence, 3 either"); return; }
    uint8_t m = mode;
    logf("[radar] set OUT pin rule %d: %s", mode, outcome(command(T_WRITE, CMD_OUT_MODE, &m, 1)));
  }
  bool ok = command(T_READ, CMD_OUT_MODE, nullptr, 0);
  if (ok && reply.n >= 1)
    logf("[radar] OUT pin goes high on %s", reply.data[0] == 1 ? "motion" : reply.data[0] == 2 ? "presence" : reply.data[0] == 3 ? "motion or presence" : "?");
  else logf("[radar] OUT pin rule: %s", outcome(ok));
}

// The sensor's range step (DFRobot "resolution mode"): 80 cm steps, 15 of them to
// 11.6 m, or 20 cm steps, 25 of them to 4.9 m. The detect range and the clear
// distance both round to a step, so 20 cm steps let a close cut-off land where it
// is set (the office mirror at 2.2 m stayed through a 200 cm cap on 80 cm steps).
void radarRes(int mode) {
  bool talk = mode >= 0 || !quietReads;
  if (mode >= 0) {
    if (mode > 1) { logf("radar res: 80 (steps to 11.6 m) or 20 (steps to 4.9 m)"); return; }
    uint8_t m = mode;
    logf("[radar] set range step %s cm: %s", mode ? "20" : "80", outcome(command(T_WRITE, CMD_RES, &m, 1)));
  }
  bool ok = command(T_READ, CMD_RES, nullptr, 0);
  if (ok && reply.n >= 1) { resMode = reply.data[0] ? 1 : 0; if (talk) logf("[radar] range step now %s cm", resMode ? "20" : "80"); }
  else if (talk) logf("[radar] range step: %s", outcome(ok));
}

// The sensor learns the empty room (DFRobot "environment calibration"): it waits
// delaySec so whoever pressed the button can leave, then listens contSec and sets
// its own per-step thresholds from the noise it hears. Nobody in view meanwhile.
// It counts down in notes (cmd 03), logged every 5 s.
void radarCalib(int delaySec, int contSec) {
  if (delaySec < 0 || delaySec > 600 || contSec < 5 || contSec > 600) { logf("radar calib: delay seconds then listen seconds, e.g. radar calib 10 30"); return; }
  uint8_t v[5] = {(uint8_t)delaySec, (uint8_t)(delaySec >> 8), (uint8_t)contSec, (uint8_t)(contSec >> 8), 1};
  bool ok = command(T_WRITE, CMD_CALIB, v, 5);
  logf("[radar] room calibration: %s. Leave the view for the next %d s", outcome(ok), delaySec + contSec);
  if (ok) calibLeft = delaySec + contSec;
}

// Sensitivity, one of DFRobot's threshold groups, for the motion reading (gate 0)
// and the still-person reading (gate 1): 0 low, 1 mid, 2 high; 3 = the custom set
// a room calibration leaves behind.
static const char *sensName(int g) { return g == 0 ? "low" : g == 1 ? "mid" : g == 2 ? "high" : g == 3 ? "custom (from calibration)" : "?"; }
void radarSens(int gate, int group) {
  if (gate < 0 || gate > 1) return;
  bool talk = group >= 0 || !quietReads;
  if (group >= 0) {
    if (group > 2) { logf("radar sens: motion or presence, then low, mid or high"); return; }
    uint8_t v[2] = {(uint8_t)gate, (uint8_t)group};
    logf("[radar] set %s sensitivity %s: %s", gate ? "presence" : "motion", sensName(group), outcome(command(T_WRITE, CMD_SENS, v, 2)));
  }
  uint8_t q[2] = {(uint8_t)gate, 0};
  bool ok = command(T_READ, CMD_SENS, q, 2);
  if (ok && reply.n >= 2) { (gate ? sensP : sensM) = reply.data[1]; if (talk) logf("[radar] %s sensitivity now %s", gate ? "presence" : "motion", sensName(reply.data[1])); }
  else if (talk) logf("[radar] %s sensitivity: %s", gate ? "presence" : "motion", outcome(ok));
}

// How long the sensor keeps reporting a person after it last saw one (DFRobot
// "target disappear delay"), seconds. Shorter = the doorway reads clear sooner.
void radarDelay(int sec) {
  bool talk = sec >= 0 || !quietReads;
  if (sec >= 0) {
    if (sec > 600) { logf("radar delay: 0 to 600 seconds"); return; }
    uint8_t v[2] = {(uint8_t)sec, (uint8_t)(sec >> 8)};
    logf("[radar] set disappear delay %d s: %s", sec, outcome(command(T_WRITE, CMD_DELAY, v, 2)));
  }
  bool ok = command(T_READ, CMD_DELAY, nullptr, 0);
  if (ok && reply.n >= 2) { delaySec = le16(reply.data); if (talk) logf("[radar] disappear delay now %d s", delaySec); }
  else if (talk) logf("[radar] disappear delay: %s", outcome(ok));
}

// Factory settings (two steps, as DFRobot's library does it), then restart.
void radarReset() {
  uint8_t zero = 0;
  logf("[radar] factory reset step 1: %s", outcome(command(T_WRITE, CMD_FACTORY_USER, &zero, 1)));
  delay(50);
  logf("[radar] factory reset step 2: %s", outcome(command(T_WRITE, CMD_FACTORY, &zero, 1)));
  delay(50);
  logf("[radar] restart: %s", outcome(command(T_WRITE, CMD_RESTART, &zero, 1)));
  version = ""; rangeClosest = rangeFarthest = 0; resMode = sensM = sensP = delaySec = -1; calibLeft = 0;
  setUp = false; begunAt = millis();    // first contact again once it is back
}

// Any one command by hand: "radar cmd r 82 01" reads the software version,
// "radar cmd w 83 0A" sets the report period to 1 s. Replies are logged as hex.
void radarCmd(const String &a) {
  String s = a; s.trim(); s.toLowerCase();
  if (s.length() < 4 || (s[0] != 'r' && s[0] != 'w') || s[1] != ' ') { logf("radar cmd: r or w, the command byte, then data bytes as hex, e.g. radar cmd r 82 01"); return; }
  String h = s.substring(2); h.replace(" ", "");
  if (h.length() < 2 || h.length() % 2 || h.length() > 2 + 2 * 32) { logf("radar cmd: whole hex bytes, e.g. radar cmd w 83 0A"); return; }
  uint8_t b[33]; int n = 0;
  for (unsigned i = 0; i < h.length(); i += 2) b[n++] = (uint8_t)strtoul(h.substring(i, i + 2).c_str(), nullptr, 16);
  command(s[0] == 'r' ? T_READ : T_WRITE, b[0], n > 1 ? b + 1 : nullptr, n - 1);
  if (!reply.fresh) { logf("[radar] command %02X: no reply in 300 ms", b[0]); return; }
  logf("[radar] command %02X: %s, %d data bytes%s%s", b[0], codeName(reply.code), reply.n, reply.n ? ": " : "", reply.n ? hex(reply.data, reply.n < 40 ? reply.n : 40).c_str() : "");
}

RadarStats radarStats() {
  RadarStats r;
  uint32_t now = millis();
  r.ageMs = lastGood ? now - lastGood : 0;
  r.talking = lastGood && r.ageMs < RADAR_SILENT_MS;
  r.fps = r.talking ? fps : 0;
  r.frames = frames; r.bad = bad; r.bytes = bytes;
  r.fireRun = r.talking ? fireRun : 0;
  r.r = rd;
  if (!r.talking) { r.r.fire = false; r.r.etaMs = 0; }
  r.closest = rangeClosest; r.farthest = rangeFarthest;
  r.version = version;
  r.res = resMode; r.sensM = sensM; r.sensP = sensP; r.delaySec = delaySec; r.calibLeft = calibLeft;
  r.why = why;
  r.whyAgoMs = whyAt ? now - whyAt : 0;
  return r;
}

String radarJson() {
  RadarStats r = radarStats();
  String j = "{\"talking\":" + String(r.talking) + ",\"age\":" + String(r.ageMs) + ",\"fps\":" + String(r.fps, 1) +
             ",\"frames\":" + String(r.frames) + ",\"bad\":" + String(r.bad) + ",\"bytes\":" + String(r.bytes) +
             ",\"layout\":" + String(layoutSeen);
  if (r.talking) {
    j += ",\"state\":" + String(r.r.state) + ",\"mdist\":" + String(r.r.mdist) + ",\"speed\":" + String(r.r.speed) +
         ",\"dir\":" + String(r.r.dir) + ",\"rawdir\":" + String(r.r.dirRaw) + ",\"menergy\":" + String(r.r.menergy) +
         ",\"pdist\":" + String(r.r.pdist) + ",\"penergy\":" + String(r.r.penergy) + ",\"light\":" + String(r.r.light / 10.0f, 1) +
         ",\"eta\":" + String(r.r.etaMs) + ",\"fire\":" + String(r.r.fire) + ",\"run\":" + String(r.fireRun) +
         ",\"clear\":" + String(clearNow);
  }
  j += ",\"res\":" + String(r.res) + ",\"sensm\":" + String(r.sensM) + ",\"sensp\":" + String(r.sensP) + ",\"delay\":" + String(r.delaySec) + ",\"calib\":" + String(r.calibLeft);
  j += ",\"closest\":" + String(r.closest) + ",\"farthest\":" + String(r.farthest) + ",\"ver\":\"" + r.version + "\"" +
       ",\"why\":\"" + r.why + "\",\"whyAgo\":" + String(r.whyAgoMs) + "}";
  return j;
}
