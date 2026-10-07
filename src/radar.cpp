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

void radarPoll() {
  while (Serial2.available()) {
    uint8_t c = Serial2.read();
    bytes++;
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
