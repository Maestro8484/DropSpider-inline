# 03 - Sensor

The trigger is a DFRobot Fermion C4002 (SEN0691), a 24 GHz mmWave radar that reports one moving person's distance and speed, with the direction they're going, about ten times a second, plus one still person's distance. It also has an OUT pin that goes high while it sees anyone. On the bench since 2026-10-10; it has fired about 190 drops. Wiring in doc 02, every setting in doc 04, the bench rows in `commissioning_log.md`.

## Why this one

| What it reports | Why it matters here |
|---|---|
| Distance to the moving person, straight line from the sensor | the drop fires at a set distance, so the spider lands as they reach the door |
| Speed toward or away from the sensor, with a direction word | walking in fires it; walking out, walking past or standing still does not |
| A still person's distance | tells the device the doorway is still busy, without being able to fire it |
| OUT pin, high while anyone is in view | the backup trigger: if the serial link goes quiet for 1 s, the firmware fires from the pin until the frames come back |

Only one moving person at a time: two people walking in together read as one. Good enough for a porch.

## Where it sits

- **On the device**, in its printed snap-lid case (`c4002_case_base_extended.stl` with `c4002_case_lid.stl`, my own longer-arm version of `cad/c4002_case.py`'s case) on `c4002_case_Swivel_mount.stl`, bolted under the base at the pad end. The case has an open floor under the two gold antenna squares, so no plastic sits in front of the antenna. The mount tilts on one M3 bolt and swivels left and right, so the radar can be aimed down the walkway from wherever the device hangs.
- **Which way:** the floor opening (the antenna) faces the walkway, the lid faces away. On the inverted install that means it looks along the device toward the beam and down.
- **Tilt:** start at 50 degrees down. At 55 it sees about 2 ft 5 in behind itself, so someone walking out from behind it can fire it; a shallower tilt, toward 30, should stop that (worked out from the field of view, not yet tried). Steeper sees less of the beam. A piece of kitchen foil behind the case (not touching the pins) is the next lever if walk-outs still fire it.
- **Not through metal.** It sees through wood, drywall and plastic, but aluminum siding or trim blocks it completely, however thin. If the porch beam is clad in aluminum, the radar only sees people once they are under the beam's bottom edge, and the metal can bounce back phantom readings. Tilt steeper.
- **The spider is in its view.** With nobody walking, the bench showed still readings at 27 to 30 cm and 86 to 87 cm (the spider at home, or the door frame); a still reading cannot fire or hold the re-arm. Whether the swinging spider ever reads as moving is test S2, not done yet.
- Keep fans, moving curtains and screens out of its view; a screen at 2.2 m once held the doorway "busy" until the clear distance became a setting.

## The trigger rule, as the firmware runs it

Fire when, armed and ready, two readings in a row show someone **approaching** at `approach` cm/s or faster (30 from the factory) and either **within `firecm`** (200 on my mount; 120 from the factory) or, for a fast walker, **arriving within `leadms`** (750 ms). Distance first, timing second: from a 2 m overhead mount the straight-line distance never gets much under a foot and the speed toward the sensor fades to nothing as the person comes under it, so a time-to-arrival rule could not fire at a slow pace. Automatic doors and alarm sensors work the same way, a direction gate plus a distance zone.

Clear again, and re-armed, when nobody moving reads within `clearcm` (150 on my mount, 300 from the factory) for 2 s, or after `clearms` anyway (1 s on my mount; 30 s from the factory). A still reading never holds it.

If the direction word ever reads backwards on a mount, `radarinv 1` (the page's "Direction reads backwards" tick) swaps it. On the bench it reads right as built, so it stays 0.

## The sensor's own settings

These live in the sensor, not the board, so the Radar card has Set and Read buttons for them and they survive a board flash.

| Setting | Console | What |
|---|---|---|
| Detect range | `radar range` | closest and farthest, cm. Set the closest past the hanging spider if it ever reads it. Takes effect after the restart the command does |
| Range step | `radar res` | 80 cm steps to 11.6 m, or 20 cm steps to 4.9 m. 20 for a porch walk; 80 if the walk starts beyond 4.9 m |
| Sensitivity | `radar sens` | motion and presence, low, mid or high. Lower motion if a pet or the swinging spider fires it; lower presence if furniture holds the doorway busy |
| Keep a person for | `radar delay` | 15 s from the factory, which held the doorway busy; 2 s on the bench |
| Learn the empty room | `radar calib` | the page's button: waits, then listens with nobody in view and sets its own thresholds. Do it once at each mount |

Porch numbers to start from, doc 06: range step 80 cm if the walk starts beyond 4.9 m, detect range to about 600, clearcm 300, firecm from a porch walk, then learn the empty room again.

## Bench tests S1 to S5

In `handoff_sensor_bearings.md`, one row each in `commissioning_log.md`: S1 it talks (done), S2 walking toward, away and across plus the swinging spider (the spider swing still owed), S3 ten clean walk-ins (two done), S4 no false fires (owed), S5 the TX wire pulled while armed (owed).

## What else can fire it

`sensor 2410` makes the OUT pin on GPIO33 the only trigger, for any sensor with an active-high output: the C4002's own OUT, an LD2410C, a PIR, a step mat. No direction, no distance.

## Parked, for the record

- **HLK-LD2450**, the first choice (2026-09-24, for its X and Y tracking of up to three people): three modules answered every command and never reported a target, so it was parked 2026-10-07. The design and the record are in `retired/handoff_sensor_ld2450.md`; `ld2450_cradle.stl` was its mount.
- **DFRobot C4001** (SEN0609 and SEN0610): on hand while the C4002 was on order; its three wiring answers are in doc 02. The firmware now speaks the C4002 only.
- **HLK-LD2410C**: was the fallback on the OUT pin. Not needed, the C4002's own OUT pin is the backup.
