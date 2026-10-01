# 06 - Installation under the porch

![Install](img/install.png)

## Where it goes

Porch measured by the owner 2026-09-26: ceiling 8 ft, front beam hangs 10 in below it, device 12 in behind the beam.

- **On the porch ceiling, behind the front beam.** People walk in from outside, under the beam.
- Spider line (the fairlead) **305 mm (12 in) behind the beam's back face**, centred on the walkway.
- Rod axis parallel to the beam. **Servo end, with the radar, toward the beam**; the fairlead end away from it.
- The device hangs about 112 mm below the ceiling at its lowest point (the limit switch). Retracted, the spider's bottom sits about 215 mm below the ceiling, above the beam's bottom edge (254 mm below the ceiling), so the beam hides it until the person is close.
- **Radar tilt 50 degrees down** for this porch. The beam blocks every radar ray shallower than about 45 degrees down; at 50 the middle of the radar's beam passes under it. Worked out from the measurements (drawn in the picture): legs visible from about 1.7 m outside the beam, chest from about 0.8 m. Not yet walk-tested (test S3). Radar partly sees through wood too; the walk test settles it. **Not through metal.** The radar sees through wood, drywall and plastic, but aluminum siding or trim coil blocks it completely, however thin (at 24 GHz the signal dies within about half a micron of aluminum; Hi-Link's manual and every install guide say metal blocks it). If the beam is clad in aluminum, the radar only sees people once they are in view under the beam's bottom edge, and the flat metal can bounce the signal back as phantom targets or jumpy positions. Fix for either: tilt steeper, so less of the view lands on the beam.

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

## Alternative: turned over on the beam's inside face (inverted install)

![Inverted install](img/inverted_install.png)

The owner's plan, approved 2026-09-27: the device turned upside down, its flat base at the bottom, sitting on two steel corner braces screwed to the beam's inside face. The line leaves through a hole in the base. Every load (the device's weight, the line's pull) presses the printed parts down into the base and the base onto steel, instead of hanging the PLA from screws. CAD-checked, **not yet built or hung** (open item V18). Source `cad/inverted.py`; run it for the report.

**Turned end for end in the owner's build (photo 2026-10-01):** the **servo end** of the base sits at the beam, the pad (electronics) end away from it. The radar moves to the pad end so it still looks toward the beam. Everything below is for that build.

**What changes on the device.** Nothing in the mechanism or the firmware: same spool, clutch, ratchet, finger, servo, same winding sense, same `dir`. The line simply leaves the barrel on the servo side instead of the pad side (doc 01, direction rule 1).

