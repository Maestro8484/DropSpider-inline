# Handoff: sensor change and bearing guidance (Rev C.1 addendum)

Date: 2026-09-24. From: mechanical owner. To: software/electrical team.
Do this **after** `M1_fix_handoff.md` tests T1 to T8 pass.

## 1. Sensor: switch the trigger to the HLK-LD2450

### Decision

The owner already has an LD2450. It becomes the primary trigger. The LD2410C stays wired on GPIO33 as a selectable fallback. No purchases.

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
- Wiring: LD2450 TX to GPIO16 (UART2 RX), RX to GPIO17 (UART2 TX). Both pins exist on the 38-pin NodeMCU-32S in use.

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

## 2. Bearings: care and what each one is for

| Bearing | Job | Care |
|---|---|---|
| HF0612 one-way needle bearing, pressed into `spool_body` | The clutch between rod and spool. Rev C.1 orientation: rod held, spool **locks clockwise** seen from the 606ZZ end. Lets the spool lag behind the motor on the drop, lets the motor wind it up on rewind | **Do not clean with carb cleaner or any solvent spray.** It strips the factory grease and attacks the plastic roller cage; dry needles can skid instead of locking. If gritty or sticky: flush with isopropyl alcohol only, dry, one drop of light machine oil. Never grease it |
| 606ZZ, pressed into the bracket end plate | Supports the rod's far end | Shielded and greased for life. Leave it alone; load is tiny. Carb cleaner would wash grease out with no way to repack |

If the drop feels sluggish, check in this order: spool end play (should slide 0.3 to 0.5 mm between spacers; sand a spacer if tight), line dragging in the eyelet, then the HF0612 by hand. Solvents are never the first fix.

## 3. Other decisions from the owner session, 2026-09-24

- **Existing hardware only** for Rev C.1: no new parts. Relay coil-disconnect and a dog clutch were rejected on this rule.
- **Spider:** foam, 60 g or less, so the motor can stop it cleanly (BOM N11 updated).
- **Model for this work:** Opus 5.5 at medium effort; high effort only for hard debugging.

## 4. Docs changed by the owner for this addendum

`03_sensor.md` (rewritten), `01_mechanical_design.md` (bearing care section), `08_open_items.md` (V15), `bom/BOM.csv` (LD2450, spider weight), `CLAUDE.md` (task order). **Yours after the firmware lands:** `02_electrical.md` pin map and wiring picture, `04_firmware.md`, `07_commissioning.md` step 12, web help text.
