# 01 - Mechanical design: Mechanism A, In-Line Single-Axle Clutch Spool (ISCS), Rev C

Status: **released for build**. Owner: lead mechanical engineer. Source of truth for geometry: `cad/generate.py`.

![Installed assembly](img/assembly_iso.png)

## What it does, in one paragraph

A foam spider hangs on braided fishing line wound on a spool. The spool sits on a one-way clutch bearing (HF0612) on a steel rod driven by a small stepper motor. A servo-held finger locks the spool at the top with zero power. On trigger, the finger swings out and the spool spins freely on the clutch: the spider free-falls. The motor never turns during the drop. After a short hang, the motor winds the spool back up through the clutch (which locks in that direction), the finger swings back into the ratchet teeth, and everything powers down.

## Why this layout (decisions already made, do not re-open without cause)

| Decision | Reason |
|---|---|
| Spool on a one-way clutch, motor never back-driven | A back-driven stepper brakes the fall with its detent (magnetic notchiness) and acts as a generator that can spike the 12 V line. The clutch removes both. |
| Everything on one rod ("in-line") | Strength and simplicity: no gears, belts, or offset shafts. One part to align. |
| Ratchet + servo finger for the hold | Zero power while armed, no hum, no heat. The load pushes the finger onto a printed ledge, not into the servo. |
| Stepper, not a DC gearmotor | Fixed step count per rewind, no encoder or limit switch needed. |
| Hard stop at the top = bead on the line against a printed eyelet | Rewind length varies by up to half a turn after each drop (see "End of drop"), so a counted stop alone is not reliable. |
| Spool split into two parts | Both print flat with zero supports; no support scars in the line channel. |

## Parts on the rod, motor to bearing (z = distance from the motor plate's outer face)

| z (mm) | Part | Notes |
|---|---|---|
| -32 to 0 | NEMA 11 motor | Mounted on the outside of the motor plate, 4x M2.5 |
| 10 to 30 | 5-to-6 mm rigid coupler | Motor shaft fills the 5 mm side. Blue Loctite on both set screws. |
| 20 to 120 | 6 mm hardened rod, 100 mm | Clamped in the coupler only; everything else slides on it |
| 30 to 36 | spacer_A_6mm | Sets the ratchet disk in the finger plane. Adjust with shims (see below). |
| 36 to 42 | spool_ratchet | 12 teeth, tip r 33, root r 29 |
| 40.5 to 50 | spool_body with HF0612 pressed in | Boss sits in the disk recess, 3x M3x8 screws from the motor side |
| 50 to 100 | spacer_B_50mm | |
| 100 to 106 | 606ZZ in the bearing plate | Supports the rod end |

**The one measurement that matters:** the ratchet disk must straddle the finger. Finger plane is z 36 to 39; disk is z 36 to 42. After the motor and coupler are on, measure from the motor plate's outer face to the coupler's free end. If it is not 30 mm, change spacer A by the difference using `shim_1mm` / `shim_2mm` (or reprint spacer A). The spool floats between spacer A and spacer B, so the stack must be snug, not tight.

## The lock (read this before touching the servo angles)

![Lock detail](img/lock_detail.png)

- Seen from the **606ZZ end**, the spool turns **clockwise** when the spider falls. Seen from the motor end on a ceiling (the picture), that is counterclockwise.
- The steep faces of the teeth block that direction. The tooth pushes the finger toward the ceiling, onto the **ledge** printed on the bracket. The ledge takes the load; the servo carries almost none.
- Finger locked = level, pointing at the rod (default servo 90). Released = swung toward the floor by 60 degrees (default servo 30). Both are set at commissioning.
- Lock sequence (firmware does this): motor holds the spool, finger goes in, motor turns off, the spider's weight rotates the spool back up to 1/12 turn until a tooth lands on the finger, servo lets go.
- The finger tip is tapered on the side that meets the ramp so it seats deep against the steep face.