| Part | What happens to it |
|---|---|
| Bracket | `bracket.stl` from 2026-09-28 has these five holes printed in (with the 17.0 606ZZ seat). On an older print, drill them through the base (drawing `cad/bracket_footprint_inverted.svg`, print it 1:1 as a template): **7 mm for the line** at x 25, z 45 (wider than the spool's 6 mm line channel, so the line never rubs a drilled edge; a 1/4 in bit is close enough); **3.4 mm x2 for the fairlead block** at x 32, z 28 and z 83; **3.4 mm x2 for the radar fork** at x -80, z 38.5 and z 72.5 (the pad end; drill these on every print, the printed holes at x 62 stay empty) |
| `fairlead_base.stl` (new, 18 cm3) | The fairlead, hard stop, rest stop and switch plate of doc 09 as one block under the base, at the line hole. Same flap (`fairlead_flap.stl`), same KW12-3, same hinge bolt. 2x M3 x 12 from inside the base (heads on the device side) into the block's 2.5 mm pilots. Replaces `fairlead_body.stl` for this install |
| Radar | Stays on the device, no glue: `ld2450_fork_screw.stl` (the fork with a longer plate and two holes; same ears, so the same cradle and radar) bolted under the base at the pad end with 2x M3 x 10, nuts inside, looking along the device toward the beam (where people come from) and down at 50 degrees. The nuts sit 8 mm from the base's end, under the board's edge: keep that strip clear or lift the board on 4 mm foam tape |
| Controller board | On the pad, the base's device side, now the end away from the beam, facing up. Room checked: a 52 x 75 x 30 mm box there clears every part |
| Braces | **The owner's:** two steel corner braces, 6 in legs. The flat leg under the base, the other leg standing up the beam's face beside the device's servo end. He places them and drills the base for their bolts himself. **Where a bolt can go**, checked in the model: the base only runs full width between x -24 and x 75, so at its two ends (z 0 to 18 and z 93 to 110) there is no pad and the flat legs carry the base from the servo end (x 75) to x -24; past that they run on under nothing to their tips at x -73. A bolt through the base is clear of everything inside between **x 24 and x 55** at either end, and at the motor end also between x -12 and x 12. Never between x -20 and x 20 at the 606ZZ end: the bearing plate stands there. The pad's own holes at x -80 and x -56 are not over the braces. Drawn in the model at z 8 and z 106, clear of the fairlead block; nearer the middle they hit it |

**Heights**, from the model, with 6 in braces standing up the beam with their tops about 8 mm under the ceiling:

| Point | Below the ceiling |
|---|---|
| Base (the device's bottom face) | 160 mm |
| Bead at home, against the flap | about 196 mm (fairlead v2, 2026-09-28; v1 179) |
| Spider retracted, bottom | 196 + 30 (bead and swivel) + spider height. Hidden behind the 254 mm beam only for a spider up to about 28 mm tall |
| Line | falls 54 mm from the beam's face (ceiling install: 305 mm). A spider wider than about 10 cm brushes the beam; the owner's is about 8 cm, so about 14 mm to spare while it hangs still (owner kept this layout 2026-10-01) |

Line length (barrel knot to bead) = (ceiling - 196) - (target rest height + spider height + 30) + 72. The 72 mm is line from the spool to the flap in this layout (fairlead v2, doc 09). Tie it, enter `line`, then shorten on site, as for the ceiling install.

**Radar view**, from the model: the device blocks none of the radar's field (60 degrees either side, 35 up and down); its centre line meets the beam's face plane 409 mm below the ceiling, under the beam's bottom edge (254). The beam does cut off the top of the field: anything shallower than about 19 degrees below level hits the beam, as in the ceiling install (doc 03). **Not through metal.** The radar sees through wood, drywall and plastic, but aluminum siding or trim coil blocks it completely, however thin (at 24 GHz the signal dies within about half a micron of aluminum; Hi-Link's manual and every install guide say metal blocks it). If the beam is clad in aluminum, the radar only sees people once they are in view under the beam's bottom edge, and the flat metal can bounce the signal back as phantom targets or jumpy positions. Fix for either: tilt steeper, so less of the view lands on the beam. Start the walk test at 50 degrees; if it fires late or fires on nothing, go to 55 or 60. The cradle clears every part from 20 to 90 degrees in this layout (checked in the model 2026-10-01). The radar hangs about 35 mm past the base's pad end. The spider, retracted or dropped, is inside its view: if the radar reports the spider as a person, the device would sit in "waiting for the doorway to clear" after each scare. Not checked; the first walk test (S3) shows it, and a steeper or shallower tilt moves the spider out of the middle of the view.

**Wires.** The switch and the radar now sit under the base and the board on top of it. Run both leads round the base's pad end (the servo end is against the beam) and back to the board: about 15 cm for the switch, about 10 cm for the radar (BOM N10 covers it). Tie them to the base so the spinning spool cannot catch them.

**Order.** Bench: drill the five holes, screw the fairlead block on (doc 09, inverted install), bolt the radar fork under the pad end, board on the pad, leads round the pad end, line threaded down through the base hole. Ladder: braces to the beam, device onto their flat legs, bolted through the owner's holes. Then `07_commissioning.md` as usual.

Retired 2026-09-28: the earlier hinge-and-strut wall draft and the braced shelf. Their code and STLs are in `cad/retired/`, their handoff and picture in `docs/retired/`. Do not print them.

## Sensor

- Outdoors under a covered porch: keep the device and controller out of blowing rain; the LD2450 and the electronics are not waterproof.

- **LD2450** (primary): on the device, in its tilting cradle under the servo end (`ld2450_fork_screw.stl` bolted with 2x M3, no glue; `ld2450_cradle.stl` on one M3 bolt), looking out from under the porch toward people walking in, standing upright. Set the tilt on site, starting at 20 degrees down (doc 03). Nothing to mount on the wall. Inverted install: the same parts bolted under the base's pad end, see above.
- Its lead (4 wires, 1.25 mm plug at the sensor) runs about 10 cm across the device to the controller (inverted install: about 10 cm, round the base's pad end).
- Setup per `03_sensor.md`: no calibration needed; optional app check for firmware version and tracking; leave the app's zones off.
- LD2410C (fallback only): top center of the opening, hallway side, aimed about 45 degrees down; settings in `03_sensor.md`.

## Power

- 12 V adapter at the outlet, 5.5 x 2.1 mm DC extension cable up to the ceiling. Tape the cable along the door trim.

## Safety

- Soft foam spider only, 60 g maximum, no hard eyes or wire legs at face height. Legs wider than about 50 mm may touch the limit switch at the top; trim or angle them down.
- Keep the drop clear of stairs, and of the swing of the door itself.
- 6 lb monofilament only (or put the elastic snubber back). Check the knots, the bead, the flap, and the line for nicks before each night.
- `disarm` (or unplug) when small children are expected to run through.
