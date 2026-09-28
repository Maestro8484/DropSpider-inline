# 09 - Fairlead and limit switch (Rev C.1)

Replaces `line_guide.stl`. The bracket is unchanged and reused. Closes open item V10 (switch mount).
Source: `cad/fairlead.py`, pulled into `cad/generate.py`. Regenerate STLs and images with `tools\regen_cad.ps1`.

![Spider away](img/fairlead_rest.png)
![Spider home](img/fairlead_home.png)
![Sub-assembly](img/fairlead_exploded.png)

**Quantity: one fairlead body and one flap per build** (print a spare flap if you like).

## What it is

| Part | Job |
|---|---|
| `fairlead_body.stl` | Screws to the pad in the old line guide's spot (2x M3 countersunk from the ceiling side). Holds the fairlead, the hinge, the hard stop, the rest stop, and the switch plate |
| Fairlead (in the body) | Smooth, flared bore the line runs through: 9 mm wide at the top (spool side), 3.2 mm at the narrowest, 6 mm at the bottom. No sharp edges for the line to saw on. Centered on the spool's line channel |
| `fairlead_flap.stl` | Hinged bumper below the fairlead. The line passes loosely through an open slot, so it can be slipped in after the bead and swivel are tied. The prong on the switch side of the slot is 3.8 mm wide (was 1.2, too thin, owner 2026-09-27) |
| KW12-3 roller switch | Screws to the switch plate. Its roller rests just under the flap's tail |
| Hinge pin | M2 bolt, 16 to 20 mm: free in the flap, threads itself into the body |

## How it works

1. Spider away: the flap hangs level on its rest stop. The switch is open.
2. Rewind: the 8 mm stop bead rises and lifts the flap's free end. The flap pivots; its tail swings down onto the switch roller.
3. The switch clicks after about 2.3 mm of bead travel (2.6 mm at the roller). The firmware stops the motor.
4. If the motor keeps pulling, the flap lands flat against the fairlead's underside (the hard stop) after 3.3 mm of bead travel. The motor's pull goes into that face, not into the switch or the hinge pin.
5. Spider drops: gravity and the switch spring return the flap to its rest stop.

Measured in CAD: hard stop at 14.75 degrees; roller pushed 4.3 mm at the stop, 0.3 mm gap at rest, so about 4.0 mm of actual push against the switch's 2.6 mm to click plus 0.8 mm minimum overtravel. No collisions with the spool, bracket, servo or motor; 2 mm clearance to the spinning spool.

## Print

| File | Orientation | Settings |
|---|---|---|
| fairlead_body.stl | as exported (flat side down, 17 mm tall) | PLA, 4 walls, 40% gyroid, **no supports** (the bore and slots bridge) |
| fairlead_flap.stl | as exported (flat side down) | PLA or PETG, 4 walls, 100% rectilinear, brim 5 mm |

One flap is needed; a second is a spare.

## Assemble

1. Clean the fairlead bore with a 3 mm drill turned by hand. Run a scrap of the line through it; it must slide without catching. Sand the top flare smooth if it feels rough.
2. Fit the switch to the plate: **roller end toward the fairlead** (toward the spool), body on the side away from the plate's flat back. Two M2 screws through the plate's slots and the switch, nuts on the switch side. Leave them finger-tight.
3. Push the flap's knuckle into the gap below the fairlead and line up the holes. Drive an M2 bolt (16 to 20 mm) in from the flap's outer side: free through the flap (2.5 mm hole; drill it by hand if it drags), threading itself into the body. Stop before the head clamps the flap; it must swing down under its own weight.
4. Flap level on its rest stop: slide the switch up in its slots until the roller just touches the flap tail, then back it off about 0.3 mm (a piece of paper's thickness). Tighten.
5. Check by hand: lift the flap's free end. Click at about 2 mm; flap stops flat against the fairlead a moment later. Let go: it drops back, switch opens.
6. Screw the body to the pad: 2x **M3 countersunk (flat-head) screws, 8 to 10 mm**, put in from the ceiling side down through the x = -32 pad holes, heads flush with the ceiling face, cutting their own thread into the fairlead's rail (2.5 mm pilots). No glue (owner 2026-09-26). The pad holes need a 90 degree countersink so the heads sit flush: new bracket prints have it; on an already printed bracket, twist an 8 mm drill bit by hand in each of the two holes from the ceiling side until a screw head sits flush or just below.
7. Thread the line from the spool down through the fairlead, then slide it into the flap's slot from the free end. Bead, swivel, spider below as before.

## Inverted install: `fairlead_base.stl`

For the inverted install (doc 06), the same fairlead, stops and switch plate come as one block that screws under the base at the line hole. Source `fairlead_base()` in `cad/inverted.py`: doc 09's geometry turned 180 degrees and moved to the base's outer face, so the flap, hinge, switch slots and the numbers above are unchanged. Checked in the model 2026-09-27: watertight, clear of every part, line path clear through the base hole, the bore and the flap slot, hard stop at 14.75 degrees, roller pushed 4.33 mm (needs 3.4), 2 mm clear of the spool. Its far rib is left off so the owner's braces fit at the base's ends, and a small boss under the z 28 screw gives that screw 11 mm of thread (without it, only the 4 mm plate).

| Step | What to do |
|---|---|
| Print | `fairlead_base.stl` as exported, 17 mm tall, same settings as `fairlead_body.stl` (68 mm2 of overhang, no supports) |
| Drill | the base: 7 mm at x 25, z 45 (the line), 3.4 mm at x 32, z 28 and z 83 (drawing `cad/bracket_footprint_inverted.svg`, 1:1). Sand the 7 mm hole's edges smooth: the line runs through it |
| Flap and switch | Assembly steps 1 to 5 above, unchanged |
| Screw on | 2x **M3 x 12** from inside the base (heads on the device side), cutting their own thread into the block's 2.5 mm pilots. The block's flat face against the base's outer face |
| Line | From the spool's servo side down through the base hole, the bore, then the flap's slot |

## Wiring

Bare KW12-3, three legs: COM to GND, NO to GPIO32, NC unused. Firmware pull-up: open = HIGH, pressed = LOW. Check with the web page; `liminv` if backwards.

## Known effects on other items

- **V14, answered by the geometry:** after the lock seat move lets the spool down up to 1/12 turn (about 13 mm of line), the bead drops off the flap and the switch reads **open** at rest. The firmware must not treat "open at rest" as "spider not home". Suggested rule: the last cycle ended with a switch stop, then a seat move, then idle = home.
- Ceiling install: the device now hangs about 36 mm lower (switch at y 112 vs old guide at y 76). Still hidden above the door head per doc 06 at 8 ft ceilings.
- Spider legs wider than about 50 mm may touch the switch at the top. Trim legs or angle them down.

## Unverified

- The KW12-3's operating point is taken from the owner's datasheet (2.6 mm pre-travel, 0.8 mm overtravel, 0.7 N). The slotted holes cover about plus or minus 2.5 mm of error.
- The M2 hinge bolt loosening over a season: a drop of threadlocker or CA on its thread in the body.
- Line wear in the PLA fairlead. Swap for a new print if a groove appears.
