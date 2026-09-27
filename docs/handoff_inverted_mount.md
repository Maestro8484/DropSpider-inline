# Handoff: inverted device on metal corner braces (owner's redesign, 2026-09-27)

![Inverted install mockup](img/inverted_install.png)

## Where it stands: mockup sent, waiting on the owner

Steps 1 and 2 below are done (2026-09-27). `python inverted.py` passes every check: block watertight, mounting face one plane at y 0, no clashes (braces included), line path clear through the base hole, bore and flap slot, spool clearance 0, hard stop 14.75 degrees, roller push 4.33 (needs 3.4), both screw heads clear. Two fixes were needed: the braces became 6 in stand-ins at z 8 and z 106 with no holes, and the fairlead block was trimmed to z 24 to 93 (far rib dropped) to clear them; the face check was rewritten because it wrongly counted the block's own inner steps as mounting faces. `render.inverted_png()` makes the picture above. The full rebuild (`tools\regen_cad.ps1`) was not run: `generate.py` is untouched, and it rewrites every image while another session was live.

Owed from the owner: approve the mockup (then step 3), and say where along the base the two braces go (drawn at the ends, z 8 and z 106; the 106 one hangs 8 mm past the base's end).

## First job: the mockup, for the owner to check

The owner ruled 2026-09-27: build the inverted layout (yes), he has the corner braces (yes), and he wants an accurate mockup picture first, before any doc work. Do this, in order:

1. `cd cad; python inverted.py`. Fix whatever fails until the report shows: block watertight, mounting face one plane, no CLASH lines, line path clear through base hole, bore and flap slot, spool 2 mm clearance 0, hard stop near 14.75 degrees with roller push at least 3.4, both screw heads clear.
2. Add `inverted_png()` to `cad/render.py`: `assembly_inverted()` plus `porch()`, drawn through `view_inv()` (floor down), a line and bead from `line_and_bead()`, viewed from below inside the porch like `wall_install.png`. Save as `docs/img/inverted_install.png`. Look at it. Put it at the top of this file and send it to the owner. Stop there until he answers.
3. Only after he approves: docs 06 (the wall install becomes this), 09 (block under the base, same flap and switch), 01 (line exits the servo side), 05, 08 (V10 and V18), BOM (braces), `cad/README.md`, and the drilled holes on a second footprint drawing (`footprint_svg.py` sectioning `bracket_inverted()`).

## Braces: 6 in steel L brackets, the owner's ruling 2026-09-27

His words: "i will manually edit the plate via drill or 3d model myself based on the 6inch braces". So the braces are 6 in by 6 in, 1 in wide, about 35 lb rated, and the bracket's bolt holes for them are HIS: he drills the base to the braces' own holes, or edits the model himself. The next session does not place the braces and does not drill holes for them in `bracket_inverted()`.

What the next session still does about them:

- Model the braces as 6 in stand-ins (`BRACE_LEG` 152, `BRACE_W` 25 in `cad/inverted.py`) at whatever z the owner says, and run the clash check against the fairlead block. A 6 in leg reaches from the beam to x +60 under the base; on the pad rows (z 28 and z 83) it runs through the block (x 19 to 36, z 20 to 99), so the braces go at the base's ends (about z 8 and z 106) unless he says otherwise. Ask him which z once, in the mockup message.
- Keep the fairlead block clear of the brace legs: its plate starts at z 24 and its far rib (z 93 to 99) comes off if the braces are at the ends. That is one edit in `fairlead_base()`.
- Leave the drilled holes for the braces out of `bracket_inverted()` and off the footprint drawing. Only the three holes the session owns go in: the line (5 mm at x 25, z 45) and the two block screws (x 32, z 28 and z 83). Any others are his.
- The vertical legs hang 152 mm down the beam, ending 222 mm below the ceiling, above the beam's bottom edge (254). Capacity is not a question: the device is about 1 lb and the line cannot pull more than 6 lb.

## Ground truth first

This file is a pointer, not a record of truth. The local repo wins. If anything here disagrees with a file, the file is right and this handoff is stale: say so out loud.

```
git log -1 --oneline                                     # where the repo is now
git log -1 --oneline -- docs/handoff_inverted_mount.md   # when this handoff was last true
```

## The owner's words

"all the stress - 'pulling' or tension - is being applied to the 3d print design. Why not invert this entirely - having the tension when line is retracted rapidly from below be inverted by flipping the input/output of string 180 degrees, inverting it so the stress is moreso compaction against the 3d print model - have the string/line exit the 'bottom' of the bracket, the fairlead and all other objects re-oriented 180 degrees so that all the points of potential stress occur from below the bracket and device - not from technically the 'top' of the 3d print model device. This way I can just use some l-shaped metal brackets secured to the very bottom face of the bracket, sidestepping the need to consider PLA 3d print model material weaknesses."

## What turning it over does, checked in the model 2026-09-27

| Fact | How checked |
|---|---|
| Turned over (180 degrees about the rod), the base is at the bottom and the device's +y points up. The line that today leaves the barrel on the pad side (x -25) heading for the floor would then head for the ceiling | frame in `cad/generate.py`; a rotation about z reverses y |
| Same spool, same clutch direction, same ratchet, same finger, same winding sense: the line only has to peel off the OTHER side of the barrel, the servo side (x +25), and it then heads for the base, which is now the floor side. Nothing in the mechanism or the M1 and M2 logic changes | the wrap sense fixes the unwind direction; the two tangent points of one wrap sense are opposite sides of the barrel heading opposite ways |
| From the barrel at x 25 straight to the base, at any z across the barrel (42.5 to 47.5), the line touches nothing but the barrel it leaves and the base plate it must pass through | probe in this session: 0.8 mm line cylinder against every part of `G.assembly()` |
| A 5 mm hole through the base at x 25, z 45 removes 78 mm3, the 4 mm plate only: no gusset, tower or ledge there. The owner drills it; the base is printed | same probe against `bracket()` |
| Nothing of the device sticks out past the base's outer face, so a fairlead block under the base has clear room | lowest point over the whole assembly is y 0.0 |
| The finger, ledge, tower, servo and radar cradle all keep their places; the finger's lock is a tooth pushing it onto the ledge, not gravity | `cad/generate.py` `finger()`, doc 01 lock section |
| Loads after the flip: the device's weight and the line's pull (12 N normal peak, 27 N if the line snaps) press the spool down through the rod and the two plates INTO the base, and the base sits ON the braces' horizontal legs. The only PLA in bending is the base plate itself between the braces and the far end, printed flat so the bending is in its strong direction: about 8 MPa at a 27 N snap 70 mm out, margin 6 on in-plane PLA | arithmetic: 110 wide x 4 thick plate, moment 4.7 N x 89 + 27 N x 70 |
| Two steel corner braces (1.5 or 2 in) bolted through the pad's holes at x -80 and x -56 (z 28 and 83), vertical legs screwed to the beam: the beam's top screws see about 60 N each on a snap, a #6 in wood holds several hundred | arithmetic, moment over the brace leg height |
| The device's top (the far edge of the plates, 62 mm above the base) sits about 8 mm under the ceiling if the base is 70 mm below it; the line falls at x 25, which puts it 113 mm from the beam's face when the pad end is at the beam | envelope from `G.assembly()`: pad edge x -88, line x 25 |

## What has to change (the build list)

1. **Fairlead, flap and limit switch move under the base.** Today's unit (`cad/fairlead.py`, doc 09) is a rail on the pad reaching down beside the spool. Turned over, that spot faces the ceiling and the line is on the other side. New part `fairlead_base`: a block on the base's outer face at x 25, z 45 with the same flared bore, the same hinged flap and the same KW12-3 switch, screwed through two more drilled holes. Flap geometry, hinge pin and switch slots copy from `fairlead.py`; only the body is new. The bead, swivel and stop logic (V14) are unchanged.
2. **One drilled hole in the base**, 5 mm at x 25, z 45, plus the two for the fairlead block. Positions go on `cad/bracket_footprint.svg`.
3. **Radar.** The cradle tilts toward the device's +y, which is now up. Put the fork on the base's outer face instead (same fork, screwed through two more holes, or the screw-hole version `ld2450_fork_screw` from `cad/wall_mount.py`), looking along +x and down; or under the beam as before. Owner's call after the first walk test.
4. **Mount: two steel corner braces**, no printed part. Bolted through the pad's x -80 and x -56 holes (M3; the braces' holes are usually 4 to 5 mm, a washer covers it), vertical legs screwed to the beam with #6 x 1 in. The pad end at the beam. If the far end sags, a third brace on the servo end's x 65 holes to a strap up to the ceiling; the numbers say it will not.
5. **Docs**: 06 (the wall install becomes this), 09 (fairlead under the base), 01 (line exit side, direction rules re-read for the flip), 05, 08 (V10 and V18), BOM (braces, screws). The ceiling install stays the default until this is proven.
6. **Checks to add in `generate.py`**: an `assembly_inverted()` layout with the line path from the barrel's +x tangent through the base hole to the flap, the fairlead block clash-checked against every part, the flap travel and switch push copied from `fairlead.py`, and the 2 mm spool clearance against the block.

