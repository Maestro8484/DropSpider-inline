# 08 - Open items, risks, verification status

What is proven, what is not, and what could stop the build. Evidence for every closed item is in `commissioning_log.md`.

## Risk raised by the software/electrical team, for the mechanical owner

| ID | Item | Why it matters | How to settle it |
|---|---|---|---|
| M1 | **Confirmed, fixed on paper in Rev C.1, not yet tested.** Mechanical owner agrees: design error. Fix: HF0612 flipped, motor-led drop. See `M1_fix_handoff.md`. Original finding below. A one-way clutch can only let the spool spin free in the same direction the motor drives it | The motor has to drive the spool in the wind-up direction. The spider falls in the opposite direction. A one-way bearing locks in one relative direction and slips in the other, so the direction the motor can drive is exactly the direction the spool can NOT free-spin with the rod still. Same as a bicycle: the pedals drive the wheel forward and the wheel coasts forward, but push the bike backward and the pedals turn. Read that way, either the spool free-falls (commissioning step 7 passes) and then the motor cannot wind it up in either `dir` (step 8 fails both ways), or the motor winds it up and the drop back-drives the motor, which the hard constraints forbid. Reasoned from doc 01, **not tested on hardware** | One minute by hand once the spool is on the rod: hold the rod still and find the direction the spool spins free (the drop direction). Then hold the spool still and turn the rod the other way (the wind-up direction). If the rod slips there too, the clutch cannot wind the spool and doc 01 needs the mechanical owner |
| M2 | Finger cannot release while the spider hangs. Found by the mechanical owner during the M1 rework, **not tested** | The release swing drives the finger tip into the loaded tooth's steep face, so the servo fights the tooth | Rev C.1 release winds the spool CCW about 1/12 turn while the finger swings out. Test T3 in `M1_fix_handoff.md` |

## Verified (in the design package)

| Item | How |
|---|---|
| Every STL is watertight (printable solid) | `cad/generate.py` checks on export |
| No part collides with the spinning spool; 2 mm clearance all round | swept-clearance check in `generate.py` |
| Finger tip reaches inside the tooth root | `generate.py` prints tip position |
| Spool body and ratchet print with zero supports | flat faces down, no overhangs |
| Firmware compiles and links (46% flash, 17% RAM) | `pio run`, espressif32@6.7.0 (Arduino core 2.0.16), ESP32Servo 3.0.6, FastAccelStepper 0.33.14, 2026-09-24 |

## Not yet verified (hardware needed)

