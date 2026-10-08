# Handoff (retired): LD2450 radar as the trigger

Retired 2026-10-08, superseded by `docs/handoff_sensor_bearings.md` (the DFRobot C4001 on hand, then the C4002). Kept for the record: the 2026-09-24 LD2450 design and why it was parked. Nothing here is current.

**Parked 2026-10-07 by the owner.** Three LD2450 modules in a row behaved the same on this rig: 5 V at the pins, Bluetooth advertising, both wires carrying bytes each way, every protocol command acknowledged (`radar wake`, `radar reset`, `radar baud`, `radar cmd`), factory reset and restart acknowledged, firmware 2.04.23101915 and then 2.14.25112412, and never one position frame, on the wire or in Hi-Link's app. On 2026-10-07 the owner metered 5 V on the sensor, swapped TX and RX, then swapped them back (TX to GPIO16, RX to GPIO17). The module's current was not measured; that is the one check left if anyone picks this up again. The LD2450 parser was removed from the firmware on 2026-10-07 (`CHANGELOG.md`). Log rows: `docs/commissioning_log.md`, 2026-10-07.

## Decision (2026-09-24)

The owner already has an LD2450. It becomes the primary trigger. The LD2410C is the fallback on GPIO33 (`sensor 2410`), fitted only if a named test fails; it is not fitted today. No purchases.

## Why

The prop only works if the spider lands as the person reaches the doorway. The LD2410C fires on anyone moving inside its range, in any direction, at a fixed distance. The LD2450 reports each person's X and Y position and speed, so the firmware can fire only on people walking toward the door and time the drop to their predicted arrival.

Owner concern raised: "mmWave can be finicky without a clear visual picture." Answer: the LD2450's app shows each person as a moving dot on a map, which gives that picture. Reported user experience, researched 2026-09-24:
- A Home Assistant user powered an LD2450 from 5 V only, connected over Bluetooth, and saw himself moving and standing in the app right away, before wiring it to anything (community.home-assistant.io).
- Complaints that HLKRadarTool is complicated and unintuitive, raised by a sensor maker to Hi-Link, are about the LD2410C's per-gate number entry (screek.io).
- LD2450 zones in the app are drag-and-drop boxes (Apollo Automation docs). We do not use them; see below.
- The module has no external antenna; phone Bluetooth works only within a few feet (Apollo docs).
- ESPHome requires LD2450 firmware V2.02.23090617 or later; the app can update it (esphome.io).
- Weak at people standing still beyond about 2 m; it is a tracker (atomic14.com). Irrelevant: we only want walkers.

**No calibration is required.** The LD2450 streams target data over UART from power-up. The app is optional: live view and firmware update.

## Hardware facts

- 4 pins: 5 V, GND, TX, RX. No OUT pin. Connector is 4-pin, 1.25 mm pitch.
- UART 256000 baud, 8N1, hardware UART only. About 10 frames per second, up to 3 targets, X/Y/speed in mm and cm/s per the Hi-Link protocol.
- Field of view about plus or minus 60 degrees horizontal, 35 vertical, range about 6 m.
- Wiring: LD2450 TX to GPIO16 (UART2 RX), RX to GPIO17 (UART2 TX). On the 30-pin ESP32 DevKit V1 in use they are the pins printed RX2 and TX2.

## Firmware spec (as written 2026-09-24)

1. Before writing a parser, find an existing Arduino or ESP-IDF LD2450 library. Name it, check it builds on espressif32@6.7.0, and say whether you use it and why. Known reference implementations: ESPHome's native `ld2450` component, and the GitHub project PeterkoCZ91/HLK-LD2450-security (has a tested parser with unit tests). Check licenses before copying.
2. New setting `sensor` = `2450` (default) or `2410`.
3. Trigger rule, all must hold for 2 consecutive frames, only while armed and idle:
   - |X| < `doorwidth` / 2 (default `doorwidth` 1000 mm)
   - approaching faster than `approach` (default 0.3 m/s). Confirm the speed sign convention on the bench and put it in a constant.
   - Y / speed < `leadms` (default 750 ms)
4. Clear (for re-arm): no target inside the door-width window with Y under 3 m, for 2 s.
5. Settings in NVS, console, web page, with range checks: `sensor`, `doorwidth` (400 to 2000 mm), `approach` (0.1 to 1.5 m/s), `leadms` (200 to 2000 ms).
6. Web page: live readout of up to 3 targets (X, Y, speed), and a "would trigger now" indicator, for bench tuning.
7. Radar data loss: if no valid frame for 1 s, log a fault and fall back to the LD2410C if `sensor` allows, else stay disarmed.
8. Do not send zone or region commands to the sensor. Leave its built-in area filter off so the firmware sees every target.

## Tests (S1 to S5 as first written)

| # | Test | Pass |
|---|---|---|
| S1 | App check: firmware version, walk toward the door | version at or above V2.02.23090617; dot tracks through the frame |
| S2 | Live readout while walking toward, away from, and across the door | sign of speed matches direction; X near 0 at the door center |
| S3 | Walk in at normal pace, 10 times | fires every time; spider arrives as you reach the doorway |
| S4 | Walk away, walk past across the hallway, stand still in the window | no trigger |
| S5 | Unplug the radar's TX wire while armed | fault logged within 1 s; fallback per setting |

The inverted-install notes that were in this file (radar placement and axes, the spider inside the view, aluminum blocking the signal, the longer spool-to-flap line) still apply to the current sensor and moved with the task to `docs/handoff_sensor_bearings.md`.