## What it does NOT change

The mechanism, the firmware, the motor-led drop, the 6 lb line rule, the spool, the ratchet, the finger, the servo, the hard constraints in CLAUDE.md. The bracket is not reprinted: three to five holes are drilled in it.

## Prior art, doorway droppers (web search 2026-09-27, 8 verified hits)

The field: haunters call these drop props or droppers (spider dropper, bat dropper); the overhead box is a drop mech in the pneumatic trade and a prop dropper in the Arduino trade. No published unit matches this project's box, fairlead and rewind-to-home design closely enough to copy. Two are worth borrowing from, and both agree with the inversion: the line leaves through the BOTTOM of the housing, centered under the spool.

| Name | License, date | Mounted | Line exit | Stop | Call |
|---|---|---|---|---|---|
| Motion Activated Dropping Spider, PaulMakesThings, Instructables | CC BY-NC-SA, 2010 | cardboard box over a door or hung from the ceiling | hole in the box bottom, centered under the spool: "centering between the walls of the spool is crucial, string may hop the spool when it retracts" | none, rubber band rewind | borrow: bottom-center exit |
| Sensing spider prank, jasonwinfieldnz, hackaday.io 187725 | not stated, 2022 | printed chassis screwed to the roof | hole in the chassis base under the spool, through a hinged paddle | KW11-3Z microswitch on the paddle, spider hits it on rewind | borrow: same idea as our flap and KW12-3, cruder |
| Motion Activated Halloween Spider, StumpChunkman, Instructables | CC BY-NC-SA, 2008 | card box taped above a door | hole for the motor, line off a sewing bobbin | timed | ignore |
| Halloween Dropping Spider, noelportugal, Instructables | CC BY-NC-SA, 2009 | not documented | VHS reel freed by a servo | none | ignore |
| Prop Dropper 2, Chris Savage, Nuts and Volts 2014 | CC BY, 2014 | plywood board on a ladder | tipped spool free-spools | none | ignore |
| FrightProps Spider Drop Prop and Drop Mech | commercial | steel frame bolted to a flat surface | rope off a cylinder arm | cylinder stroke | ignore: pneumatic, $400 to $530 |
| Spirit Halloween Dropping Mechanism | commercial | velcro strap round a beam | not shown | IR trigger | ignore: no details published |

Numbers: drops 2 ft to 15 ft; spools from a sewing bobbin to a 3 in jar lid; only one DIY unit has a stop sensor (a microswitch on a paddle at the exit hole, which is what V10 already is). Not reachable: Hackster (403), the haunter forums (paywall), Thingiverse and Printables searches return spiders and webs, no motorized dropper with a housing.
