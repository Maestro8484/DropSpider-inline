# 05 - Print and assembly

Time: about 5 h printing, 1 h assembly. Tools: small Phillips, 1.5 mm and 2 mm hex keys (coupler set screws), multimeter, vise or bar clamp, CA glue, blue threadlocker, hair dryer.

![Exploded](img/exploded.png)

## A. Print

All PLA except the finger (PETG if you have it). Settings table in `01_mechanical_design.md`. Print 3 fingers and both shims.

## B. Sub-assemble the spool

1. Press the **HF0612** into `spool_body` from the flange side. It ends up flush with the flange and sticking out about 2.5 mm on the boss side. That stub goes into the ratchet disk's center hole.
2. Check its direction now: push a spare piece of the 6 mm rod in, hold the rod, and spin the body. It must spin freely one way and lock the other. Mark the free direction on the flange with a marker.
3. Set `spool_ratchet` onto the boss, counterbored side facing away from the body. Drive **3x M3x8** into the body. Snug, do not strip.
4. Look at the spool from the **plain flange side** (this side will face the 606ZZ end). The free direction marked in step 2 must be **clockwise** from this side. If not, press the bearing out and flip it.
5. Tie **150 mm of 2 mm round elastic** to the barrel (pass it round the barrel between the flanges, overhand knot, CA on the knot). Tie the braid to the free end of the elastic with a small double uni knot, trimmed tight: it has to fit through the 3.2 mm eyelet.

## C. Frame and rod

![Step 1](img/step1.png)

6. Press the **606ZZ** into the end plate. Screw the **NEMA 11** to the outside of the motor plate, 4x M2.5x6, wires pointing toward the base.

![Step 2](img/step2.png)

7. Slide the **coupler** onto the motor shaft, 5 mm side, until the shaft stops. Blue threadlocker, tighten that set screw. Leave the 6 mm side loose.

![Step 3](img/step3.png)

8. Measure from the motor plate's outer face to the free end of the coupler. It should be 30 mm. If it is 29, add `shim_1mm` next to spacer A; if 28, `shim_2mm`; if more than 30, sand spacer A down by the difference.
9. Hold, in line inside the frame: spacer A (next to the coupler), the spool (ratchet disk toward the motor), spacer B.

![Step 4](img/step4.png)

10. Push the **6 mm rod** in from the outside of the 606ZZ plate: through the bearing, spacer B, spool (rotate the spool its free way as the rod enters the needles), spacer A, into the coupler until it bottoms. Blue threadlocker, tighten the 6 mm set screw.
11. Check: the spool spins freely by hand clockwise (from the 606ZZ end), and turning it counterclockwise turns the motor shaft. The stack is snug with no end play above 0.5 mm.

## D. Servo and finger

![Step 5](img/step5.png)

12. Drop the **SG90** into the tower pocket from the 606ZZ side, output spline toward the spool, wires out the far end. Two tab screws.
13. Power the servo (or do this at commissioning): send it to 90 degrees before fitting the horn.
14. Glue a **finger** onto the single-arm horn with CA, horn hub in the round recess. Press the horn on with the finger level and pointing at the rod, resting just above the ledge, tip in the teeth. Horn screw in.

![Lock detail](img/lock_detail.png)

## E. Line guide and line

![Step 6](img/step6.png)

15. Glue `line_guide` to the pad with CA or epoxy. Two M3 screws through the rail and the x = -32 holes as alignment pins while it cures, then take them out.
16. Wind the elastic, then the braid, onto the spool by turning it counterclockwise (seen from the 606ZZ end). The free end leaves the spool on the pad side; thread it through the eyelet.
17. Below the eyelet, in order: **8 mm bead** (slides on the braid), **barrel swivel** (tie the braid to it; the bead rests on it), **spider** tied to the swivel's other end.
18. Unwind fully and measure from the barrel knot to the bead, elastic included, unstretched. That is the `line` value for the firmware.

## F. Electronics

19. Set the buck to 5.0 V with the meter before connecting any loads.
20. Set the TMC2209 Vref to 0.85 V, motor unplugged. DIP switches all OFF.
21. Wire per `02_electrical.md`. Mount the controller board on the pad with foam tape or zip ties through the x = -80 holes. Keep the x = -56 holes and the two at the servo end clear: they are the ceiling screw holes.
22. Go to `07_commissioning.md` before mounting anything overhead.

## Base layout reference

![Base](img/base_layout.png)
