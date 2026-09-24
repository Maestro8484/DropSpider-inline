// DropSpider - Mechanism A (In-Line Single-Axle Clutch Spool) - Rev C
// Hardware constants. Tunables below "DEFAULTS" can be changed at runtime over serial and saved to flash.
#pragma once

// ---------- pins, ESP32 DevKit V1 30-pin ----------
#define PIN_STEP        25   // -> carrier STEP
#define PIN_DIR         26   // -> carrier DIR
#define PIN_EN          27   // -> carrier EN   (LOW = driver on, HIGH = coils off)
#define PIN_SERVO       13   // -> SG90 orange. Not GPIO14: 14 pulses at boot and would twitch the finger.
#define PIN_SENSOR      33   // <- LD2410C OUT (HIGH = presence). Or AM312 PIR OUT.
#define PIN_RADAR_RX    16   // <- LD2410C TX (reserved, not used by this firmware)
#define PIN_RADAR_TX    17   // -> LD2410C RX (reserved, not used by this firmware)
#define PIN_BUTTON      0    // on-board BOOT button: manual test drop (active LOW)
#define PIN_LED         2    // on-board blue LED

// ---------- mechanics (fixed by the printed parts) ----------
#define MOTOR_FULL_STEPS    200
#define MICROSTEPS          8      // carrier DIP switches all OFF on a TMC2209 = 1/8
#define BARREL_DIA_MM       50.0f
#define SPOOL_TO_EYELET_MM  40.0f  // braid that stays between spool and eyelet when fully up
#define OVERSHOOT_TURNS     0.75f  // extra rewind so the swivel always seats on the eyelet
#define RAMP_STEPS          600    // acceleration ramp length
#define RAMP_START_FRAC     0.20f  // start speed as a fraction of full speed

// ---------- timing ----------
#define SERVO_MOVE_MS       350    // time for the finger to travel
#define LOCK_SEAT_MS        700    // servo keeps pushing while the spool settles onto a tooth
#define TRIGGER_DEBOUNCE_MS 60     // sensor must stay HIGH this long
#define CLEAR_BEFORE_REARM  2000   // sensor must read LOW this long before the next scare

// ---------- DEFAULTS (runtime tunable, saved in NVS) ----------
#define DEF_SERVO_LOCK      90     // finger level, in the teeth, resting on the ledge
#define DEF_SERVO_REL       30     // finger swung toward the floor, clear of the teeth
#define DEF_LINE_MM         720    // barrel knot to stop bead, elastic included. Measure yours.
#define DEF_RPM             240    // rewind speed
#define DEF_REWIND_DIR      1      // flip (0/1) if rewind turns the wrong way
#define DEF_SETTLE_MS       1500   // hang time at the bottom before rewind
#define DEF_REARM_MS        20000  // lockout after each scare
#define DEF_ARMED           1
