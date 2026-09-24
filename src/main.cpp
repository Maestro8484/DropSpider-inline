// DropSpider - Mechanism A (In-Line Single-Axle Clutch Spool) - Rev C firmware
// Board: 38-pin ESP32-S NodeMCU. Driver: TMC2209 in STEP/DIR/EN standalone mode on an A4988-style carrier.
// Cycle: sensor edge -> finger out (free-fall) -> settle -> rewind (stops at the limit switch) -> finger in
//        -> driver off -> lockout -> wait for the doorway to clear.
// Holding at the top costs zero power: the finger and ratchet hold, driver and servo are both off.
//
// Where to look:
//   include/config.h   every pin and fixed number
//   src/machine.cpp    the cycle, stepper, servo, sensor, button, limit switch
//   src/console.cpp    text commands (USB serial and the web page share them)
//   src/web.cpp        WiFi, the web page, network firmware updates
//   src/settings.cpp   tunables saved in flash

#include <Arduino.h>
#include "config.h"
#include "settings.h"
#include "machine.h"
#include "console.h"
#include "web.h"

void setup() {
  pinMode(PIN_EN, OUTPUT); digitalWrite(PIN_EN, HIGH);   // coils off first thing
  Serial.begin(CONSOLE_BAUD);
  settingsBegin();
  machineBegin();            // own task from here on; never rewinds at boot
  logf("\nDropSpider Mechanism A Rev C ready. Type help.");
  webBegin();                // may take up to 15 s to join WiFi; the machine is already live
  logf("%s", webWhereAmI().c_str());
  consoleRun("status");
}

void loop() {
  consolePollSerial();
  webLoop();
  delay(2);
}
