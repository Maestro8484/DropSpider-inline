#include "radar.h"
#include "config.h"
#include "console.h"
#include <soc/gpio_reg.h>

// The LD2450 streams from power-up, no command needed, 10 frames a second at
// 256000 baud. Frame layout from Hi-Link's manual (section 6, tables 2 and 3):
//   AA FF 03 00 | 3 targets x 8 bytes | 55 CC        (30 bytes)
// Each target is four little-endian 16-bit fields: X, Y, speed, gate size. In X,
// Y and speed, bit 15 set means positive and the other 15 bits are the size.
// Units mm, mm, cm/s, mm. An empty slot is all zeros.
//
// Existing parsers looked at 2026-10-06: ESPHome's ld2450 component (GPL, needs
// ESPHome, read for its decode only), PeterkoCZ91/HLK-LD2450-security (MIT, but a
// whole security system around it), RBEGamer/HLK-LD2450 (MIT, reads past the end
// of its buffer and drops frames split across reads). The frame is simple enough
// that the parser below, written to the manual, is smaller than any of them.

static const uint8_t HEAD[4] = {0xAA, 0xFF, 0x03, 0x00};
static uint8_t buf[30];
static int have = 0;

static RadarTarget tgt[3];
static uint8_t raw[96];                 // the last bytes heard, newest last, for 'radar raw'
static uint32_t rawN = 0;               // bytes ever written into raw
static uint32_t lastGood = 0, frames = 0, bad = 0, bytes = 0;
static uint32_t fpsFrom = 0, fpsCount = 0;
static float fps = 0;
static int rxPin = PIN_RADAR_RX, txPin = PIN_RADAR_TX;
static uint32_t begunAt = 0;
static bool autoProbed = false;

static int16_t decode(uint8_t lo, uint8_t hi) {
  int16_t v = (int16_t)(((hi & 0x7F) << 8) | lo);
  return (hi & 0x80) ? v : (int16_t)-v;
}

static void frameDone() {
  if (buf[28] != 0x55 || buf[29] != 0xCC) { bad++; return; }
  for (int i = 0; i < 3; i++) {
    const uint8_t *p = buf + 4 + i * 8;
    tgt[i].x = decode(p[0], p[1]);
    tgt[i].y = decode(p[2], p[3]);
    tgt[i].speed = decode(p[4], p[5]);
    tgt[i].gate = (uint16_t)(p[6] | (p[7] << 8));
  }
  frames++; fpsCount++;
  lastGood = millis();
}

static void listen(int rx, int tx) {
  rxPin = rx; txPin = tx;
  Serial2.setRxBufferSize(1024);
  Serial2.begin(RADAR_BAUD, SERIAL_8N1, rx, tx);
  begunAt = millis();
}

void radarBegin() { listen(PIN_RADAR_RX, PIN_RADAR_TX); }

// Where is the radar's signal? Its TX idles high and sends about 10 bursts a second,
// so the pin it is on flips hundreds of times in 400 ms while sitting mostly high.
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
  String quiet;
  for (int i = 0; i < N; i++) {
    bool mostlyHigh = highs[i] * 10 > samples * 8;
    if (edges[i] >= 100 && mostlyHigh && found < 0) found = PROBE_PINS[i];
    if (edges[i]) logf("[radar] GPIO%d: %lu changes, high %d%% of the time%s", PROBE_PINS[i], (unsigned long)edges[i],
                       (int)(highs[i] * 100 / samples), found == PROBE_PINS[i] ? "  <- radar signal" : "");
  }
  if (found < 0) {
    logf("[radar] no radar signal on any free pin: the LD2450 has no 5 V, or its yellow TX wire reaches no pin");
    listen(PIN_RADAR_RX, PIN_RADAR_TX);
  } else if (found == PIN_RADAR_RX) {
    logf("[radar] signal on GPIO%d (RX2), where it belongs", found);
    listen(PIN_RADAR_RX, PIN_RADAR_TX);
  } else {
    int tx = found == PIN_RADAR_TX ? PIN_RADAR_RX : PIN_RADAR_TX;
    logf("[radar] signal on GPIO%d, not RX2: listening there%s", found,
         found == PIN_RADAR_TX ? " (the yellow and green wires are swapped at the board; fine as is, or swap them back)" : "");
    listen(found, tx);
  }
  return found;
}

