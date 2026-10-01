// DropSpider - Mechanism A (In-Line Single-Axle Clutch Spool) - Rev C
// Every pin and every fixed number, in one file. The values under DEFAULTS can be
// changed at runtime from the serial console or the web page and saved to flash.
#pragma once

// ---------- board ----------
// In use: 30-pin ESP32 DevKit V1 (ESP-WROOM-32, CP2102 USB). The 38-pin NodeMCU-32S
// also works unchanged. PlatformIO board: nodemcu-32s (same chip, same pins).
// Every pin below is on both the 30-pin and the 38-pin board, and none of them
// is a pin the chip uses for itself at boot except GPIO0 (the BOOT button) and
// GPIO2 (the LED), which are used for exactly those things.

// ---------- pins ----------
// D27, D26, D25 sit side by side on the header in the same order as the expansion board's DIR, STEP, EN
// columns, so a 3-wire ribbon goes across straight (owner 2026-10-01; was STEP 25, DIR 26, EN 27).
#define PIN_STEP        26   // -> expansion board STEP, S row
#define PIN_DIR         27   // -> expansion board DIR, S row
#define PIN_EN          25   // -> expansion board EN, S row   (LOW = driver on, HIGH = coils off)
#define PIN_SERVO       13   // -> SG90 orange. Not GPIO14: 14 pulses at boot and would twitch the finger.
#define PIN_SENSOR      33   // <- LD2410C OUT (HIGH = presence). Or AM312 PIR OUT.
#define PIN_LIMIT       32   // <- limit switch (3-pin endstop) at the eyelet: pressed = spider home
#define PIN_RADAR_RX    16   // <- LD2410C TX (reserved, not used by this firmware)
#define PIN_RADAR_TX    17   // -> LD2410C RX (reserved, not used by this firmware)
#define PIN_BUTTON      0    // on-board BOOT button: manual test drop (active LOW)
#define PIN_LED         2    // on-board blue LED

// ---------- mechanics (fixed by the printed parts) ----------
#define MOTOR_FULL_STEPS    200
#define MICROSTEPS          8      // expansion board DIP switches all OFF on a TMC2209 = 1/8
#define STEPS_PER_TURN      (MOTOR_FULL_STEPS * MICROSTEPS)
#define BARREL_DIA_MM       50.0f
#define SPOOL_TO_EYELET_MM  40.0f  // braid that stays between spool and eyelet when fully up
#define OVERSHOOT_TURNS     0.75f  // extra rewind so the bead always reaches the eyelet
#define RAMP_STEPS          600    // steps to reach full rewind speed from standstill

// ---------- Rev C.1 motor-led drop ----------
// + = rewind (clockwise seen from behind the motor), - = unwind (counterclockwise), as everywhere in the firmware.
#define UNLOAD_STEPS        (STEPS_PER_TURN / 12)          // wind up 1/12 turn while the finger swings out (M2)
#define UNLOAD_RPM          120
#define SEAT_STEPS          (STEPS_PER_TURN * 12 / 120)    // 1/12 turn x 1.2: lets the spool down onto a tooth
#define SEAT_RPM            30
#define DROP_KNOT_MARGIN_MM 30     // a drop never comes closer than this to the barrel knot
// The drop's gentler stop is switched in this far ahead of the exact point, so a
// late look by the machine task can never make the motor overshoot and reverse.
#define DECEL_MARGIN_S      0.010f
#define DECEL_MARGIN_STEPS  50
// Rewind ran this much more than the drop: the spool got ahead of the motor
// (lost steps on the stop) and the line's stretch caught the spider.
#define LOST_STEPS_WARN_MM  20

// ---------- timing ----------
#define SERVO_MOVE_MS       350    // time for the finger to travel
#define LOCK_SEAT_MS        700    // servo keeps pushing while the spool settles onto a tooth
#define TRIGGER_DEBOUNCE_MS 60     // sensor must stay HIGH this long
#define CLEAR_BEFORE_REARM  2000   // sensor must read LOW this long before the next scare
#define BUTTON_DEBOUNCE_MS  40
#define LIMIT_DEBOUNCE_MS   4      // short on purpose: this reading stops the motor
#define MACHINE_TICK_MS     2      // how often the machine task looks at everything
#define FAULT_STRIKES       3      // this many faults in a row and it stops arming itself

// ---------- limit switch sanity ----------
// If the switch trips before this fraction of the expected rewind, the line snagged
// or broke rather than the spider arriving.
#define REWIND_MIN_FRAC     0.25f

// ---------- network ----------
#define HOSTNAME            "dropspider"         // page at http://dropspider.local
#define AP_SSID             "DropSpider-setup"   // own network if the home one fails
#define AP_PASSWORD         "dropspider"         // 8 characters minimum
#define WIFI_JOIN_TIMEOUT_MS 15000
#define OTA_USER            "admin"              // web page update login; password is OTA_PASS

// Network credentials come from secrets.ini through platformio.ini. These
// fallbacks only exist so the file still compiles without them.
#ifndef WIFI_SSID
#define WIFI_SSID ""
#endif
#ifndef WIFI_PASS
#define WIFI_PASS ""
#endif
#ifndef OTA_PASS
#define OTA_PASS "dropspider"
#endif

#define CONSOLE_BAUD        115200

// ---------- DEFAULTS (runtime tunable, saved in flash) ----------
#define DEF_SERVO_LOCK      90     // finger level, in the teeth, resting on the ledge
#define DEF_SERVO_REL       30     // finger swung toward the floor, clear of the teeth
#define DEF_LINE_MM         720    // barrel knot to stop bead, line straight not pulled. Measure yours.
#define DEF_RPM             240    // rewind speed
#define DEF_REWIND_DIR      1      // flip (0/1) if rewind turns the wrong way
#define DEF_SETTLE_MS       1500   // hang time at the bottom before rewind
#define DEF_REARM_MS        20000  // lockout after each scare
#define DEF_ARMED           1
#define DEF_LIMIT_FITTED    0      // turn on once the limit switch is wired and reads right
#define DEF_LIMIT_INVERTED  0      // flip if the switch reads backwards
#define DEF_DROP_MM         (DEF_LINE_MM - 40 - 60)  // how far the spider travels
#define DEF_DROP_RPM        500    // top speed of the drop. 1 m/s is about 610 rpm
#define DEF_DROP_ACC        120000 // microsteps/s^2 at the start of the drop. 100000 is about 1 g
#define DEF_DROP_DEC        60000  // microsteps/s^2 for the stop, about 0.6 g. Keep low: motor torque
#define DEF_RELEASE_MS      250    // finger travel time before the drop starts
