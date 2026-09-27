# 06 - Installation under the porch

![Install](img/install.png)

## Where it goes

Porch measured by the owner 2026-09-26: ceiling 8 ft, front beam hangs 10 in below it, device 12 in behind the beam.

- **On the porch ceiling, behind the front beam.** People walk in from outside, under the beam.
- Spider line (the fairlead) **305 mm (12 in) behind the beam's back face**, centred on the walkway.
- Rod axis parallel to the beam. **Servo end, with the radar, toward the beam**; the fairlead end away from it.
- The device hangs about 112 mm below the ceiling at its lowest point (the limit switch). Retracted, the spider's bottom sits about 215 mm below the ceiling, above the beam's bottom edge (254 mm below the ceiling), so the beam hides it until the person is close.
- **Radar tilt 50 degrees down** for this porch. The beam blocks every radar ray shallower than about 45 degrees down; at 50 the middle of the radar's beam passes under it. Worked out from the measurements (drawn in the picture): legs visible from about 1.7 m outside the beam, chest from about 0.8 m. Not yet walk-tested (test S3). Radar partly sees through wood too; the walk test settles it.

## Heights (8 ft porch ceiling, beam 10 in deep)

| Point | Height |
|---|---|
| Porch ceiling | 2440 mm (96 in) |
| Bottom of the front beam | 2184 mm (86 in) |
| Spider, retracted | bottom of spider about 2230 mm, hidden above the beam's bottom edge |
| Spider at rest after the drop | 1550 mm (61 in): face height for teens and adults, above small children |
| Lowest point if the motor loses grip and the line's stretch catches it | about 1450 mm (57 in) |

Line length to set (barrel knot to bead) = (ceiling - 85 mm) - (target rest height + spider height + 30 mm for bead and swivel) + 45 mm.
The 85 mm is where the bead sits against the flap at home; the 45 mm is line between the spool and the flap.
For the table above with a 100 mm spider: 2355 - 1680 + 45 = 720 mm. Tie it at 720, enter `line 720`, then shorten on site until the resting height is right.

## Fastening

- 4 screws: the 2 holes at the servo end and the 2 pad holes at x = -56 (the middle pair).
- Into a joist: #4 x 1 in pan-head wood screws.
- Into drywall only: #4 screws in ribbed plastic anchors, or small toggle anchors. With 6 lb mono the peak pull is about 12 N (1.2 kg) and can never pass about 27 N, where the line snaps. Never hang it on braid without an elastic snubber.
- The ceiling face must be flat against the base; nothing may stick out of the ceiling side (this is why the fairlead's two screws are countersunk flush).

## Alternative: hanging from the beam's inside face (wall install, draft)

![Wall install](img/wall_install.png)

The owner's plan (2026-09-27): keep the printed bracket, hinge its pad end to a plate on the beam, a bar at 45 degrees between the far ends of the two plates at each side. Five small flat prints, M3 pins, wood screws. Designed and CAD-checked the same day, **not yet printed or hung** (open item V18). Source `cad/wall_hinge.py`; run it for the report.

**Parts (69 cm3 of PLA in all).**

| Part | Print | What it is |
|---|---|---|
| `hinge_plate.stl` | 1, 29 cm3 | A frame screwed to the beam's inside face: a top rail carrying the two hinge forks, two legs hanging down the beam with a fork at the bottom of each for the bars. One #4 x 1 in screw at each leg corner |
| `hinge_clip.stl` | 2, 2 cm3 each | Each bolts on top of the pad through the x -80 and x -56 holes of one row (2x M3, nuts under the pad; the controller board then sits on foam tape) and carries a knuckle past the pad's edge. Hinge pin: M3 x 25 through fork, knuckle, fork, with a nut |
| `tie_bar.stl` | 1, 12 cm3 | The second plate: a strip on top of the device's far edge, 2x M3 through the base's x 65 holes (nut under the base; at z 20 the nut touches the servo tower's face by under 1 mm, so put the nut on top there and the head below, or file one flat). A lug hangs under each end, past the device |
| `strut.stl` | 2, 12 cm3 each | The bar at 40 degrees with an eye at each end: M3 x 20 pin into the leg's bottom fork, M3 x 20 pin into the tie bar's lug. It sits outside the device, past the motor at one end and past the bearing plate at the other |

**Why the bar is a printed bar and not chain.** The hinge is at the top and the plate hangs down the beam, so the device's weight tries to fold the hinge shut and the bar between the plates' far ends is pushed, not pulled. Chain or cord goes slack under a push. The bar takes 4 N standing and 20 N if the line snaps, across both; one 7 x 8 mm PLA bar buckles at about 160 N.

| Point | Wall install (draft) |
|---|---|
| Line (the fairlead) | 77 mm from the beam's face (ceiling install: 305 mm) |
| Device top | 8 mm below the ceiling (the hinge knuckle needs the room) |
| Spider retracted, bottom | spider height + 123 mm below the ceiling; hidden behind a 254 mm beam up to a 130 mm spider |
| Line length | the ceiling-install formula with (ceiling - 8) for the ceiling height |

**Radar.** On the device it looks toward the door, away from people walking in. Either accept a late trigger for the first walk test, or screw `ld2450_fork_screw.stl` (the fork with a 44 mm plate and two #4 holes, `cad/wall_mount.py`) up into the beam's underside and put the cradle on it looking out and down; the lead then runs up the beam's face (about 350 mm, BOM N10).

**Order.** Bench: clips on the pad, tie bar on the base. Ladder: plate to the beam with 4x #4 x 1 in (2 mm pilots), top rail against the ceiling, legs down; every screw has a straight screwdriver path along the rod direction, checked in the model. Hold the device hanging at about 45 degrees, drop its knuckles into the forks, push the two hinge pins through and nut them. Swing the far end up level, pin each strut top and bottom, tighten the hinge pins. Nothing is glued.

**Checked in the model.** All five parts watertight; plate, clips, tie bar and struts clear every device part and each other; all six pins pass through their holes; the device swings on the hinge clear of the plate from level down to 65 degrees (hang it at less than that); every print has under 200 mm2 of unsupported overhang. A one-piece braced shelf is in `cad/wall_mount.py` (212 cm3) if this draft flexes.

## Sensor

- Outdoors under a covered porch: keep the device and controller out of blowing rain; the LD2450 and the electronics are not waterproof.

- **LD2450** (primary): on the device, in its tilting cradle under the servo end (`ld2450_fork.stl` glued, `ld2450_cradle.stl` on one M3 bolt), looking out from under the porch toward people walking in, standing upright. Set the tilt on site, starting at 20 degrees down (doc 03). Nothing to mount on the wall.
- Its lead (4 wires, 1.25 mm plug at the sensor) runs about 10 cm across the device to the controller.
- Setup per `03_sensor.md`: no calibration needed; optional app check for firmware version and tracking; leave the app's zones off.
- LD2410C (fallback only): top center of the opening, hallway side, aimed about 45 degrees down; settings in `03_sensor.md`.

## Power

- 12 V adapter at the outlet, 5.5 x 2.1 mm DC extension cable up to the ceiling. Tape the cable along the door trim.

## Safety

- Soft foam spider only, 60 g maximum, no hard eyes or wire legs at face height. Legs wider than about 50 mm may touch the limit switch at the top; trim or angle them down.
- Keep the drop clear of stairs, and of the swing of the door itself.
- 6 lb monofilament only (or put the elastic snubber back). Check the knots, the bead, the flap, and the line for nicks before each night.
- `disarm` (or unplug) when small children are expected to run through.
