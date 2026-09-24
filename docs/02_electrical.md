# 02 - Electrical

![Wiring](img/wiring.png)

## Pin map, ESP32 DevKit V1 30-pin

| ESP32 pin | Goes to | Direction | Notes |
|---|---|---|---|
| VIN | buck OUT+ (5.0 V) | power in | Do not feed 12 V here |
| GND (any) | common ground | - | All grounds tie together |
| GPIO25 | carrier STEP | out | One pulse = 1/8 motor step |
| GPIO26 | carrier DIR | out | Rewind direction set in firmware |
| GPIO27 | carrier EN | out | LOW = motor powered, HIGH = coils off (free) |
| GPIO13 | SG90 orange | out | Not GPIO14: 14 pulses during boot and twitches the finger |
| GPIO33 | LD2410C OUT | in | HIGH = someone present. Firmware adds a pull-down |
| GPIO16 (RX2) | LD2410C TX | in | Optional, reserved for future radar config over serial |
| GPIO17 (TX2) | LD2410C RX | out | Optional, same |
| GPIO0 | on-board BOOT button | in | Press = manual test drop |
| GPIO2 | on-board LED | out | Slow blink = armed and ready |

## Driver: BIGTREETECH TMC2209 V1.3 on the A4988/DRV8825 carrier

- Plug the driver in with its **EN** pin on the carrier's **EN** position. Backwards destroys it on power-up.
- DIP switches 1, 2, 3 all **OFF**. On a TMC2209 that is 1/8 microstep (each STEP pulse moves 1/8 of a full step) and leaves the UART pin (the driver's serial setup line, unused here) alone.
- Current: turn the driver's pot until the voltage from the pot's metal top to GND reads **0.85 V** (= 0.6 A, 90 percent of the motor's 0.67 A). Do this with 12 V on and the **motor unplugged**. Factory default is about 1.2 V, too high for this motor.
- STEP/DIR/EN only. UART is not wired; the carrier does not bring that pin out.

## Power

| Rail | Source | Loads | Worst case |
|---|---|---|---|
| 12 V | 12 V 2 A wall adapter | driver/motor, buck input | about 0.6 A while rewinding (about 3 s per scare), about 0.05 A idle |
| 5 V | LM2596 buck, set to 5.0 V with a meter **before** connecting anything | ESP32 (0.25 A peak), SG90 (0.7 A stall peak), LD2410C (0.08 A) | about 1 A peak, well under the buck's 2 A |

- 470 uF 16 V electrolytic across the servo's red and brown, at the servo end (stripe to GND). Stops servo current spikes resetting the ESP32.
- Idle draw between scares is a few watts at most: driver disabled, servo detached, radar and ESP32 on.
- USB can stay connected to a PC for the console while 12 V is on.
- Ceiling install: run 12 V up with a 5.5 x 2.1 mm DC extension cable. Keep the adapter at the outlet, never at the ceiling.

## Logic-level check (V1, required before first motor run)

The carrier powers the driver's logic side from its own 5 V regulator, and the ESP32 drives STEP/DIR/EN at 3.3 V. Most TMC2209 boards accept that, but it is not guaranteed.

Test: with the motor connected, run `jog 1600` from the console. The motor must make exactly one smooth turn. Then `jog -1600`, one turn back.

If it stutters, misses, or does nothing while the driver clearly holds (shaft stiff): add a 74AHCT125 (or any 5 V buffer with 3.3 V-compatible inputs) powered from the 5 V rail between ESP32 and carrier on STEP, DIR, EN. Wiring: ESP32 pin -> buffer input, buffer output -> carrier, buffer enable pins to GND.

## Motor wiring

STEPPERONLINE NEMA 11 (0.67 A): black + green = coil A, red + blue = coil B. Black to 1A, green to 1B, red to 2A, blue to 2B. If the motor buzzes but will not turn, swap black and green. Never plug or unplug the motor with 12 V on.

## Sensor wiring

LD2410C on a 1 m lead (4 conductors minimum: VCC, GND, OUT, spare). 5 V power, 3.3 V output, so OUT goes straight to GPIO33. See `03_sensor.md` for placement and tuning.
