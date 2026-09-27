# Handoff: vertical-face mount (designed, waiting on the owner's rulings)

What this is for: the record of the wall-mount design for hanging the DropSpider from the inside face of the porch's front beam, the rulings the owner still has to give, and what the next session does after he gives them. The design itself lives in `cad/wall_mount.py`; the owner-facing description is the "Alternative: hanging from the beam's inside face" section of `06_installation.md`.

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
| `cad/wall_mount.py` builds `wall_mount` (shelf, wall plate, two end braces, one part, 212 cm3) and `ld2450_fork_screw` (the radar fork with a 44 mm plate and two #4 screw holes) | `python wall_mount.py`: both `watertight=True` |
| The mount clears every device part at the installed pose; the device's ceiling face lies on the shelf's underside (highest device point y 0.0) | same run: `wall_mount clears every device part` |
| All 6 nut pockets are open voids (the cut landed); the print stands shelf-top-down, 169 x 154 footprint, 85 tall, 217 mm2 of bridged ceiling (the 6 pockets), 24,411 mm2 on the bed | same run: `nut pockets are open on all 6 holes: True`, print lines |
| All 4 wood screws have a straight 6 mm driver path along x past the device | same run: four `clear` lines |
| The radar under the beam clears the beam, the plate and the device at every tilt 0 to 60 in 10 degree steps; the fork plate sits on the beam's underside (y 249.0 both) | same run: seven `clear` lines |
| Strength (estimate, not measured): 6.85 N m at the wall with a safety factor of 3; braces 0.68 MPa (margin 30 on a 20 MPa layer bond); 52 N per top screw; 16 N per device bolt with six | same run: `load:` block |
| Both parts export from `generate.py` (`PARTS` has `wall_mount` and `ld2450_fork_screw`); the full rebuild passes with no clash and every part watertight | `tools\regen_cad.ps1`, output read |
| Pictures: `docs/img/wall_install.png` (device on the beam, radar under it) and `docs/img/wall_exploded.png` (mount lifted, nuts above, bolts below, screws out) | rendered by `render.py` `wall_png()` and `wall_exploded_png()`, both looked at |
| Docs updated: 06 (new section), 05 (section G), 01 (print table rows, fastener line), 08 (V18), BOM (N7 note, W1, PRINT-WALL), `cad/README.md` (file, check, two lessons), CLAUDE.md task 4 | files read back after the patch |
| Nothing is printed. The wall mount has never carried a load | no print, no test |

## What was decided by the session, and why (the owner has not ruled yet)

The 2026-09-27 handoff asked for a prior-art search, then the decisions below. The search (web and GitHub, 8 verified hits) named the field: the fixed form is a gusseted L-bracket or knee brace; the owner's hinge-and-chain form is a folding shelf bracket. Usable numbers from it: a free pin wants 0.25 mm a side; a gusset should be at least as thick as the wall it stiffens and reach at least half the arm; PLA creeps under a permanent load; a PLA bracket in its weakest print orientation still held over 40 kg in one test. The two best models (CarbonProp's folding wall bracket on Printables, CC BY-NC, and MagnetDanny's parametric reinforced L-bracket on MakerWorld) were read for their hinge-on-bolt and full-width-gusset approaches; nothing was copied.

1. **Pad end at the wall, radar moved under the beam.** On the device the radar looks along the rod's +x end; at the wall's inside face that is toward the door, away from the approach, and turned round it looks into the beam. So the fork gets screw holes and goes on the beam's underside looking out and down, with the same cradle. Cost: a longer radar lead (about 350 mm) and two more #4 screws.
2. **Rigid braces, not hinge and chain.** The braces are compression props, PLA's strong case; nothing swings, creeps or needs levelling; one part instead of a plate, a hinged shelf, two pins and two ties. The hinge form would be the same shelf split from the plate at the top corner, knuckles on M3 pins, two cord eyes on the shelf's outer edge. It is not built.
3. **Bolt on, no bracket reprint.** The device bolts up into the shelf through its own six ceiling holes; the bracket is untouched. The fairlead's two flat heads sit under the solid shelf.
4. **Where the line falls: 74 mm from the beam's face**, fixed by the geometry (6 mm gap, 5 mm plate). To move it out, raise `WALL_GAP` in `cad/wall_mount.py`; each millimeter of gap moves the line one millimeter and adds a millimeter of lever arm.
5. **Print orientation: shelf top on the bed, plate and braces standing.** The prior-art advice to print an L on its side does not apply: the second brace would hang over air. The nut pockets on the bed side use the finger's stepped bridging.

## Rulings owed from the owner

1. **Rigid braces (built) or hinge and chain (not built).** Advise: rigid. Yes or no?
2. **Radar under the beam on the screw-on fork.** Advise: yes. Yes or no?
3. **Line 74 mm from the beam's face.** Advise: accept; walk under it after the print before moving it. Yes or no?
4. **Print `wall_mount.stl`** (212 cm3, roughly 150 g of PLA at the doc 01 settings; hours, not measured). Advise: print only after rulings 1 and 2. Yes or no?

## What the next session does after the rulings

- Ruling 1 "hinge": build the hinged variant in `cad/wall_mount.py` as two parts (`wall_plate`, `shelf_hinged`) with knuckles on M3 pins (hole drawn 3.5, a free pin per the fit numbers), two cord eyes, the same checks, and the fold-flat pose clash-checked.
- Ruling 4 "print": the owner prints both parts; then V18 in `08_open_items.md`: nuts tapped in, device bolted on at the bench, a 5 kg pull on the assembled mount before it goes overhead; note any fit that is off by the usual 0.1 to 0.3 mm and adjust the drawn size in code.
- Either way: the ceiling install in doc 06 stays the default. Nothing about the device, the firmware or tasks 1 to 3 changes.

## Constraints that still bind

- CLAUDE.md hard constraints (motor-led drop, the 6 lb line must stretch, no braid without the elastic snubber).
- Existing hardware only: M3 x 10 to 12 bolts and nuts, #4 x 1 in wood screws (already on the BOM for the ceiling), the radar's existing M3 pivot bolt. Nothing new to buy for the wall install beyond the screws.
- The bracket is printed and final; the mount bolts to it.
- No glue: the nuts tap into their pockets, the fork screws to the beam.
- Expensive-work rule: the rebuild is cheap and allowed; a print is the owner's call.
