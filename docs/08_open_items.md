# 08 - Open items, risks, verification status

What is proven, what is not, and what could stop the build. Evidence for every closed item is in `commissioning_log.md`.

## Risk raised by the software/electrical team, for the mechanical owner

| ID | Item | Why it matters | How to settle it |
|---|---|---|---|
| M1 | A one-way clutch can only let the spool spin free in the same direction the motor drives it | The motor has to drive the spool in the wind-up direction. The spider falls in the opposite direction. A one-way bearing locks in one relative direction and slips in the other, so the direction the motor can drive is exactly the direction the spool can NOT free-spin with the rod still. Same as a bicycle: the pedals drive the wheel forward and the wheel coasts forward, but push the bike backward and the pedals turn. Read that way, either the spool free-falls (commissioning step 7 passes) and then the motor cannot wind it up in either `dir` (step 8 fails both ways), or the motor winds it up and the drop back-drives the motor, which the hard constraints forbid. Reasoned from doc 01, **not tested on hardware** | One minute by hand once the spool is on the rod: hold the rod still and find the direction the spool spins free (the drop direction). Then hold the spool still and turn the rod the other way (the wind-up direction). If the rod slips there too, the clutch cannot wind the spool and doc 01 needs the mechanical owner |

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
| V1 | ESP32 3.3 V signals drive the carrier's 5 V driver logic | commissioning step 4 | 74AHCT125 buffer |
| V2 | Servo angle direction (release = smaller angle) | step 5 | swap `setlock`/`setrel` values |
| V3 | HF0612 press fit in PLA holds without creeping | step 11, then after 20 cycles | CA on the outer ring |
| V4 | Snubber stiffness: 150 mm of 2 mm elastic stops a 100 g spider in about 150 mm | step 7 | double the elastic, or shorten it |
| V5 | Motor skipping at the bead stop is short and harmless | step 9 | lower `rpm`, trim overshoot in `config.h`. With the limit switch on, the motor stops at the switch and should not skip at all |
| V6 | Finger lifetime in PLA | step 14 | PETG finger |
| V7 | LD2410C range and through-wall behavior in this house | step 12 | tune gates; AM312 fallback |
| V9 | Limit switch reads right and stops the rewind at the bead | steps 3b and 9 | `liminv`; move the switch; route its lead away from the motor wires |
| V10 | Limit switch mount at the eyelet | not in `cad/generate.py`. Geometry changes need the owner's approval | temporary mount (tape or a clip) for the bench; a printed mount is a Rev D item |
| V11 | Board joins the home network, page loads, network update works | step 3a, then one `tools\flash_ota.bat` | USB console `wifi`; own network DropSpider-setup at 192.168.4.1 |
| V12 | Board on COM13 is the 38-pin ESP32-S NodeMCU (ESP32, 4 MB flash) | chip read by esptool during the first USB flash | it would not enter flash mode on its own on 2026-09-24; hold BOOT, tap EN, let go of BOOT |

## Closed

| ID | Item | Result |
|---|---|---|
| V8 | Firmware on PlatformIO's current esp32 core (3.x) | Closed by pinning, not by testing 3.x: `platform = espressif32@6.7.0` (Arduino core 2.0.16) builds clean, 2026-09-24. Moving to core 3.x is a deliberate future change, not an accident of a fresh install |

## Known limits of Rev C

- Ceiling mount only.
- No stall sensing; the carrier hides the TMC2209 UART pin.
- Static IP address not set yet; DHCP only.
- One shared update password, from `secrets.ini`. Fine on a home network.

## Done in firmware since the handoff

- Rewind no longer blocks the console: the machine runs on its own task and FastAccelStepper makes the step pulses.
- Web page (console, bench controls, settings, network setup), network firmware updates, limit switch hard cut-off, three-strike fault stop.

## Candidate Rev D items (not started)

- Wall-mount variant with a relocated line guide.
- Radar distance read over UART instead of the OUT pin, for a tighter trigger window.
- Enclosure for the controller board.
- Printed limit switch mount at the eyelet (V10).
