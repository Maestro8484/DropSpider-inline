# Handoff: vertical-face mount (draft designed, print is the next step)

What this is for: the record of the wall install draft for hanging the DropSpider from the inside face of the porch's front beam, and what the next session does once the owner has printed and hung it. The design lives in `cad/wall_hinge.py`; the owner-facing description is the "Alternative: hanging from the beam's inside face" section of `06_installation.md`.

## Ground truth first

This file is a pointer, not a record of truth. The local repo wins. If anything here disagrees with a file, the file is right and this handoff is stale: say so out loud.

Staleness check, run first:

```
git log -1 --oneline                                   # where the repo is now
git log -1 --oneline -- docs/handoff_vertical_mount.md # when this handoff was last true
```

Same hash: nothing landed since it was written. Different: re-verify every state line below against the file it names.

## The owner's ruling, 2026-09-27

His plan, in his words: "retain existing bracket with some modification... hinge on one end (the end containing the pcb mounting plate probably) ---> hinge perpendicular to another plate with opposing hinge for M3 bolt or an additional 6mm axle... then have two eyes at both ends with light duty chain or thin paracord securing both ends of the device + perpendicularly mounted bracket resulting in a 90 degree perpendicular orientation". On being shown a one-piece braced shelf instead: "this is over-engineered dude - that's why MY plan was easy, quick rapid print and working draft". The braced shelf stays in `cad/wall_mount.py` as a fallback and is out of the print list.

## State facts, recorded 2026-09-27, each with how it was checked

| Fact | How checked |
|---|---|
| `cad/wall_hinge.py` builds `hinge_plate` (18 cm3, 88 x 46 x 13.5) and `hinge_clip` (2 cm3, print two); both watertight; both in `generate.py` `PARTS` and exported to `cad/stl` | `python wall_hinge.py`, `python generate.py` |
| Plate, clips, pins and cords clear every device part; the pin holes line up through both forks and the knuckle; the device swings 0, 30, 60, 90 degrees on the hinge without touching the plate | same run: `clear every device part`, `True`, four `clear of the plate` |
| Prints: plate beam-face down, 80 mm2 unsupported; clip on its end, 16 mm2 | same run, print lines |
| Cords rise 40 over 159 mm (14 degrees), lever 36 mm about the hinge: 12 N standing, 63 N on a line snap, both cords together | same run, `cords:` block (estimate from a 480 g device, not measured) |
| Device top 45 mm below the ceiling (`PLATE_H`); a spider up to about 90 mm tall stays hidden behind a 254 mm beam | arithmetic in the report: spider height + 160 < 254 |
| Line falls 77 mm from the beam's face | same run |
| Picture `docs/img/wall_install.png` | `render.py` `wall_png()`, looked at |
| Docs: 06 (section rewritten), 05 (section G), 01 (print table, fastener line), 08 (V18), BOM (W1 to W3, PRINT-WALL), `cad/README.md`, CLAUDE.md task 4 | read back |
| Nothing printed, nothing hung | no print, no test |

## Why the device hangs below the ceiling (the one design fact to keep)

A cord only pulls. To hold the far end level it must run up from the device to an anchor above the hinge, and no anchor can be above the ceiling. So the hinge is at the plate's bottom, the eyes at its top, and the device's top sits `PLATE_H` below the ceiling. With the hinge at the ceiling the cords would be level and carry nothing. `PLATE_H` trades spider hiding (smaller is better) against cord pull (smaller is harder); 45 is the draft value.

## What the next session does

1. Owner prints one plate and two clips. Fit check the usual way: the knuckle hole is drawn 3.5 for a free M3, the fork holes 3.4, the eye 4.0; printed holes come out 0.1 to 0.3 small.
2. Bench hang: two screws in a scrap board, plate on, device on the pins, cords tied, 5 kg pull on the far end. Record it against V18 in `08_open_items.md`.
3. If it sags or bounces on the drop: shorten `PLATE_H` for a steeper cord, or move to the braced shelf in `cad/wall_mount.py`.
4. Radar: the owner decides after the first walk test whether it stays on the device (looks toward the door here) or goes under the beam on `ld2450_fork_screw`.

## Constraints that still bind

- CLAUDE.md hard constraints (motor-led drop, the 6 lb line must stretch, no braid without the elastic snubber).
- Existing hardware only: M3 bolts and nuts, #4 x 1 in wood screws (already on the BOM), cord or chain the owner has.
- The bracket is printed and final; the clips bolt to it.
- No glue.
