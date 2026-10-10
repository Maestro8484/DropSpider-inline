# Handoff: trigger sensor, the DFRobot C4002 as `sensor 4002`

Work order: bring up the DFRobot C4002 radar (SEN0691, 24 GHz, ordered 2026-10-07) as the trigger, in its printed case on the radar fork, and bench it through S1 to S5. The C4002 is the only sensor; the C4001 on hand is not used (owner's call), its three wiring answers stay in doc 02 for reference. The file name is historical; bearing care is in doc 01. The LD2450 design is retired: `docs/retired/handoff_sensor_ld2450.md`.

**Ground truth:** the repo on disk wins over this file. Staleness check: `git log -1 --oneline` against `git log -1 --oneline -- docs/handoff_sensor_bearings.md`; a different hash means commits landed after this was written, read `CHANGELOG.md` for them.

## Before you start

- **Firmware is written, audited, and has never run on a sensor.** `src/radar.cpp` speaks the C4002's binary protocol; settings `sensor` (4002 or 2410), `approach`, `leadms`, `radarinv` (`CHANGELOG.md` 2026-10-07 and 2026-10-10). Which build the board runs now is not known; assume it needs the current one.
- **Case and wiring are done in the repo, not on the bench** (`CHANGELOG.md` 2026-10-10): `cad/c4002_case.py`, STLs `c4002_case_base.stl` and `c4002_case_lid.stl`; wiring in doc 02 "Sensor wiring", the wiring guide and build guide.
- **T1 to T8:** read `docs/commissioning_log.md` for a PASS row on each. Without them S1 and S2 can still run; S3 to S5 wait.
- **Gate for any flash or motion:** the owner says he is at the device and `status` shows busy 0, driverOn 0, ready. The session runs every command itself; the owner is never handed one.

## What the audit left for the bench (2026-10-10, `CHANGELOG.md` that day)

The radar code was audited against DFRobot's three decoders and the web radar card rebuilt with its controls on it (walking speed, lead time, direction swap, trigger source, the sensor's detect range with Set and Read). Three things only the sensor can settle:

- **The data byte count.** The firmware decodes the result frame as 18 bytes packed, the way DFRobot's Python port and ESPHome component read it. The first frame's count is logged; the page's radar card shows it under the timeline. 18 is right. Any other count: `radar raw` and compare the bytes with the layout at the top of `src/radar.cpp` before trusting a single reading.
- **The direction word.** DFRobot's code says 2 = approaching; its Home Assistant tutorial says 0. Walk toward the sensor in S2 and read the card: if it says going away, tick "Direction reads backwards" (`radarinv 1`), Save settings. No rebuild.
- **The sensor's current draw** for doc 02's power table.

## Read first

1. Doc 02 "Sensor wiring" and the pin table: the five wires.
2. `src/radar.cpp` and `include/radar.h`: `feed()` to `packetDone()` to `result()` to `judge()`, `fireRun`, `clearNow`, `setupSensor()`, the console helpers.
3. `src/machine.cpp` `readInputs()`: `S.sensor == 4002` uses the serial rule, and the OUT pin when serial is silent for `RADAR_SILENT_MS` (1 s).
4. `src/console.cpp` `printRadar()` and the `radar` commands (`raw`, `baud`, `probe`, `range`, `version`, `cmd`); `src/web.cpp` radar card.

## The work, in order