| ID | Item | Test | If it fails |
|---|---|---|---|
| V1 | ESP32 3.3 V signals drive the expansion board's 5 V driver logic | commissioning step 4 | 74AHCT125 buffer |
| V2 | Servo angle direction (release = smaller angle) | step 5 | swap `setlock`/`setrel` values |
| V3 | HF0612 press fit in PLA holds without creeping | step 11, then after 20 cycles | CA on the outer ring |
| V4 | Line stretch as the shock absorber (6 lb mono, owner 2026-09-26, elastic dropped): estimated 12 N peak for a 60 g spider if the motor loses grip; snaps at about 27 N. Not tested; a motor-fault drop is never forced on purpose | step 7 | if a knot ever parts, put 150 mm of 2 mm elastic back at the barrel |
| V5 | Motor skipping at the bead stop is short and harmless | step 9 | lower `rpm`, trim overshoot in `config.h`. With the limit switch on, the motor stops at the switch and should not skip at all |
| V6 | Finger lifetime in PLA | step 14 | PETG finger |
| V7 | LD2410C range and through-wall behavior in this house (fallback sensor only since Rev C.1) | step 12 with `sensor 2410` | tune gates; AM312 fallback |
| V9 | Limit switch reads right and stops the rewind at the bead | steps 3b and 9 | `liminv`; move the switch; route its lead away from the motor wires |
| V10 | Limit switch mount. **Designed in Rev C.1:** KW12-3 in the fairlead with a hinged flap (doc 09, `cad/fairlead.py`). CAD-checked: 4.0 mm roller push against 3.4 mm needed, hard stop takes the motor's pull. Not yet built | doc 09 assembly step 5 by hand, then commissioning step 9 | slide the switch in its slots; reprint the flap |
| V11 | Board joins the home network, page loads, network update works | step 3a, then one `scripts\update_firmware.bat` WiFi update | USB console `wifi`; own network DropSpider-setup at 192.168.4.1 |
| V13 | Top drop speed and stopping ability of the NEMA 11 at 12 V, 0.6 A, with the real spider (estimate: about 500 rpm, stops 60 g or less cleanly) | T4, T5, T7 in `M1_fix_handoff.md` | lower `droprpm` / `dropdec`; lighter spider |
| V14 | **Answered by the fairlead geometry:** after the lock seat the bead drops off the flap, so the switch reads OPEN at rest. Firmware must infer home from the last cycle (switch stop, then seat move), not from the boot reading | commissioning step 10; boot with the spider home | firmware rule, not hardware |
| V15 | LD2450 as the trigger: tracking through the door frame, speed sign, approach-only firing, arrival timing | S1 to S5 in `handoff_sensor_bearings.md` | widen or narrow `doorwidth`, tune `leadms`; `sensor 2410` fallback |
| V16 | Printed fits on the owner's printer after the fit-check fixes: finger on the spline (5.0 drawn), spacers, ratchet over the HF0612 stub, flap on the M2 bolt, cradle grooves | test fit at assembly | open the hole with a drill by hand; adjust the drawn size in code |
| V18 | Wall install draft (doc 06 alternative): `hinge_plate.stl`, 2x `hinge_clip.stl`, cords. CAD-checked 2026-09-27 (watertight, clears every part, pins line up, swings clear, cord pull 63 N on a line snap). **Not printed, not hung** | print, fit the clips, hang it on the bench from two screws in a board, pull 5 kg on the far end | shorten `PLATE_H` for a steeper cord, or the braced shelf in `cad/wall_mount.py` |
| V17 | The fitted SG90 is a 180 degree positioning servo, not a 360 continuous one (the owner's spare has no hard stop) | `servo 90`, `servo 30`, `servo 150`, no finger fitted: must move and hold | swap the servo |
| V18 | Finger height on the real spline: plate must cover the ratchet disk by at least 5 mm (spline tip measured about 2 mm short of the ledge) | look edge-on at assembly step 14 | spacer A and shims move the disk |
| V19 | Reinforced fairlead body strength and the flat switch face on a real print; switch mounts with no washers | assembly steps 15 to 15d | 6 walls on that part |
| V12 | Board on COM13 is an ESP32 with 4 MB flash. **Closed 2026-09-25:** first the 38-pin NodeMCU-32S, now the 30-pin DevKit V1 in use, both ESP32-D0WD-V3, 4 MB, read by esptool | chip read by esptool during the first USB flash | it would not enter flash mode on its own on 2026-09-24; hold BOOT, tap EN, let go of BOOT |

## Closed

| ID | Item | Result |
|---|---|---|
| V8 | Firmware on PlatformIO's current esp32 core (3.x) | Closed by pinning, not by testing 3.x: `platform = espressif32@6.7.0` (Arduino core 2.0.16) builds clean, 2026-09-24. Moving to core 3.x is a deliberate future change, not an accident of a fresh install |

## Known limits of Rev C.1

- Ceiling mount only.
- No stall sensing; the expansion board hides the TMC2209 UART pin.
- Static IP address not set yet; DHCP only.
- One shared update password, from `secrets.ini`. Fine on a home network.

## Done in firmware since the handoff

- Rewind no longer blocks the console: the machine runs on its own task and FastAccelStepper makes the step pulses.
- Web page (console, bench controls, settings, network setup), network firmware updates, limit switch hard cut-off, three-strike fault stop.

## Candidate Rev D items (not started)

- Wall-mount variant with a relocated fairlead.
- Enclosure for the controller board.