// Talk to the radar over its RX wire (ESP32 TX2). Command frames, from Hi-Link's
// serial protocol as ESPHome's ld2450 component sends them (read 2026-10-07):
//   FD FC FB FA | len lo, len hi | cmd, 00 | value bytes | 04 03 02 01
// A command only works inside configuration mode (cmd FF, value 01 00), and in that
// mode the radar stops its 10 Hz target frames until end configuration (FE) or a
// restart (A3). The reply to any command is a frame with the same header, cmd | 0x100
// and a status word of 00 00 for ok. Version reply: 6 bytes from offset 12.
static void sendCmd(uint8_t cmd, const uint8_t *val, int n) {
  uint8_t head[8] = {0xFD, 0xFC, 0xFB, 0xFA, (uint8_t)(2 + n), 0x00, cmd, 0x00};
  static const uint8_t foot[4] = {0x04, 0x03, 0x02, 0x01};
  Serial2.write(head, 8);
  if (n) Serial2.write(val, n);
  Serial2.write(foot, 4);
  Serial2.flush();
}

// Read everything the radar sends in the next ms; keep the first cap bytes; return the count.
static int gather(uint32_t ms, uint8_t *out, int cap) {
  int n = 0;
  uint32_t t0 = millis();
  while (millis() - t0 < ms) {
    while (Serial2.available()) { uint8_t c = Serial2.read(); if (n < cap) out[n] = c; n++; }
    delay(1);
  }
  return n;
}

static String hex(const uint8_t *p, int n) {
  String s;
  char b[4];
  for (int i = 0; i < n; i++) { snprintf(b, sizeof b, "%02X ", p[i]); s += b; }
  return s;
}

static bool hasFrame(const uint8_t *r, int n) {
  for (int i = 0; i + 3 < n; i++) if (r[i] == 0xAA && r[i + 1] == 0xFF && r[i + 2] == 0x03 && r[i + 3] == 0x00) return true;
  return false;
}

// Send one command inside configuration mode (already entered) and log its reply as hex.
static void ask(const char *what, uint8_t cmd, const uint8_t *val, int n) {
  uint8_t r[64];
  sendCmd(cmd, val, n);
  int got = gather(150, r, sizeof r);
  logf("[radar] %s: %d bytes back%s%s", what, got, got ? ": " : "", got ? hex(r, got < 40 ? got : 40).c_str() : "");
}

