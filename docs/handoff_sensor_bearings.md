# Handoff: trigger sensor, the DFRobot C4001 on hand as `sensor 4001`, then the C4002 when it arrives

Work order for the software team: make the DFRobot C4001 radar (SEN0609 25 m or SEN0610 12 m, the owner has one) the trigger, bench it, and add the C4002 (SEN0691, ordered 2026-10-07) when it lands. The file name is historical; bearing care is in doc 01. The LD2450 design this file once held is retired: `docs/retired/handoff_sensor_ld2450.md`.

**Ground truth:** the repo on disk wins over this file. Staleness check: `git log -1 --oneline` against `git log -1 --oneline -- docs/handoff_sensor_bearings.md`; a different hash means commits landed after this was written, read `CHANGELOG.md` for them.

## Before you start

- T1 to T8 pass: read `docs/commissioning_log.md` for a PASS row on each. If they are not there, the sensor can still be built and bench-read (S1, S2), but S3 to S5 wait.
- The C4002 firmware is in the tree and has never run on a sensor: `src/radar.cpp` speaks the C4002's binary protocol, settings `sensor` 4002 or 2410, `approach`, `leadms` (`CHANGELOG.md` 2026-10-07). It is the pattern to copy for the C4001, not a thing to rewrite.
- The sensor must be wired and the board locked and idle before any flash: `status` shows busy 0, driverOn 0, ready. Nothing moves until the owner says he is at the device.

## Read first

1. `src/radar.cpp` and `include/radar.h`: the parser `feed()` to `packetDone()` to `result()` to `judge()`, the rule, `fireRun`, `clearNow`, `setupSensor()`, and the console helpers.
2. `src/machine.cpp` `readInputs()`: where `S.sensor == 4002` chooses the serial rule over the OUT pin.
3. `src/settings.cpp`: the `sensor` row and the refusal of values other than 2410 and 4002.
4. `src/console.cpp` `printRadar()` and the `radar` dispatch; `src/web.cpp` radar card, `/api/radar`.
5. DFRobot's `DFRobot_C4001` library, MIT, github.com/DFRobot/DFRobot_C4001 v1.0.0. A clone may still be at `C:/Users/SuperMaster/AppData/Local/Temp/claude/c4001lib/DFRobot_C4001/`; re-clone if gone. Read `examples/mRangeVelocity/mRangeVelocity.ino`, `setSensorMode()` near line 119 of `src/DFRobot_C4001.cpp`, and `anaysisData()` near line 669.

## What the C4001 does (read 2026-10-08 from that library, nothing of it yet seen on a sensor)

- Serial 9600 8N1, fixed ("Baud rate cannot be changed", the example). I2C is also possible (0x2A); not used, the fork's wiring is serial.
- Two modes. Presence mode reports `$DFHPD,0*` or `$DFHPD,1*`. Speed-and-range mode, the one we want, reports one target per line: `$DFDMD,par1,par2,par3,par4,par5,par6,par7*`, where par1 = number of targets (0 or 1), par3 = range in meters as a decimal, par4 = speed in m/s as a signed decimal, par5 = energy. The library multiplies par3 and par4 by 100 to get cm and cm/s. Which sign of speed means approaching is stated nowhere read; S2 settles it.
- Commands are plain words ending in a newline, sent while the sensor is stopped: `sensorStop`, then the command, then `saveConfig`, then `sensorStart`. Speed mode is `setRunApp 1` (presence is `setRunApp 0`). Detect range is `setRange <min m> <max m>` (30 to 2000 cm; the example sets 11 to 1200), read back with `getRange`. Threshold `setThrFactor <n>`. OUT pin polarity `setGpioMode 1 <0 or 1>`, read with `getGpioMode 1`. Factory reset `resetCfg`, restart `resetSystem`. The library waits 50 to 800 ms between these; the firmware must not block the machine task while it does.
- Pins: VCC 5 V, GND, TX, RX, OUT. Wiring is the C4002's: VCC to the 5 V rail, GND, sensor TX to GPIO16 (RX2), sensor RX to GPIO17 (TX2), OUT to GPIO33 (HIGH = presence, the no-firmware fallback). Meter its current at first power-up; the library and wiki do not state it.

