# Handoff: vertical-face mount (strategy session)

What this is for: a fresh session designs a way to hang the DropSpider from a vertical face (the inside, back face of the porch's front beam, hidden from people walking in) while the device keeps its current orientation: rod level, bracket ceiling face level and on top, spider dropping straight down.

## Ground truth first

This file is a pointer, not a record of truth. The local repo wins. If anything here disagrees with a file, the file is right and this handoff is stale: say so out loud.

Staleness check, run first:

```
git log -1 --oneline                                   # where the repo is now
git log -1 --oneline -- docs/handoff_vertical_mount.md # when this handoff was last true
```

Same hash: nothing landed since it was written. Different: re-verify every state line below against the file it names.

## State facts, recorded 2026-09-27, each with how it was checked

| Fact | How checked |
|---|---|
| Bracket: base plate x -24..75, y 0..4, z 0..110; electronics pad x -88..-24, y 0..3, z 18..93; ceiling face is y = 0. Whole bracket 163 x 110 mm footprint, 62 mm tall | `cad/generate.py` `bracket()`, and bounds printed from `G.assembly()` |
| Whole device envelope: x -88..75, y 0..112 (lowest point is the limit switch), z -32..120 (motor sticks out to z -32) | bounds of every part in `G.assembly()` |
| Ceiling mount today: 2 holes 3.4 mm at x 65, z 20 and z 90 in the base; 6 holes 3.2 mm in the pad (x -80, -56, -32 by z 28, 83); the x -32 pair is countersunk for the fairlead's 2 flat-head screws | `bracket()` cuts; `cad/bracket_footprint.svg` |
| Nothing may stick out of the ceiling face (y = 0) in the CEILING install. In a vertical-face install nothing touches the ceiling, so that rule may relax: decide it explicitly | `cad/README.md` lessons |
| The bracket is printed and final. Additions should bolt or screw to it; a reprint is the owner's call | `cad/README.md` lessons |
| Radar (LD2450) sits at the +x (servo) end, looking out along +x, tilted 50 degrees down, in `ld2450_cradle` on `ld2450_fork` under the bracket | `cad/sensor_mount.py`; radar bounds x 25..60 |
| Porch: 8 ft ceiling, front beam hangs 10 in (254 mm), device today 12 in (305 mm) behind the beam's back face, rod parallel to the beam, servo/radar end toward the beam | `docs/06_installation.md` |
| Printed PLA in the device: about 171 cm3 (roughly 130 to 210 g depending on infill), plus motor, servo, spool hardware, spider (60 g max) | volumes summed from `G.assembly()`; spider limit in the build guide |
| Worst-case load: if the motor loses grip, the 6 lb monofilament line snaps at about 27 N; estimated peak about 12 N for a 60 g spider. The mount must hold the device plus that | `docs/01_mechanical_design.md` (estimate, not measured) |
| No glue anywhere the owner can avoid it; the fairlead is screwed on at the bench | owner, 2026-09-26 |

## The owner's tentative concept, in his words (starting point, not a ruling)

"retain existing bracket with some modification... or if additional strength may be necessary to design additional ribs/material to have a hinge on one end (the end containing the pcb mounting plate probably) ---> hinge perpendicular to another plate with opposing hinge for M3 bolt or an additional 6mm axle (duplicate one of the ones used for the existing axle/spindle), then have two eyes at both ends with light duty chain or thin paracord securing both ends of the device + perpendicularly mounted bracket resulting in a 90 degree perpendicular orientation"

Read as: a wall plate screwed to the vertical face; the device's bracket hinges to it along one edge (hinge pin = an M3 bolt or a second 6 mm rod); two tie points on the far edge of the device run light chain or thin paracord up to two tie points high on the wall plate, holding the device level at 90 degrees to the wall. This is the fold-down shelf with chain stays, a known pattern.

## The job for the strategy session

1. **Prior-art search first** (new design, so the global rule's case (a) applies). Web and GitHub, practitioner's words: "3D printed wall mount bracket hinge", "fold down shelf chain support", "drop leaf shelf bracket", "cantilever wall bracket knee brace 3D print", "printed hinge M3 bolt pin". Report a small table: project, license, what it does that we need, copy / borrow / ignore.
2. **Settle the decisions below with the owner**, one flat numbered list, advice and the yes/no question on each item.
3. **Design it** in the repo's own tool: a new `cad/wall_mount.py` (pattern: `cad/sensor_mount.py`), parts as functions with `*_print()` orientations, added to `PARTS` in `generate.py`, placed in `assembly()` for a new "wall" layout, clash checked against every part.
4. **Checks to add and pass**: watertight; no clash with any part at the installed pose; print overhang report (down-facing area off the bed) like `fairlead.py` has; hinge pin clearance (fit check numbers from this project: holes print 0.1 to 0.3 mm small; a free pin wants about 0.25 mm a side); strength by the load above with a stated margin.
5. **Pictures**: a render of the device hanging from the wall plate, and an exploded view; then doc updates (06 install, 05 assembly, BOM).

## Decisions the session must put to the owner (with this session's advice)

1. **Which end goes against the wall.** The radar is at the +x (servo) end and must look out toward people walking in. If the device hangs on the beam's inside face with the pad (-x) end at the wall, as the owner suggested, the radar ends up facing inward, away from the approach. If the +x end goes at the wall, the radar looks into the beam. Advice: pad end at the wall as suggested, and move the radar to its own small mount on the wall plate below the beam's bottom edge, looking out; its cable runs along the plate.
2. **Hinge plus chain stays, or a rigid 90 degree bracket with a knee brace (a diagonal gusset).** Hinge and chain: folds flat, easy to hang, adjustable level, but it can swing when the motor jerks. Rigid knee brace: no swing, simpler, more plastic. Advice: rigid knee brace, because the motor-led drop and the stop yank the device every cycle and a swinging device throws off the spider's stop height and the radar's aim.
3. **Hinge pin**: M3 bolt, or a second 6 mm rod. Advice: M3 bolt if hinged (already in the parts bin; a 6 mm rod is overkill at these loads).
4. **Where the line falls.** Today the spider drops 305 mm behind the beam. On the beam's face it drops about 100 mm or less from the beam. Advice: owner decides by walking under it; a closer drop surprises sooner but risks brushing the beam.
5. **Reprint the bracket or bolt on.** Advice: bolt on through the existing pad and base holes first; only reprint if the strength numbers fail.

## Constraints

- CLAUDE.md hard constraints all apply (motor-led drop, snubber rule now: the 6 lb monofilament line must stretch, no braid without elastic).
- Existing hardware only (Rev C.1 owner rule): M3 and M2 bolts, 6 mm rod stock, paracord or light chain the owner has. Ask before listing anything to buy.
- Print on the owner's Bambu, PLA, no supports, orientation set in code. Lessons in `cad/README.md` apply (recesses face up or use stepped bridging; every member starts on the bed; flat mounting faces are one plane).
- Expensive-work rule: no long runs without asking. The rebuild (`tools\regen_cad.ps1`) is cheap and allowed.
