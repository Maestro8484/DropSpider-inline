# 08 - Open items, risks, verification status

## Verified (in the design package)

| Item | How |
|---|---|
| Every STL is watertight (printable solid) | `cad/generate.py` checks on export |
| No part collides with the spinning spool; 2 mm clearance all round | swept-clearance check in `generate.py` |
| Finger tip reaches inside the tooth root | `generate.py` prints tip position |
| Spool body and ratchet print with zero supports | flat faces down, no overhangs |
| Firmware compiles and links for ESP32 (21% flash, 6% RAM) | arduino-cli, esp32 core 2.0.9, ESP32Servo 3.0.5 |

## Not yet verified (hardware needed)

| ID | Item | Test | If it fails |
|---|---|---|---|
| V1 | ESP32 3.3 V signals drive the carrier's 5 V driver logic | commissioning step 4 | 74AHCT125 buffer |
| V2 | Servo angle direction (release = smaller angle) | step 5 | swap `setlock`/`setrel` values |
| V3 | HF0612 press fit in PLA holds without creeping | step 11, then after 20 cycles | CA on the outer ring |
| V4 | Snubber stiffness: 150 mm of 2 mm elastic stops a 100 g spider in about 150 mm | step 7 | double the elastic, or shorten it |
| V5 | Motor skipping at the bead stop is short and harmless | step 9 | lower `rpm`, trim overshoot in `config.h` |
| V6 | Finger lifetime in PLA | step 14 | PETG finger |
| V7 | LD2410C range and through-wall behavior in this house | step 12 | tune gates; AM312 fallback |
| V8 | Firmware on PlatformIO's current esp32 core (3.x) | first `pio run` | pin `platform = espressif32@6.4.0` (core 2.0.x) |

## Known limits of Rev C

- Ceiling mount only.
- No stall sensing; the carrier hides the TMC2209 UART pin.
- Rewind blocks the console for 2 to 3 s.

## Candidate Rev D items (not started)

- Wall-mount variant with a relocated line guide.
- Radar distance read over UART instead of the OUT pin, for a tighter trigger window.
- Enclosure for the controller board.
