# Handoff: vertical-face mount (draft designed to the owner's plan, print is the next step)

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

## The owner's ruling, 2026-09-27, second pass

On the cord version: "what drawign makes no sense - the hinge plate is excessively short in relation to its utility and where is the 45degree connector between the two plates endsd?" So: the plate is tall, the hinge is at its top, the device sits at the ceiling, and a bar at about 45 degrees joins the far ends of the two plates at each side. That bar is pushed, not pulled (the weight folds the hinge shut), so it is a printed strut, not chain.

## State facts, recorded 2026-09-27, each with how it was checked

| Fact | How checked |
|---|---|
| `cad/wall_hinge.py` builds `hinge_plate` (29 cm3, 181 x 159 x 13.5), `hinge_clip` (2 cm3, print two), `tie_bar` (12 cm3), `strut` (12 cm3, print two); all watertight; all in `generate.py` `PARTS` and exported to `cad/stl` | `python wall_hinge.py`, `python generate.py` |
| Plate, clips, tie bar and struts clear every device part and each other; all six pins pass through their holes; all four wood screws have a straight screwdriver path (struts not yet on); the device swings on the hinge clear of the plate from level down to 65 degrees (the rod touches a leg at 70) | same run |
| Prints: plate beam-face down 176 mm2 unsupported; clip 16; tie bar 43; strut 0 | same run, print lines |
| Struts: 206 mm at 40 degrees, lever 111 mm about the hinge; pushed 4 N standing, 20 N on a line snap, both together; one 7 x 8 strut buckles at about 160 N (margin 5 on the x3 load) | same run (estimate from a 480 g device, not measured) |
| Device top 8 mm below the ceiling; a spider up to about 130 mm tall stays hidden behind a 254 mm beam; line 77 mm from the beam's face | same run |
| Picture `docs/img/wall_install.png` | `render.py` `wall_png()`, looked at |
| Docs: 06 (section rewritten), 05 (section G), 01 (print table, fastener line), 08 (V18), BOM (W1 to W3, PRINT-WALL), `cad/README.md`, CLAUDE.md task 4 | read back |
| Nothing printed, nothing hung | no print, no test |

## What the next session does

1. Owner prints the five parts (one plate, two clips, one tie bar, two struts). Fit check the usual way: turning holes (knuckles, strut eyes) drawn 3.5, holding holes 3.4; printed holes come out 0.1 to 0.3 small.
2. Bench hang: four screws in a scrap board, plate on, clips and tie bar on the device, pins in, 5 kg pull on the far end. Record it against V18 in `08_open_items.md`.
3. If a strut bows: raise `STRUT_D` in `cad/wall_hinge.py`. If the install is awkward on the ladder: the braced one-piece shelf in `cad/wall_mount.py` is the fallback.
4. Radar: the owner decides after the first walk test whether it stays on the device (looks toward the door here) or goes under the beam on `ld2450_fork_screw`.

## Constraints that still bind

- CLAUDE.md hard constraints (motor-led drop, the 6 lb line must stretch, no braid without the elastic snubber).
- Existing hardware only: M3 bolts and nuts, #4 x 1 in wood screws (already on the BOM), cord or chain the owner has.
- The bracket is printed and final; the clips bolt to it.
- No glue.
