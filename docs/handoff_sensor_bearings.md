# Handoff: trigger sensor, the DFRobot C4002 as `sensor 4002`

Work order: finish the bench of the DFRobot C4002 radar (SEN0691, 24 GHz) as the trigger, then carry the numbers to the porch. The firmware, the case and the wiring are done and on the device; the radar has fired the drop. What is left is in "The work, in order". The file name is historical; bearing care is in doc 01. The LD2450 design is retired: `docs/retired/handoff_sensor_ld2450.md`.

**Ground truth:** the repo on disk wins over this file, and the board wins over both. Staleness check: `git log -1 --oneline` against `git log -1 --oneline -- docs/handoff_sensor_bearings.md`; a different hash means commits landed after this was written, read `CHANGELOG.md` for them. Every bench result so far is in `docs/commissioning_log.md`, rows dated 2026-10-10.

## State facts, recorded at the close of 2026-10-13 (each line says how it was read)

Staleness check: compare `git log -1 --oneline` with `git log -1 --oneline -- docs/handoff_sensor_bearings.md`; a different hash means work landed after this was written.

- **Mount:** the device is over the inside of the front door, about 7.5 ft up (owner). Radar on the owner's new parts: `c4002_case_base_extended.stl` (19 mm longer pivot to case) on `c4002_case_Swivel_mount.stl` (swivels left and right as well as tilting). Being remounted and re-aimed by the owner at the close; tilt and swivel not yet known.
- **On the board, FLASHED (f82b153), read from `/api/status`:** ready, home, no fault, disarmed (armed saved 0). dropmm 607 (the owner's own teach from the page, kept by him), droprpm 600 (700 skipped steps, log 2026-10-12), dropacc 80000, dropdec 60000, rearm 0, clearms 1000, firecm 200, clearcm 150, approach 30, radar detect range 0 to 300.
- **VERIFIED:** a power-up with the spider down stops on a fault instead of arming; the C4002 at 10 frames a second; drops at 600 rpm without skipped steps; the page teach sets dropmm from the wound length.
- **FLASHED, NOT yet exercised:** 3 presses of the limit switch = bring it home (lower 1/2 turn, wind at 80 rpm, clear the fault, re-arm); every rewind after a drop finishes at 80 rpm; one slow second try when a rewind misses the switch; `lastlog` (page: Last fault log) keeps the log up to a fault through a power cut.
- **Open, not the sensor's:** rewinds that never close the switch (3 on record, 0 switch edges, spider at the top or part way). If one comes back, read `lastlog` before anything else.
- **Timing, measured 2026-10-12:** trigger to end of drop about 1.7 s; the fall is about 0.7 s, the rest is the release (driver start 200 ms, finger wait 500 ms, a driver reset of about 220 ms because the unload hits the switch every time).
- **Field of view page:** https://claude.ai/artifact/HBP7CQnUQara66fL5Zy2jv (computed: at 55 degrees down the radar sees about 2 ft 5 in behind itself; about 30 degrees down stops walk-out drops).

## Why the rule is proximity (so nobody re-litigates it)

The sensor gives the straight-line distance from itself to the person and the speed along that line. From a 2 m overhead mount the distance never gets much under a foot (the head), and the speed toward the sensor fades to zero as the person comes under it. So "distance divided by speed" never got small at a slow pace, and the lead-time rule could not fire at any lead time under about 1500 ms (log rows, run 1). The owner ruled 2026-10-10: "it needs to be less timed and more proximity-based triggering". The rule now: armed and ready, two readings in a row, someone approaching at `approach` cm/s or faster, and either within `firecm` or (for a fast walker) arriving within `leadms`. Automatic doors and alarm sensors work the same way: a direction gate plus a distance zone. Do not build a time-to-arrival rule back in.

## Read first

1. `docs/commissioning_log.md`, the 2026-10-10 rows, bottom up: every number above came from one of them.
2. The radar card on the page (`http://dropspider.local`): every setting named here is a control on it, with a one-line hint, and a check line under the sensor's knobs says where a person is when the spider lands at the current fire distance.
3. Doc 04, the settings and the `radar` commands, if a name is unclear.

## Gate for any flash or motion

The owner says he is at the device and `status` shows busy 0, driverOn 0, ready. Before a flash the spider is seated on the finger with the motor off (that is the lock state the board leaves after every move). The session runs every command itself; the owner is never handed one. One motion command per turn, read the board back, write the log row, then the next.

## The work, in order

1. **Arm and walk in (owner at the device).** When the owner says the radar is remounted and aimed: `arm`, `save`, then he walks in three times at normal pace; read each from the board log, one log row each. Then three walk-outs from behind the door side. If walk-outs fire, the tilt is the lever (shallower, toward 30 degrees down, per the field of view page), then a steel shroud.
2. **Exercise the new rewind code** on the first drops: the log must show the slow finish, and any miss must show the second try. One row each.
3. **Release time, owner's call (asked 2026-10-12, not answered):** seat the spider about 1/2 in lower so the unload stops hitting the switch (saves the 220 ms driver reset), and shorten the finger wait from 500 to 300 ms. Each needs 2 or 3 test drops.
4. **Learn the empty room** at this mount, hall empty for 40 s (radar card button).
5. **S2 swinging spider, S4 no trigger, S5 the wire**, as below, at this mount.
6. **Porch numbers when it hangs there** (doc 06): range step 80 cm if the walk starts beyond 4.9 m, detect range to about 600, clearcm 300, firecm from a porch walk, learn the empty room again.
7. **Build guide section 10 radar card drawing** (team, any time): still the old LD2450 view; redraw for the C4002 and the owner's swivel mount, then `python tools/make_build_guide.py`.
8. **Docs** after the bench: doc 02, doc 04 if anything changed, doc 07 step 12, `CHANGELOG.md`. Commit by name.

## Tests (S1 to S5 in `docs/commissioning_log.md`, one row per attempt)

| # | Test | Pass | Where it stands 2026-10-10 |
|---|---|---|---|
| S1 | Power the sensor, open the web radar card | `[radar] C4002 answers` and 18 data bytes in the log; the reading follows a walker | PASS (current draw dropped by the owner) |
| S2 | Live readout walking toward, away from, and across the doorway; spider at rest, dropped, swinging | direction word checked on the tilted mount; spider at rest not reported | PASS for the walk and the spider at rest; swinging not done |
| S3 | Walk in at normal pace, 10 times | fires every time; spider arrives as you reach the doorway | 2 of 10, both fired, both late at fire distance 120; now 200 |
| S4 | Walk away, walk past across the hallway, stand still in the window | no trigger | not done |
| S5 | Unplug the sensor's TX wire while armed | fault logged within 1 s; the OUT pin takes over | fallback seen on a sensor restart; the wire pull not done |

## Done when

`sensor 4002` in its case fires the drop on the bench (S3 ten of ten with the spider arriving on time), S4 and S5 pass, and the docs in step 9 say so.

## Finish

Changelog line, roadmap line 4 removed, close V15 in `docs/08_open_items.md` with the S1 to S5 log rows, move this file to `docs/retired/`.

## Rules for the session

- The owner is not a developer: verdict first, short, plain English, gloss jargon in a few words. No em dashes, arrows, emojis. A question gets a one-line answer and no work.
- No flash and no motion until he says he is at the device and the board shows busy 0, driverOn 0, ready. Never plug or unplug the motor with 12 V on. Servo plug back in before any drop.
- Never hand him a command to run.
- Stage files by name; never `git add -A`.
- The Pi4 is never touched from this repo.
- Freedom units when talking to him about the room (feet and inches); the settings stay in cm because the sensor and the firmware are.
