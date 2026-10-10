// DFRobot Fermion C4002 radar (SEN0691) on UART2: the trigger when the setting
// 'sensor' is 4002. It reports one moving person's distance, speed and direction
// and one still person's distance, about 10 times a second once asked to. The
// machine task reads radarFire() and radarClear(); the web page reads radarJson().
// If the serial link goes silent for RADAR_SILENT_MS the machine falls back to the
// sensor's OUT pin on GPIO33.
#pragma once
#include <Arduino.h>

struct RadarReading {
  uint8_t  state;       // 0 nobody, 1 someone still (presence), 2 someone moving
  int16_t  mdist;       // cm, the moving person
  int16_t  speed;       // cm/s, the moving person, sign as the sensor gives it
  uint8_t  dirRaw;      // the sensor's own direction word: 0 away, 1 no direction, 2 approaching (per DFRobot's code)
  uint8_t  dir;         // the direction the rule uses: dirRaw, swapped when the setting 'radarinv' is 1
  uint8_t  menergy;     // 0 to 99, how sure the sensor is of the moving person
  int16_t  pdist;       // cm, the still person
  uint8_t  penergy;     // 0 to 99
  uint16_t light;       // tenths of a lux, the sensor's own light sensor
  bool     fire;        // this reading passes the trigger rule (approaching, fast enough, arriving soon enough)
  int      etaMs;       // distance / speed, 0 when not approaching
};

struct RadarStats {
  bool     talking;     // a good result frame within RADAR_SILENT_MS
  uint32_t ageMs;       // since the last good frame (0 if none yet)
  float    fps;         // good frames in the last second
  uint32_t frames, bad, bytes;
  int      fireRun;     // consecutive readings that passed the rule
  RadarReading r;
  uint16_t closest, farthest;  // the sensor's own detect range, cm, as read at start-up (0 0 if never read)
  String   version;     // the sensor's software version, as read at start-up ("" if never read)
  String   why;         // what the radar saw when the last sensor-fired drop started ("" if none yet)
  uint32_t whyAgoMs;    // how long ago that was (0 if none yet)
};

void radarBegin();      // call once from setup()
void radarPoll();       // call from loop(): reads whatever the UART holds; 1.5 s after boot asks the sensor to report 10 times a second, again every RADAR_RETRY_MS while silent
bool radarTalking();    // result frames arriving (task safe)
bool radarFire();       // the last two readings both passed the trigger rule (task safe)
bool radarClear();      // nobody in view, or everyone farther than RADAR_CLEAR_CM (task safe); false while silent
void radarMarkFire(bool viaLink);   // the machine task says a drop just started on the sensor: keep what it saw, for the page (task safe)
int  radarProbe();      // find which free pin carries the sensor's signal and listen there; -1 if none (blocks 0.4 s)
void radarRaw();        // print the last 96 bytes heard on RX2
void radarBaud();       // find which speed the sensor answers at and set it back to RADAR_BAUD (blocks up to 4 s)
void radarVersion();    // ask the sensor its software and hardware version
void radarRange(int closest, int farthest);   // read the sensor's detect range, or set it (cm); -1 -1 = read only
void radarOut(int mode);                      // set the OUT pin's rule: 1 motion, 2 presence, 3 either; 0 = read only
void radarReset();      // factory reset the sensor and restart it (blocks about 1 s)
void radarCmd(const String &a);               // one protocol command by hand: "r 82 01" (read) or "w 83 01" (write)
RadarStats radarStats();
String radarJson();