## The work, in order

1. **Setting.** `sensor` accepts 4001; `src/settings.cpp` row range 2410 to 4002 and the refusal message name all three values. `DEF_SENSOR` in `include/config.h` becomes 4001 (the sensor on hand). Doc 04's settings row follows.
2. **Baud per sensor.** `RADAR_BAUD` becomes two values, `RADAR_BAUD_4001 9600` and `RADAR_BAUD_4002 115200`, chosen from `S.sensor` in `radarBegin()`; changing `sensor` says "takes effect after restart", as `dir` does.
3. **Second parser in `src/radar.cpp`.** A text-line reader selected by `S.sensor == 4001`: collect bytes to `*` or newline, 80 characters max, resync on `$`. Parse `$DFDMD` into the same `RadarReading`: state 2 when par1 is 1, else 0 (the C4001 has no still-person reading; leave `pdist` 0); `mdist` = par3 times 100; `speed` = par4 times 100, signed; `dir` from the sign of speed through one constant `C4001_APPROACH_SIGN` (+1 or -1, set by S2), 1 (none) when speed is 0; `menergy` from par5 clipped to 99. `$DFHPD` lines mean the sensor is in presence mode: log once and send the speed-mode command. Then the same `judge()`, the same `fireRun`, `clearNow`, `goodAt`, so `radarFire()`, `radarClear()`, `radarTalking()`, `radarJson()` and the machine task do not change.
4. **Start-up command for the C4001** in `setupSensor()`: `sensorStop`, `setRunApp 1`, `saveConfig`, `sensorStart`, with the library's waits done as non-blocking steps from `radarPoll()`, 1.5 s after boot, as the C4002 path does. Skip the speed-mode command when `$DFDMD` lines are already arriving.
5. **Console `radar` commands per protocol.** `radar range` reads `getRange` and sets `setRange`; `radar version`, `radar baud`, `radar out` and `radar cmd` with hex bytes say "does not apply to the C4001" (its baud is fixed; `radar cmd` may instead send one plain-word command and print the reply, which is how the OUT polarity and threshold get set by hand). `radar reset` sends `resetCfg` then `resetSystem`. `radar raw` and `radar probe` work unchanged. `status` shows `sensor=4001(radar)`.
6. **Machine task.** `src/machine.cpp` `readInputs()`: `link` is true for 4001 or 4002 when `radarTalking()`. The fault and recovery log lines name the sensor.
7. **Web page.** The radar card's readings table shows a dash for the still person when the sensor is a 4001; the help text names both sensors. `/api/radar` unchanged.
8. **Docs.** Doc 02 pin rows and sensor wiring (the C4001 takes the C4002's wires; add its current once metered), doc 04 settings and `radar` command rows, doc 07 step 12, `CHANGELOG.md`, roadmap line 4. `cad/c4002_plate.svg` is the C4002's plate (22 x 26 mm board); whether the C4001 fits it is the owner's measurement of his board against the plate, its size was not read from any source.
9. **Build** with `pio run`. Commit by name. No flash until the sensor is wired and the board is locked and idle.
10. **When the C4002 arrives:** wire it in place of the C4001, `sensor 4002`, `save`, restart, meter its current, flash nothing new, read the first log lines: `[radar] result frames carry N data bytes` must say 20; anything else means the decode is wrong and `radar raw` shows the bytes. Then S1 to S5 again on it. Two things only that bench can settle: whether the C4002 keeps the report period through a power cut (the firmware sends it at every boot anyway) and which way its direction word reads on the tilted mount (if backwards, one comparison in `judge()`).

The trigger rule, both sensors, unchanged from the C4002 build: armed and idle only, two readings in a row with the person approaching, speed at or above `approach` (default 30 cm/s), distance divided by speed at or below `leadms` (default 750 ms). Clear for re-arm: nobody, or everyone farther than `RADAR_CLEAR_CM` (300), for `CLEAR_BEFORE_REARM` (2 s). Serial silent for `RADAR_SILENT_MS` (1 s): fault logged, the OUT pin on GPIO33 carries the trigger; `sensor 2410` is the OUT pin only.

## Inverted install: four things the firmware must handle (from the 2026-09-28 LD2450 plan, still true for any radar)

Numbers from `cad/inverted.py` and doc 06; none seen on real hardware yet.

1. **Radar placement.** The radar hangs in its cradle under the base at the servo end, about 154 mm out from the beam's face, looking back toward the beam and 50 degrees down (55 to 60 if the walk test asks; the cradle clears to 65). People approach from outside, under the beam, toward the radar. The radar sits about 2.28 m up and tilted, so its range is not the floor distance to the doorway; tune `leadms` and the clear distance on the porch, not on the bench. The C4001 and C4002 report range and speed, not position, so the LD2450's `doorwidth` and `xflip` ideas do not apply.
2. **The spider is inside the radar's view.** Retracted it hangs a few cm below the base and about 37 mm toward the beam from the radar; dropped, near the lower edge of the view. It moves during the drop and the rewind and swings after, so the clear rule could see it as a person and hold the device in "waiting for the doorway to clear" after every scare. In S2, read what the sensor reports with the spider at rest, dropped and swinging, then set the sensor's own minimum detect range (`radar range`) past it; check that does not also hide a person standing in the doorway.
3. **Aluminum blocks the radar.** At 24 GHz, aluminum siding or trim stops the signal completely, however thin. If the beam is clad, the radar sees people only once they are under the beam's bottom edge, and flat metal can bounce back phantom targets or jumpy readings. Keep the two-readings rule; do not loosen it to cure late firing. The owner's fix is a steeper tilt.
4. **Line between the spool and the flap is longer.** `include/config.h` has `SPOOL_TO_EYELET_MM 40.0f` (its comment still says braid; the line is bonded nylon thread, size 69). Doc 06 gives 45 mm for the ceiling install and about 72 mm for the inverted one with fairlead v2 (doc 09, 2026-09-28). With 40 the drop-distance limit (`dropMmMax()` = line - 40 - 30) lets the spider stop 15 mm closer to the barrel knot than the 30 mm margin intends, and the rewind estimate in `machine.cpp` is 15 mm short (the 0.75-turn overshoot and the limit switch cover that). Also: the factory `dropmm` 620 only fits the old 720 line; the inverted line is about 636, so the page refuses the new line until `dropmm` is lowered. Fix: make it 72, or a setting, and check the factory `dropmm` fits the inverted line. This is roadmap line 1 and `docs/handoff_task1_firmware.md` step 1.

## Tests (log as S1 to S5 in `docs/commissioning_log.md`, one row per attempt, sensor named)

| # | Test | Pass |
|---|---|---|
| S1 | Power the sensor, meter its current, open the web radar card | `[radar] C4001 answers` in the log (or the C4002 line with 20 data bytes); the moving dot follows a walker |
| S2 | Live readout while walking toward, away from, and across the doorway; spider at rest, dropped, swinging | speed sign for approaching known and put in `C4001_APPROACH_SIGN` (C4002: the direction word checked); spider excluded by the detect range without hiding a person in the doorway |
| S3 | Walk in at normal pace, 10 times | fires every time; spider arrives as you reach the doorway |
| S4 | Walk away, walk past across the hallway, stand still in the window | no trigger |
| S5 | Unplug the sensor's TX wire while armed | fault logged within 1 s; the OUT pin takes over |

## Done when

`sensor 4001` fires the drop on the bench (S3 passes) and the docs in step 8 say so; the C4002 is a second pass of S1 to S5 when it arrives.

## Finish

Changelog line, roadmap line 4 removed, close V15 in `docs/08_open_items.md` with the S1 to S5 log rows, move this file to `docs/retired/`.

## Rules for the session

- The owner is not a developer: verdict first, short, plain English, gloss jargon in a few words. No em dashes, arrows, emojis.
- No motion until he says he is at the device. Lock before any flash. Never plug or unplug the motor with 12 V on. Servo plug back in before any drop. Bench radar on 12 V through the buck, not USB.
- Stage files by name; never `git add -A`.
- The Pi4 is never touched from this repo.