// The line idles high but never changes: the radar is powered and silent. Ask it to
// speak: version (proves the green wire and its serial port both work), then end
// configuration mode, then a restart if it still sends no target frames.
void radarWake() {
  static const uint8_t one[2] = {0x01, 0x00};
  uint8_t r[64];
  int n;
  logf("[radar] wake: sending on GPIO%d (TX2), listening on GPIO%d", txPin, rxPin);
  while (Serial2.available()) Serial2.read();

  sendCmd(0xFF, one, 2);                              // enable configuration
  n = gather(150, r, sizeof r);
  logf("[radar] enable configuration: %d bytes back%s%s", n, n ? ": " : "", n ? hex(r, n < 24 ? n : 24).c_str() : "");
  if (!n) {
    logf("[radar] no reply at all: the green wire (RX on the radar, TX2 on the ESP32) is open, or the radar's serial port is dead. Its Bluetooth being alive says the chip runs");
    return;
  }

  sendCmd(0xA0, nullptr, 0);                          // read firmware version
  n = gather(150, r, sizeof r);
  int at = -1;
  for (int i = 0; i + 17 < n; i++)
    if (r[i] == 0xFD && r[i + 1] == 0xFC && r[i + 2] == 0xFB && r[i + 3] == 0xFA && r[i + 6] == 0xA0 && r[i + 7] == 0x01) { at = i; break; }
  if (at >= 0) {
    const uint8_t *v = r + at + 12;
    logf("[radar] firmware V%u.%02X.%02X%02X%02X%02X (ESPHome wants V2.02.23090617 or later)", v[1], v[0], v[5], v[4], v[3], v[2]);
  } else logf("[radar] version: %d bytes back%s%s", n, n ? ": " : "", n ? hex(r, n < 24 ? n : 24).c_str() : "");

  // State that could silence it: tracking mode (reply ... 01 00 = single, 02 00 = multi) and
  // the area setting (reply: 2-byte type, 0 = off, 1 = detect only inside, 2 = ignore inside, then 3 boxes).
  ask("tracking mode", 0x91, nullptr, 0);
  ask("area setting", 0xC1, nullptr, 0);

  sendCmd(0xFE, nullptr, 0);                          // end configuration
  n = gather(600, r, sizeof r);
  bool frames = hasFrame(r, n < (int)sizeof r ? n : sizeof r);
  logf("[radar] end configuration: %d bytes in 0.6 s%s", n, frames ? ", target frames are flowing" : ", still no target frames");
  if (!frames) {
    sendCmd(0xFF, one, 2);
    gather(100, r, sizeof r);
    sendCmd(0xA3, nullptr, 0);                        // restart the module
    n = gather(3000, r, sizeof r);
    frames = hasFrame(r, n < (int)sizeof r ? n : sizeof r);
    logf("[radar] restart: %d bytes in 3 s%s", n, frames ? ", target frames are flowing" : ", still no target frames: it answers commands but will not report; 'radar reset' puts its settings back to factory");
  }
  have = 0;
}

// Show the last bytes heard on RX2, oldest first, with the frame headers named.
void radarRaw() {
  uint32_t n = rawN < sizeof raw ? rawN : sizeof raw;
  if (!n) { logf("[radar] raw: nothing heard yet"); return; }
  uint8_t out[sizeof raw];
  for (uint32_t i = 0; i < n; i++) out[i] = raw[(rawN - n + i) % sizeof raw];
  logf("[radar] raw: last %lu of %lu bytes heard (FD FC FB FA = command reply, AA FF 03 00 = position frame):", (unsigned long)n, (unsigned long)rawN);
  for (uint32_t i = 0; i < n; i += 24) logf("  %s", hex(out + i, (n - i) < 24 ? (n - i) : 24).c_str());
}

// A firmware update can leave the module at another speed (reported for V2.14 and
// later). Try enable configuration at each speed the module knows; the one that
// answers is its speed. If it is not 256000, set 256000 (A1, index 7) and restart.
static const uint32_t BAUDS[] = {256000, 115200, 230400, 460800, 57600, 38400, 19200, 9600};
void radarBaud() {
  static const uint8_t one[2] = {0x01, 0x00};
  static const uint8_t idx256k[2] = {0x07, 0x00};
  uint8_t r[64];
  uint32_t found = 0;
  for (uint32_t b : BAUDS) {
    Serial2.end();
    Serial2.begin(b, SERIAL_8N1, rxPin, txPin);
    delay(20);
    while (Serial2.available()) Serial2.read();
    sendCmd(0xFF, one, 2);
    int n = gather(150, r, sizeof r);
    bool ack = false;
    for (int i = 0; i + 3 < n && i + 3 < (int)sizeof r; i++) if (r[i] == 0xFD && r[i + 1] == 0xFC && r[i + 2] == 0xFB && r[i + 3] == 0xFA) { ack = true; break; }
    logf("[radar] %lu baud: %d bytes back%s", (unsigned long)b, n, ack ? "  <- it answers here" : "");
    if (ack) { found = b; break; }
  }
  if (!found) {
    logf("[radar] no speed answers: the module is not listening (mid-update, rebooting, held by the phone, or off)");
    listen(rxPin, txPin);
    return;
  }
  if (found == RADAR_BAUD) {
    sendCmd(0xFE, nullptr, 0);
    gather(150, r, sizeof r);
    logf("[radar] speed is already %lu; nothing changed", (unsigned long)found);
    listen(rxPin, txPin);
    return;
  }
  ask("set speed 256000", 0xA1, idx256k, 2);
  ask("restart", 0xA3, nullptr, 0);
  listen(rxPin, txPin);                               // back to 256000
  int n = gather(3000, r, sizeof r);
  logf("[radar] after the speed change: %d bytes in 3 s at 256000%s", n, hasFrame(r, n < (int)sizeof r ? n : sizeof r) ? ", target frames are flowing" : ", no target frames yet");
  have = 0;
}

