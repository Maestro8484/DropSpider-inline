// HLK-LD2450 radar on UART2, read for the web page's radar view and the 'radar'
// console command. Watch only: it does not fire the drop yet (roadmap task 4);
// the drop is still fired by the GPIO33 line.
#pragma once
#include <Arduino.h>

struct RadarTarget {
  int16_t  x, y;        // mm: x across the sensor's face, y straight out from it
  int16_t  speed;       // cm/s as the sensor reports it; which sign means "coming closer" is test S2
  uint16_t gate;        // mm, the sensor's distance-gate size; 0 = empty slot
  bool present() const { return x || y || gate; }
};

struct RadarStats {
  bool     talking;     // a good frame within RADAR_SILENT_MS
  uint32_t ageMs;       // since the last good frame (0 if none yet)
  float    fps;         // good frames in the last second
  uint32_t frames, bad, bytes;
  int      count;       // targets in the last frame
  RadarTarget t[3];
};

void radarBegin();      // call once from setup()
void radarPoll();       // call from loop(): reads whatever the UART holds
RadarStats radarStats();
String radarJson();     // {"talking":..,"age":..,"fps":..,"frames":..,"bad":..,"bytes":..,"t":[[x,y,speed,gate] or null, x3 slots]}
