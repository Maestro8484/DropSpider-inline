// Runtime settings: start as the defaults in config.h, change live from the serial
// console or the web page, and survive a power cut once saved. Reflashing the
// firmware does not wipe them.
#pragma once
#include <Arduino.h>

struct Settings {
  int servoLock, servoRel, lineMm, rpm, rewindDir, settleMs, rearmMs, armed;
  int limitFitted, limitInverted;
};

// The live copy everything reads. Change it only through settingsSet().
extern Settings S;

void settingsBegin();                  // load from flash, or defaults
void settingsSave();                   // write the live values to flash
void settingsDefaults();               // factory values into the live copy (not saved)

// Set one value by its console name (setlock, setrel, line, rpm, dir, settle,
// rearm, limit, liminv). The value must be a whole number inside the allowed
// range, or nothing changes and false comes back with the reason in why.
bool settingsSet(const String &name, const String &value, String &why);
bool settingsIsName(const String &name);

// A comma separated JSON fragment of every setting, for the web page.
String settingsJson();

// Home network saved from the web page. Empty means use the one in secrets.ini.
String wifiSavedSsid();
String wifiSavedPass();
void   wifiSave(const String &ssid, const String &pass);

// Drop counter, kept through power cuts.
uint32_t dropCount();
void     dropCountBump();

// Parse a signed whole number strictly: "12", "-1600". Empty, "12x", "abc" fail.
bool parseLong(const String &s, long &out);
