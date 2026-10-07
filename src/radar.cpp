#include "radar.h"
#include "config.h"

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

void radarBegin() {
  Serial2.setRxBufferSize(1024);
  Serial2.begin(RADAR_BAUD, SERIAL_8N1, PIN_RADAR_RX, PIN_RADAR_TX);
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