1. **Print and fit the case (owner).** `c4002_case_base` and `c4002_case_lid`, flat side down, no supports. Board antenna side (two gold squares) down over the floor opening, pin end at the two buttons, wires out the 15 mm opening; the lid's four posts hold the board, the snaps hold the lid. Knuckle between the fork's ears (`ld2450_fork_screw`), M3 bolt. First print may need filing; note what was filed in the commissioning log.
2. **Wire (owner).** Five dupont jumpers or a soldered 5-pin header: VIN to the 5 V rail, GND, sensor TX to GPIO16 (RX2), sensor RX to GPIO17 (TX2), OUT to GPIO33 (hot glue off D33). Power from the 12 V adapter through the buck, never USB alone.
3. **Build and flash (session, behind the gate).** `pio run`; then the owner's update road, `scripts\update_firmware.bat`, run by the session. `sensor 4002` is the factory default (`DEF_SENSOR`); if `status` shows otherwise, set it, `save`, restart.
4. **First power-up readings.** Meter the sensor's current and add it to doc 02's power table (DFRobot does not state it). Read the log: `[radar] C4002 answers: reporting every ... ms` and `[radar] result frames carry 18 data bytes`. Any count but 18 means the decode is wrong; `radar raw` shows the bytes. No answer: the firmware asks again every 5 s and says so once; `radar baud` scans for its speed, and check TX and RX are crossed.
5. **S1 to S5** below, one row per attempt in `docs/commissioning_log.md`.
6. **PLA check.** A person at 3 m, read with `radar raw` or the web card: bare board, then in the case. The floor opening leaves no PLA over the antenna, so the two should match; if the case reads clearly shorter, say so before S3.
7. **Two things only this bench can settle.** Whether the C4002 keeps its report period through a power cut (the firmware sends it at every boot anyway, and again every 5 s while silent). Which way its direction word reads on the tilted mount: if backwards, tick "Direction reads backwards" on the radar card (`radarinv 1`), Save settings, log it.
8. **Build guide section 10 radar card drawing** (team, any time): it is still the old LD2450 top view; only its label says C4002. Redraw from the C4002 card in the wiring section, run `python tools/make_build_guide.py`.
9. **Docs** after the bench: doc 02 current, doc 04 if any setting or command changed, doc 07 step 12, `CHANGELOG.md`. Commit by name.

The trigger rule, unchanged: armed and idle only, two readings in a row with the person approaching, speed at or above `approach` (default 30 cm/s), distance divided by speed at or below `leadms` (default 750 ms). Clear for re-arm: nobody, or everyone farther than `RADAR_CLEAR_CM` (300), for `CLEAR_BEFORE_REARM` (2 s). Serial silent for 1 s: fault logged, OUT on GPIO33 carries the trigger. `sensor 2410` is the OUT pin only.

## Inverted install: four things the firmware must handle

Numbers from `cad/inverted.py` and doc 06; none seen on real hardware yet.

1. **Placement.** The case hangs on the fork under the base at the servo end, about 154 mm out from the beam's face, looking back toward the beam and 50 degrees down (55 to 60 if the walk test asks). It sits about 2.28 m up and tilted, so its range is not the floor distance to the doorway: tune `leadms` and the clear distance on the porch, not the bench. The C4002 reports range and speed, not position; the LD2450's `doorwidth` and `xflip` do not apply.
2. **The spider is inside the radar's view.** Retracted, dropped and swinging, it can read as a person and hold the device in "waiting for the doorway to clear". In S2 read what the sensor reports with the spider at rest, dropped and swinging, then set the minimum detect range (`radar range`) past it, and check that does not hide a person in the doorway.
3. **Aluminum blocks the radar.** Siding or trim stops 24 GHz completely and can bounce phantom targets. Keep the two-readings rule; the owner's fix for late firing is a steeper tilt.
4. **Line between the spool and the flap** is about 72 mm inverted; `SPOOL_TO_EYELET_MM` is 40. Roadmap line 1, `docs/handoff_task1_firmware.md` step 1; not this handoff's work, but S3 depends on it.

## Tests (S1 to S5 in `docs/commissioning_log.md`, one row per attempt)

| # | Test | Pass |
|---|---|---|
| S1 | Power the sensor, meter its current, open the web radar card | `[radar] C4002 answers` and 18 data bytes in the log; the reading follows a walker |
| S2 | Live readout walking toward, away from, and across the doorway; spider at rest, dropped, swinging | direction word checked on the tilted mount; spider excluded by the detect range without hiding a person in the doorway |
| S3 | Walk in at normal pace, 10 times | fires every time; spider arrives as you reach the doorway |
| S4 | Walk away, walk past across the hallway, stand still in the window | no trigger |
| S5 | Unplug the sensor's TX wire while armed | fault logged within 1 s; the OUT pin takes over |

## Done when

`sensor 4002` in its case fires the drop on the bench (S3 passes), S4 and S5 pass, and the docs in step 9 say so.

## Finish

Changelog line, roadmap line 4 removed, close V15 in `docs/08_open_items.md` with the S1 to S5 log rows, move this file to `docs/retired/`.

## Rules for the session

- The owner is not a developer: verdict first, short, plain English, gloss jargon in a few words. No em dashes, arrows, emojis. A question gets a one-line answer and no work.
- No flash and no motion until he says he is at the device and the board shows busy 0, driverOn 0, ready. Never plug or unplug the motor with 12 V on. Servo plug back in before any drop.
- Never hand him a command to run.
- Stage files by name; never `git add -A`.
- The Pi4 is never touched from this repo.
