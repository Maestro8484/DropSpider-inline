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
#define PIN_SENSOR      33   // <- C4002 OUT (HIGH = someone there): the trigger when the serial link is silent, or with sensor 2410 (any active-high sensor: LD2410C, PIR, step mat)
#define PIN_LIMIT       32   // <- limit switch (3-pin endstop) at the eyelet: pressed = spider home
#define PIN_RADAR_RX    16   // <- C4002 TX (RX2): its result frames, 10 a second
#define PIN_RADAR_TX    17   // -> C4002 RX (TX2): report period at boot, and the 'radar' console commands
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
// After the limit switch stops a wind, or a rewind stalls, the motor backs down
// 1/8 turn slowly and holds (owner 2026-10-06): the bead rests clear of the flap
// and the eyelet, and the line carries only the spider.
#define BACKOFF_STEPS       (STEPS_PER_TURN / 8)           // about 20 mm of line
#define BACKOFF_RPM         30
#define DRIVER_SETTLE_MS    200    // standstill after the driver is switched on, before the first step (stealthChop tuning needs 130 ms)
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
// A run of limit switch presses by hand, at rest: PRESS_REHOME presses = bring it home
// (owner 2026-10-13), PRESS_SLEEP presses = sleep (not armed) or wake (owner 2026-10-14:
// "sleep mode by pressing the limit switch 5 times within 4 seconds"). The run is
// judged PRESS_QUIET_MS after the last press, so pressing on past 3 never starts a rehome.
#define PRESS_WINDOW_MS     4000   // all presses of one run fall within this of the first
#define PRESS_QUIET_MS      1200   // then left alone this long before anything happens
#define PRESS_REHOME        3
#define PRESS_SLEEP         5
// Homing the way a CNC machine does it (GRBL: seek fast, then feed slowly onto the switch)
#define FEED_RPM            80     // the last part of every rewind after a drop, and the whole of a reset wind
#define FEED_ZONE_TURNS     2.25f  // a rewind after a drop slows to FEED_RPM this far before the end of its count
#define RETRY_DOWN_STEPS    (STEPS_PER_TURN / 2)       // a rewind that misses the switch lowers this much (about 78 mm)...
#define RETRY_UP_STEPS      (STEPS_PER_TURN * 5 / 2)   // ...then winds this far at FEED_RPM, once, before it calls a fault
#define RETRY_SETTLE_MS     1000   // swing settles between the two
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
#define RADAR_BAUD          115200   // C4002 as shipped (DFRobot library example); 'radar baud' finds it if it moved
#define RADAR_SILENT_MS     1000     // no good frame this long = radar silent: the OUT pin carries the trigger
#define RADAR_REPORT_TENTHS 1        // asked of the sensor at boot: a result every 0.1 s
#define RADAR_RUN_GAP_MS    500      // a gap this long between result frames breaks the "two readings in a row" count
#define RADAR_RETRY_MS      5000     // while no result frames arrive, the report-period command is sent again this often

// ---------- DEFAULTS (runtime tunable, saved in flash) ----------
#define DEF_SERVO_LOCK      90     // finger level, in the teeth, resting on the ledge
#define DEF_SERVO_REL       30     // finger swung toward the floor, clear of the teeth
#define DEF_LINE_MM         720    // barrel knot to stop bead, line straight not pulled. Measure yours.
#define DEF_RPM             240    // rewind speed
#define DEF_REWIND_DIR      1      // flip (0/1) if rewind turns the wrong way
#define DEF_SETTLE_MS       1500   // hang time at the bottom before rewind
#define DEF_REARM_MS        20000  // lockout after each scare
#define DEF_ARMED           1      // every power-up arms; armed is never saved (owner 2026-10-13)
#define DEF_LIMIT_FITTED    0      // turn on once the limit switch is wired and reads right
#define DEF_LIMIT_INVERTED  0      // flip if the switch reads backwards
#define DEF_DROP_MM         (DEF_LINE_MM - 40 - 60)  // how far the spider travels
#define DEF_DROP_RPM        500    // top speed of the drop. 1 m/s is about 610 rpm
#define DEF_DROP_ACC        120000 // microsteps/s^2 at the start of the drop. 100000 is about 1 g
#define DEF_DROP_DEC        60000  // microsteps/s^2 for the stop, about 0.6 g. Keep low: motor torque
#define DEF_RELEASE_MS      250    // finger travel time before the drop starts
#define DEF_SENSOR          4002   // 4002 = C4002 over serial, OUT pin if it goes silent; 2410 = OUT pin on GPIO33 only
#define DEF_APPROACH        30     // cm/s toward the sensor, slower than this does not fire
#define DEF_LEAD_MS         750    // fire when distance / speed is under this (ms before the person arrives)
#define DEF_FIRE_CM         120    // fire when someone approaching at 'approach' or faster is within this slant distance, cm; 0 = time rule only (owner 2026-10-10: proximity over timing)
#define DEF_CLEAR_CM        300    // the doorway is clear when nobody reads within this slant distance (was the fixed RADAR_CLEAR_CM; a setting since the office bench 2026-10-10, where a mirror at 2.2 m held it)
#define DEF_CLEAR_MS        30000  // waiting for the doorway to clear re-arms anyway after this long, ms; 0 = wait for clear (owner 2026-10-11)
#define DEF_RADAR_INV       0      // 1 = the sensor's direction word reads backwards on this mount (swap approaching and away); test S2 decides