// Factory reset (A2) then restart: every setting the module keeps (tracking mode, area
// boxes, baud rate, Bluetooth) goes back to how it shipped. Nothing of ours is stored in it.
void radarReset() {
  static const uint8_t one[2] = {0x01, 0x00};
  uint8_t r[64];
  int n;
  logf("[radar] reset: factory settings, then restart");
  while (Serial2.available()) Serial2.read();
  sendCmd(0xFF, one, 2);
  n = gather(150, r, sizeof r);
  if (!n) { logf("[radar] no reply to enable configuration: nothing reached it (see 'radar wake')"); return; }
  ask("factory reset", 0xA2, nullptr, 0);
  ask("restart", 0xA3, nullptr, 0);
  n = gather(5000, r, sizeof r);
  bool frames = hasFrame(r, n < (int)sizeof r ? n : sizeof r);
  logf("[radar] after the reset: %d bytes in 5 s%s", n, frames ? ", target frames are flowing" : ", still no target frames");
  have = 0;
}

void radarPoll() {
  while (Serial2.available()) {
    uint8_t c = Serial2.read();
    bytes++;
    raw[rawN++ % sizeof raw] = c;
    if (have < 4) {                       // still looking for AA FF 03 00
      if (c == HEAD[have]) buf[have++] = c;
      else if (c == HEAD[0]) { buf[0] = c; have = 1; }
      else have = 0;
      continue;
    }
    buf[have++] = c;
    if (have == (int)sizeof buf) { frameDone(); have = 0; }
  }
  uint32_t now = millis();
  // Nothing at all heard 3 s after starting: look for the signal once by itself.
  if (!autoProbed && !bytes && now - begunAt > 3000) { autoProbed = true; logf("[radar] nothing heard on RX2 in 3 s, looking for the signal"); radarProbe(); return; }
  if (now - fpsFrom >= 1000) { fps = fpsCount * 1000.0f / (now - fpsFrom); fpsCount = 0; fpsFrom = now; }
}

RadarStats radarStats() {
  RadarStats r;
  uint32_t now = millis();
  r.ageMs = lastGood ? now - lastGood : 0;
  r.talking = lastGood && r.ageMs < RADAR_SILENT_MS;
  r.fps = r.talking ? fps : 0;
  r.frames = frames; r.bad = bad; r.bytes = bytes;
  r.count = 0;
  for (int i = 0; i < 3; i++) {
    r.t[i] = tgt[i];
    if (r.talking && tgt[i].present()) r.count++;
  }
  return r;
}

String radarJson() {
  RadarStats r = radarStats();
  String j = "{\"talking\":" + String(r.talking) + ",\"age\":" + String(r.ageMs) + ",\"fps\":" + String(r.fps, 1) +
             ",\"frames\":" + String(r.frames) + ",\"bad\":" + String(r.bad) + ",\"bytes\":" + String(r.bytes) + ",\"t\":[";
  for (int i = 0; i < 3; i++) {                     // slot order kept, so the page can draw each one's trail
    if (i) j += ",";
    if (!r.talking || !r.t[i].present()) { j += "null"; continue; }
    j += "[" + String(r.t[i].x) + "," + String(r.t[i].y) + "," + String(r.t[i].speed) + "," + String(r.t[i].gate) + "]";
  }
  return j + "]}";
}
