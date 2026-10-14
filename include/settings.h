// Runtime settings: start as the defaults in config.h, change live from the serial
// console or the web page, and survive a power cut once saved. Reflashing the
// firmware does not wipe them.
#pragma once
#include <Arduino.h>

struct Settings {
  int servoLock, servoRel, lineMm, rpm, rewindDir, settleMs, rearmMs, armed;
  int limitFitted, limitInverted;
  int dropMm, dropRpm, dropAcc, dropDec, releaseMs;
  int sensor, approach, leadMs, fireCm, clearCm, clearMs, radarInv;
};

// The live copy everything reads. Change it only through settingsSet().
extern Settings S;

void settingsBegin();                  // load from flash, or defaults
void settingsSave();                   // write the live values to flash
void settingsDefaults();               // factory values into the live copy (not saved)

// Set one value by its console name (setlock, setrel, line, rpm, dir, settle,
// rearm, limit, liminv, dropmm, droprpm, dropacc, dropdec, relms, sensor, approach,
// leadms, radarinv). The value must
// be a whole number inside the allowed range, or nothing changes and false comes
// back with the reason in why.
bool settingsSet(const String &name, const String &value, String &why);
bool settingsIsName(const String &name);

// The log lines around the last fault, kept in flash so a power cut does not lose them.
void faultLogSave(const String &text);
String faultLogLoad();

// A comma separated JSON fragment of every setting, for the web page.
String settingsJson();
// The same for the factory values, so the page can mark what differs from stock.
String settingsStockJson();
// A JSON array body of the names whose live value differs from what is saved in flash
// (owner 2026-10-14: the page marks them and shows one Save bar while any exist).
String settingsUnsavedJson();

// Home network saved from the web page. Empty means use the one in secrets.ini.
String wifiSavedSsid();
String wifiSavedPass();
void   wifiSave(const String &ssid, const String &pass);

// Fixed network address saved from the page or the console (owner 2026-10-14, after the
// router moved the board from .138 to .135 overnight). Empty means the router picks.
String ipSaved();
void   ipSave(const String &ip);

// Longest drop the line allows: stops DROP_KNOT_MARGIN_MM short of the barrel knot.
int dropMmMax();

// V14: the spider was left seated on the finger after a rewind stopped by the
// limit switch. The switch reads open there by design, so this is how boot knows
// the spider is home. Kept through power cuts.
bool homeSaved();
void homeSave(bool home);

// Drop counter, kept through power cuts.
uint32_t dropCount();
void     dropCountBump();

// Power-up counter, bumped once at every boot. The page uses it to say whether a
// kept cycle record is from this power-up or an earlier one.
uint32_t bootCount();

// The last cycles (one record each, see machine.h), kept through power cuts.
size_t cyclesLoad(void *buf, size_t max);
void   cyclesSave(const void *buf, size_t n);

// Parse a signed whole number strictly: "12", "-1600". Empty, "12x", "abc" fail.
bool parseLong(const String &s, long &out);
