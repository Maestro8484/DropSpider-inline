# Handoff: task 2, LD2450 radar as the trigger

From the mechanical owner to the software/electrical team, written 2026-09-24. Future work only; what is already done is in `CHANGELOG.md`.

**Before you start:** T1 to T8 in `M1_fix_handoff.md` must pass. Check: `docs/commissioning_log.md` has a PASS row for each.

## 1. Sensor: switch the trigger to the HLK-LD2450

### Decision

The owner already has an LD2450. It becomes the primary trigger. The LD2410C is the fallback on GPIO33 (`sensor 2410`), fitted only if a named test fails; it is not fitted today. No purchases.

### Why

The prop only works if the spider lands as the person reaches the doorway. The LD2410C fires on anyone moving inside its range, in any direction, at a fixed distance. The LD2450 reports each person's X and Y position and speed, so the firmware can fire only on people walking toward the door and time the drop to their predicted arrival.

Owner concern raised: "mmWave can be finicky without a clear visual picture." Answer: the LD2450's app shows each person as a moving dot on a map, which gives that picture. Reported user experience, researched 2026-09-24:
- A Home Assistant user powered an LD2450 from 5 V only, connected over Bluetooth, and saw himself moving and standing in the app right away, before wiring it to anything (community.home-assistant.io).
- Complaints that HLKRadarTool is complicated and unintuitive, raised by a sensor maker to Hi-Link, are about the LD2410C's per-gate number entry (screek.io).
- LD2450 zones in the app are drag-and-drop boxes (Apollo Automation docs). We do not use them; see below.
- The module has no external antenna; phone Bluetooth works only within a few feet (Apollo docs).
- ESPHome requires LD2450 firmware V2.02.23090617 or later; the app can update it (esphome.io).
- Weak at people standing still beyond about 2 m; it is a tracker (atomic14.com). Irrelevant: we only want walkers.

**No calibration is required.** The LD2450 streams target data over UART from power-up. The app is optional: live view and firmware update.

### Hardware facts

- 4 pins: 5 V, GND, TX, RX. No OUT pin. Connector is 4-pin, 1.25 mm pitch; check the owner has the cable.
- UART 256000 baud, 8N1, hardware UART only. About 10 frames per second, up to 3 targets, X/Y/speed in mm and cm/s per the Hi-Link protocol (confirm units against the library you pick).
- Field of view about plus or minus 60 degrees horizontal, 35 vertical, range about 6 m.
- Wiring: LD2450 TX to GPIO16 (UART2 RX), RX to GPIO17 (UART2 TX). On the 30-pin ESP32 DevKit V1 in use they are the pins printed RX2 and TX2.

### Firmware spec

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

### Tests (log as S1 to S5 in `commissioning_log.md`)

| # | Test | Pass |
|---|---|---|
| S1 | App check: firmware version, walk toward the door | version at or above V2.02.23090617; dot tracks through the frame |
| S2 | Live readout while walking toward, away from, and across the door | sign of speed matches direction; X near 0 at the door center |
| S3 | Walk in at normal pace, 10 times | fires every time; spider arrives as you reach the doorway |
| S4 | Walk away, walk past across the hallway, stand still in the window | no trigger |
| S5 | Unplug the radar's TX wire while armed | fault logged within 1 s; fallback per setting |

### Inverted install: four things the firmware must handle (added 2026-09-28)

The owner is building the inverted install (doc 06, V18): the device turned over on two steel corner braces on the porch beam's inside face. The mechanism, the winding sense, `dir` and the switch logic do not change. These four things do. Numbers from `cad/inverted.py` and doc 06; none of them has been seen on real hardware yet.

1. **Radar placement and axes.** The LD2450 hangs in its cradle under the base at the servo end, about 154 mm out from the beam's face, looking back toward the beam and 50 degrees down (55 to 60 if the walk test asks; the cradle clears to 65). People approach from outside, under the beam, toward the radar. Its X axis runs along the rod, which is parallel to the beam, so X is across the walkway, and the line falls at about X = 0. Which way is +X depends on which end of the device the owner puts where. Do not hard-code the sign: add a setting (for example `xflip`, 0 or 1) or confirm it in S2 and store it. The radar sits about 2.28 m up and tilted, so Y is not the floor distance to the doorway; tune `leadms` and the clear distance on the porch, not on the bench.
2. **The spider is inside the radar's view.** Retracted it hangs a few cm below the base and about 37 mm toward the beam from the radar, near X = 0 at short range; dropped, it hangs near the lower edge of the view. It moves during the drop and the rewind and swings after. As written, rule 4 (clear = no target in the window under 3 m for 2 s) could see the spider as a person and hold the device in "waiting for the doorway to clear" after every scare. Design for it: in S2, read the spider's X, Y and speed on the live readout at rest, dropped and swinging, then exclude it (for example a `minrange` setting below which targets are ignored, or ignore targets in a small box around the line during the cycle and for a few seconds after). Check the exclusion does not also hide a person standing in the doorway.
3. **Aluminum blocks the radar.** At 24 GHz, aluminum siding or trim stops the signal completely, however thin. If the beam is clad, the radar sees people only once they are under the beam's bottom edge, and the flat metal can bounce back phantom targets or jumpy positions. Keep the 2-consecutive-frame rule; do not loosen it to cure late firing. The owner's fix is a steeper tilt.
4. **Line between the spool and the flap is longer.** `include/config.h` has `SPOOL_TO_EYELET_MM 40.0f` (its comment still says braid; the line is 6 lb mono). Doc 06 gives 45 mm for the ceiling install and about 72 mm for the inverted one with fairlead v2 (doc 09, 2026-09-28). With 40 the drop-distance limit (`dropMmMax()` = line - 40 - 30) lets the spider stop 15 mm closer to the barrel knot than the 30 mm margin intends, and the rewind estimate in `machine.cpp` is 15 mm short (the 0.75-turn overshoot and the limit switch cover that). Also: the factory `dropmm` 620 only fits the old 720 line; the inverted line is about 636, so the page refuses the new line until `dropmm` is lowered (the build guide tells the owner to do that first). Fix: make it 72 (fairlead v2, 2026-09-28, doc 09), or a setting, and check the factory `dropmm` fits the inverted line. This one bites task 1's bench tests too, not only the radar work.

### Docs yours after the firmware lands

`02_electrical.md` pin map and wiring picture, `04_firmware.md`, `07_commissioning.md` step 12, web help text, and the build guide's radar rows (sections 09, 10 and 12, now marked AFTER TASK 2).

### Finish

Changelog line, remove this task's roadmap line, close V15 in `08_open_items.md` with the S1 to S5 log rows, move this file to `docs/retired/`. Bearing care, formerly section 2 here, is reference and lives in `01_mechanical_design.md`, "Bearing care".
