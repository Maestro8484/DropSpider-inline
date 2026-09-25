# 06 - Installation above a doorway

![Install](img/install.png)

## Where it goes

- **On the ceiling, on the room side** of the doorway the victims walk through.
- Line (the fairlead) **300 mm (12 in) in from the wall face**, centered on the door's width.
- Rod axis parallel to the wall, either direction. The fairlead side (electronics pad) should face the doorway so the controller sits closest to where the sensor lead comes from.
- The device hangs about 112 mm below the ceiling at its lowest point (the limit switch). Retracted, the spider's bottom sits about 215 mm below the ceiling, above the sight line under the door head. It stays hidden until the person is about 0.6 m from the wall.

## Heights (8 ft ceiling, 6 ft 8 in door; adjust for yours)

| Point | Height |
|---|---|
| Ceiling | 2440 mm (96 in) |
| Top of door opening | 2030 mm (80 in) |
| Spider, retracted | bottom of spider about 2230 mm |
| Spider at rest after the drop | 1550 mm (61 in): face height for teens and adults, above small children |
| Lowest point if the motor loses grip and the snubber catches | about 1450 mm (57 in) |

Line length to set (barrel knot to bead, elastic included) = (ceiling - 85 mm) - (target rest height + spider height + 30 mm for bead and swivel) + 45 mm.
The 85 mm is where the bead sits against the flap at home; the 45 mm is braid between the spool and the flap.
For the table above with a 100 mm spider: 2355 - 1680 + 45 = 720 mm. Tie it at 720, enter `line 720`, then shorten on site until the resting height is right.

## Fastening

- 4 screws: the 2 holes at the servo end and the 2 pad holes at x = -56 (the middle pair).
- Into a joist: #4 x 1 in pan-head wood screws.
- Into drywall only: #4 screws in ribbed plastic anchors, or small toggle anchors. With the snubber fitted, the peak pull is about 10 N (1 kg). Without the snubber, do not install.
- The ceiling face must be flat against the base; nothing may stick out of the ceiling side (this is why the fairlead body is glued).

## Sensor

- **LD2450** (primary): flat on the wall above the door, **hallway side**, facing straight out down the approach. Not tilted. Painter's tape or a small printed clip holds it.
- Its lead (4 wires, 1.25 mm plug at the sensor) runs over the head of the door to the controller.
- Setup per `03_sensor.md`: no calibration needed; optional app check for firmware version and tracking; leave the app's zones off.
- LD2410C (fallback only): top center of the opening, hallway side, aimed about 45 degrees down; settings in `03_sensor.md`.

## Power

- 12 V adapter at the outlet, 5.5 x 2.1 mm DC extension cable up to the ceiling. Tape the cable along the door trim.

## Safety

- Soft foam spider only, 60 g maximum, no hard eyes or wire legs at face height. Legs wider than about 50 mm may touch the limit switch at the top; trim or angle them down.
- Keep the drop clear of stairs, and of the swing of the door itself.
- Snubber on every time. Check the knot, the bead, the flap, and the snubber before each night.
- `disarm` (or unplug) when small children are expected to run through.
