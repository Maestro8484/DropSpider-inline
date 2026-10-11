# Handoff: trigger sensor, the DFRobot C4002 as `sensor 4002`

Work order: finish the bench of the DFRobot C4002 radar (SEN0691, 24 GHz) as the trigger, then carry the numbers to the porch. The firmware, the case and the wiring are done and on the device; the radar has fired the drop. What is left is in "The work, in order". The file name is historical; bearing care is in doc 01. The LD2450 design is retired: `docs/retired/handoff_sensor_ld2450.md`.

**Ground truth:** the repo on disk wins over this file, and the board wins over both. Staleness check: `git log -1 --oneline` against `git log -1 --oneline -- docs/handoff_sensor_bearings.md`; a different hash means commits landed after this was written, read `CHANGELOG.md` for them. Every bench result so far is in `docs/commissioning_log.md`, rows dated 2026-10-10.

## State facts, recorded at the close of 2026-10-10 (each line says how it was read)

- **On the board, FLASHED and VERIFIED:** the C4002 talks at 115200, 18 data bytes per result frame, 10 frames a second, 0 bad frames (board log and `/api/radar`). Direction word 2 = approaching, negative speed = approaching, so `radarinv` stays 0 (walk test, sampled). Keeps its report period through a power cut (boot log order). Silent-link fallback to the OUT pin and back both fire (board log during a sensor restart). The radar fired the drop twice, drops 27 and 28, each a clean cycle to the switch and the lock (board log).
- **Settings saved on the board** (`/api/status`): `sensor 4002`, `approach 30`, `firecm 200`, `clearcm 150`, `leadms 1200`, `radarinv 0`. `firecm` and `clearcm` are the office numbers, not the porch's.
- **Settings kept in the sensor** (read back with `radar res`, `radar delay`, `radar sens`, `radar range`): detect range 0 to 300 cm, range step 20 cm, disappear delay 2 s (shipped at 15 s), motion and presence sensitivity mid (as shipped). Learn the empty room has NOT been run.
- **The mount is a mockup:** office doorway, 6 ft 10 in up, 55 degrees down, facing out into the hall. A screen (a magic mirror) with a dresser sits about 6.5 ft in front of it and reads as a still person at about 2.2 m. The owner's chair is behind the sensor at its 4 o'clock and the radar sees him there through its back.
- **Not measured, by the owner's call:** the sensor's current draw.
- **Open, not the sensor's:** one page drop on 2026-10-10 rewound its full 750 mm without the switch closing, with the spider ending at the top in the locked position; later rewinds all stopped at the switch. The switch itself works (5 hand presses logged). Watch the flap on the next few rewinds.

## Why the rule is proximity (so nobody re-litigates it)

The sensor gives the straight-line distance from itself to the person and the speed along that line. From a 2 m overhead mount the distance never gets much under a foot (the head), and the speed toward the sensor fades to zero as the person comes under it. So "distance divided by speed" never got small at a slow pace, and the lead-time rule could not fire at any lead time under about 1500 ms (log rows, run 1). The owner ruled 2026-10-10: "it needs to be less timed and more proximity-based triggering". The rule now: armed and ready, two readings in a row, someone approaching at `approach` cm/s or faster, and either within `firecm` or (for a fast walker) arriving within `leadms`. Automatic doors and alarm sensors work the same way: a direction gate plus a distance zone. Do not build a time-to-arrival rule back in.

## Read first

1. `docs/commissioning_log.md`, the 2026-10-10 rows, bottom up: every number above came from one of them.
2. The radar card on the page (`http://dropspider.local`): every setting named here is a control on it, with a one-line hint, and a check line under the sensor's knobs says where a person is when the spider lands at the current fire distance.
3. Doc 04, the settings and the `radar` commands, if a name is unclear.

## Gate for any flash or motion

The owner says he is at the device and `status` shows busy 0, driverOn 0, ready. Before a flash the spider is seated on the finger with the motor off (that is the lock state the board leaves after every move). The session runs every command itself; the owner is never handed one. One motion command per turn, read the board back, write the log row, then the next.

## The work, in order

1. **Foil behind the sensor (owner).** Kitchen foil or aluminum tape on the outside of the case lid, covering the back of the board, touching no pin. Why: walking out of the office is an approach from behind, and the radar sees through its back; on the porch that is anyone stepping out the front door. Then the test: owner inside the office, walks out under the sensor at normal pace, three times, device armed; the board log must show no `[cycle] trigger: radar`. If it still fires, a second layer and a wider patch; if that fails, the mount angle is the lever (steeper down means less view behind).
2. **Learn the empty room.** The card's button (10 s to leave, 30 s of listening) with everyone and the dog out of the sensor's view until the chip on the card goes away. Then read the sensitivity selects: they should say custom. Why: the sensor sets its own per-step thresholds from the room's noise, which is DFRobot's answer to the screen at 2.2 m. If the still reading at about 2.2 m is gone afterwards, `clearcm` can go back toward 300 here; if not, leave `clearcm` 150 for the office.
3. **S3, the count.** Fire distance 200 cm, owner walks in from the hall at normal pace, straight through under it, stepping out of view between runs so it re-arms (the chip says armed, doorway clear). Ten runs, one log row each, with the owner's one-line view of each (early, on time, late). Read the card's check line after the first: it says where the person is when the spider lands at the current fire distance; raise `firecm` if the spider lands behind them, lower it if it lands while they are still out in the hall. Save settings.
4. **S2, the swinging spider.** Device disarmed, spider hanging after a drop (page Drop, then watch the card while it swings, then still). The card must not say "someone moving, approaching" at 30 cm/s or more for two readings while it swings; if it does, motion sensitivity low on the card, and note it.
5. **S4, no trigger.** Armed. Walk away from under it, walk across the hall past the doorway, stand still in the doorway for 30 s. Three log rows; `drops` on the page must not move.
6. **S5, the wire.** Armed, nobody near. Owner pulls the sensor's TX wire (the one on GPIO16) for 5 s and puts it back. Board log must show `[radar] FAULT: no result frame for 1000 ms` within a second and `[radar] frames back` after. One row.
7. **Porch numbers, when it hangs there (doc 06).** Range step 80 cm if the walk starts beyond 4.9 m, else keep 20. Detect range 0 to about 600. `clearcm` 300. `firecm` from a walk at the porch: the check line on the card gives the landing point. Learn the empty room again on the porch, at night with the porch empty. Then `save`.
8. **Build guide section 10 radar card drawing** (team, any time): it is still the old LD2450 top view; only its label says C4002. Redraw from the C4002 card in the wiring section, run `python tools/make_build_guide.py`.
9. **Docs** after the bench: doc 02 current (the five wires are right), doc 04 if any setting or command changed, doc 07 step 12, `CHANGELOG.md`. Commit by name.

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
