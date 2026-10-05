# Handoff: spool Rev C.4, the line must stay on the spool

The line comes off the far (606ZZ) side of `spool_onepiece` and winds onto the rod and spacer (owner 2026-10-04: "line slips off side once = spool all off on smaller axle side"). Redesign the spool so it cannot, keeping what the one-piece fixed. For a CAD session working with the owner (Joe).

## Ground truth first

This file is a work order, not a record. The repo on disk wins: `cad/generate.py` is the source of truth for every dimension below. If this file and the code disagree, the code is right and this file is stale; say so out loud. Staleness check:

```
git log -1 --oneline                                  # where the repo is now
git log -1 --oneline -- docs/handoff_spool_rev_c4.md  # when this file was last true
```

## Before you start

1. Ask Joe one line: is `spool_onepiece` the spool on the rod, and where did the line climb out (over the far flange, between the flange and spacer B)? This handoff assumes yes and over the far flange. If it is the old three-part stack, the causes below change; stop and re-read.
2. Run `cd cad; python generate.py`; every line of the "one-piece spool" block must pass before you change anything.
3. Read open item V22 in `docs/08_open_items.md`: the causes found in the model, which this work removes.

## What the model shows (the causes, each checked in `cad/generate.py`)

- **The far wall is 2 mm tall and a ramp.** `OP_FLANGE_R` 27 against the 25 barrel, and its inner face is the 45 degree chamfer that let it print without supports: a slope the line can walk up. The old Rev C.2 walls were 7 mm (r 32), vertical.
- **The line feeds onto that ramp, not the barrel.** The line leaves the spool toward the base hole at z 45 (`inverted.LINE_Z`). After the finger moved 2.5 mm nearer the servo, the barrel sits at z 41 to 44.5 (`OP_Z0` 32.5), so the feed point is 0.5 mm past the barrel's far edge, on the ramp. The 2.5 mm shim move given to Joe on 2026-10-02 put it there.
- **The motor-side wall is 3 mm** (separator r 28), the most the finger allows (it reaches in to r 29.4); the ratchet face beyond it stands to r 29.
- **Light line, light spider.** 3 lb mono and a 13 g spider: about 0.13 N of tension on the wraps, so they wind loose, and a loose coil of mono springs outward. Not measured.
- Prior art, read 2026-10-04: winch drums keep the flange at least 2.5 line diameters above the top wrap and the fleet angle (line's angle off square to the drum) under 2 degrees on a smooth drum ([Firgelli](https://www.firgelliauto.com/blogs/mechanisms/drum-and-rope-conversion), [Dymot](https://www.dymot.co.za/rope-fleeting-angle/)). Those rules assume a tensioned rope. Here the wall is 10 line diameters, which passes the rule, so the escape is slack and loose wraps plus the off-centre feed, the fishing reel's problem more than the winch's.

## Stopgap Joe can do now, no printing (give it to him first)

1. Far side, in this order: spool, the old `spool_shield` disc (64 mm, already printed), a 12 mm shim, spacer B. The disc is a 7 mm vertical wall.
2. Shift the spool 2 mm toward the 606ZZ: a 2 mm shim between the coupler and `spacer_A_nose_7_5mm`, and 3.5 mm less on the 606ZZ side (2 for the shift, 1.5 for the disc). The barrel then sits under the line hole; the teeth still overlap the finger 5 mm, the minimum in doc 05 step 14.
3. Rewind the line under a little hand tension so the wraps lie tight.

## The work, in order (advised design; build it, then show Joe)

1. **Keep the body's good parts:** bearing seat with shoulder and snap lip, teeth straight across the finger (z 32.5 to 39.5), separator r 28, printed line hole, ratchet face down with no supports.
2. **Centre the barrel on the line:** thicken the separator from 1.5 to 3.75 mm so the 3.5 mm barrel runs z 43.25 to 46.75, centred on z 45. Add a check to `onepiece_checks`: the feed point (`inverted.LINE_Z`) lies inside the barrel's flat with at least 1 mm to spare each side.
3. **Far wall as a separate flat cap:** the body ends at the barrel's far edge (no ramp). A 2 mm disc, r 32 (7 mm above the barrel), vertical face toward the line, centre hole 7.0, three lugs that drop into the three spoke windows so it turns with the spool. Spacer B (or a 12 mm shim) clamps it; no screws, no glue. It prints flat with no supports. The bearing stays wholly in the body, so the wobble fix is kept. Export `spool_cap.stl`.
4. **Line hole** stays mid-barrel (it moves to z 45 with the barrel); re-run the stub check.
5. **Stack:** body plus cap in the model is about 16.25 long (z 32.5 to 48.75); write the new spacer and shim numbers for Joe's build, as a change from what he has on the rod.
6. **Optional, offer, do not default: PTFE guide tube (Joe's idea, 4 mm OD).** What it can and cannot do, from the model: it cannot enter the 3.5 mm channel (4 mm OD) and its tip must stay outside the spinning teeth and cap plus 2 mm (r 35), so the tip ends about 25 mm below where the line leaves the barrel. It is then a closer, low-friction fairlead that sets where along the barrel the line lands; it does not stop a loose coil jumping a low wall. The base hole (7 mm) takes it with about 1.5 mm of sideways play; the fairlead block's 3.2 mm throat does not, so the tube ends above the block unless the block is reprinted with a 4.1 bore. Worth it if the PLA bore's friction slows the 13 g spider; design a printed holder only if Joe says yes.
7. **Optional, offer: taper the barrel 1 to 2 degrees,** larger at the separator, so tension slides the wraps toward the tall cap and away from the 3 mm separator. Physics, not tested; build only if the bench test still shows climbing on the motor side.
8. Export only the changed STLs. Update doc 01's one-piece section and print table, doc 05 section B, and the build guide's spool step; close V22 when the bench test passes.

## Tests

- `python generate.py`: all one-piece checks pass, plus the new feed-point check; the cap is watertight and prints flat.
- `python inverted.py`: line path and every check unchanged.
- Bench, logged by Joe in `docs/commissioning_log.md`: 2.2 m of line on (1.5 m spare), ten drops and rewinds with the real spider, no wrap leaves the barrel. A phone slow-motion video of one drop: if loose loops form on the spool during the drop or the bounce, that is the spool running on after the spider slows (a baitcaster backlash), a firmware matter for `docs/handoff_task1_firmware.md`, not this spool.

## Done when

Ten drops and rewinds on the bench with no line off the spool, and the docs describe the new spool.

## Rules for the session

- Make the parts and stop. Slicer settings are Joe's; deliver STLs only.
- Export only the changed STLs; no full rebuild, no mass picture regeneration.
- Every direction is seen from behind the motor.
- Decisions go to Joe as one flat numbered list, the question in bold on each item.
- Plain English, no em dashes, no arrows.