## Direction rules (the only things that can be assembled backwards)

1. **Line exits on the electronics-pad side** of the spool and goes straight down through the eyelet. Wind it so pulling the line spins the spool clockwise seen from the 606ZZ end.
2. **HF0612 orientation:** with the spool on the rod and the rod held still, the spool must spin freely clockwise (seen from the 606ZZ end) and lock counterclockwise. If backwards, press the bearing out and flip it.
3. **Motor rewind direction:** set in firmware (`dir 0/1`), no rewiring.

## Line and hard stop

From the spool outward: **150 mm elastic snubber** (2 mm round elastic, tied to the barrel, wound on first) -> 20 lb braided line -> through the eyelet -> **8 mm hard plastic bead** (the stop, too big to pass the 3.2 mm eyelet) -> small barrel swivel (stops the spider spinning the line into twists) -> spider.

The snubber lives at the spool end on purpose. At the spider end it would hang 150 mm below the device when retracted and show under the door head. At the spool end it is wound up out of sight and only pays out at the very bottom of the drop. The elastic-to-braid knot must pass the eyelet: use a small double uni knot and trim tight.

## End of drop and why the snubber is mandatory

The spool is free, so nothing stops the spider until the line runs out. At that moment the knot swings to the bottom of the barrel and the pull goes straight into the rod. Without give in the line, a 100 g spider falling 0.7 m produces a shock of order 100 N or more, enough to snap the knot, the PLA, or the ceiling anchors. A 150 mm elastic snubber stretches the stop over 100 mm or more and cuts the peak to about 10 N. It also makes the spider bounce, which is the better scare.

The same swing means the knot can end up to half a turn either side of the bottom, which is why the rewind overshoots by 0.75 turn and relies on the bead stop.

## Materials and print settings

| File | Qty | Orientation | Infill | Walls | Supports | Brim |
|---|---|---|---|---|---|---|
| spool_body.stl | 1 | as exported, flange down | gyroid 40% | 4 | none | none |
| spool_ratchet.stl | 1 | as exported | gyroid 40% | 4 | none | none |
| bracket.stl | 1 | base down | gyroid 40% | 4 | tree, **not** build-plate-only | none |
| line_guide.stl | 1 | as exported (flat) | gyroid 40% | 4 | none | none |
| finger.stl | 3 | flat | rectilinear 100% | - | none | 5 mm, 0.1 gap |
| spacer_A_6mm.stl, spacer_B_50mm.stl | 1 each | on end | rectilinear 100% | - | none | 5 mm, 0.1 gap |
| shim_1mm.stl, shim_2mm.stl | 2 each | flat | rectilinear 100% | - | none | none |

PLA for everything. Print the finger in PETG if any is loaded; PLA fingers are consumables, keep spares. 5 top and bottom layers.

## Press fits and fasteners

- HF0612 into spool body: 9.9 mm bore for a 10.0 mm bearing. Press in with a vise or clamp. Too tight: warm the hub with a hair dryer. Too loose: one drop of CA on the outside. Never glue near the rollers.
- 606ZZ into bracket: 16.8 mm for 17.0 mm. Same method.
- Spool disk to body: 3x M3x8 self-tapping into 2.5 mm holes.
- Line guide to pad: **glue** (CA with accelerator, or 5-minute epoxy) over the whole rail. Push two M3 screws through the rail and the x = -32 pad holes as alignment pins while it cures, then remove them. Screws cannot stay: a head or nut on the ceiling side would hold the bracket off the ceiling. The guide only ever sees the bead stop load, about 2 N.
- Motor: 4x M2.5x6.
- SG90: its own two tab screws.

## Limits of this revision

- Ceiling mount only. Wall mount changes where the line exits and the guide does not fit.
- Spider: soft foam, 150 g maximum, nothing hard or pointed.
- Drop length set by line length, about 0.5 to 1.2 m.
