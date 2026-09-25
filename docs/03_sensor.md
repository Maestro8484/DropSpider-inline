# 03 - Sensor

Rev C.1. Decision date 2026-09-24. Details and sources in `handoff_sensor_bearings.md`.

## Choice: HLK-LD2450 (primary), HLK-LD2410C (fallback), both already owned

| | LD2450 (primary) | LD2410C (fallback) | PIR, e.g. AM312 (not owned) | Ultrasonic HC-SR04 (not owned) |
|---|---|---|---|---|
| What it reports | X and Y position and speed of up to 3 moving people, about 10 times a second | one yes/no presence line, plus distance over serial | yes/no when a warm body moves across its view | distance to whatever is straight ahead |
| Can it tell approaching from leaving or passing | **yes** | no | no | only by watching distance shrink |
| Can it time the drop to the person's arrival | **yes** (distance divided by speed) | no, fixed trigger distance | no | roughly |
| Setup | none required; optional app for a live map and firmware update | range zones ("gates") set in the app | aim it | aim it, set one distance |
| Wiring | 4 pins: 5 V, GND, TX, RX. **No OUT pin** | 5 pins incl. OUT | 3 pins | 4 pins, 5 V echo needs a resistor divider |
| Connector | 4-pin, 1.25 mm pitch plug | 2.54 mm header | | |
| Weakness | poor at people standing still (irrelevant here) | fires on anyone moving in range, both directions | pets, heat vents, passers-by | narrow beam, soft clothing |

## Wiring

| Sensor pin | ESP32 |
|---|---|
| LD2450 5V | 5 V rail |
| LD2450 GND | GND |
| LD2450 TX | GPIO16 (UART2 RX) |
| LD2450 RX | GPIO17 (UART2 TX) |
| LD2410C OUT (fallback, may stay connected) | GPIO33 |

UART2 at 256000 baud, 8N1. Hardware UART only.

## Placement

- Flat on the wall above the door, **hallway side**, facing straight out down the approach. Not tilted down: the LD2450 is built to look straight out (about 120 degrees wide, 70 degrees tall).
- Its X axis is left-right across the doorway, Y is distance out into the hallway.
- Keep ceiling fans and moving curtains out of its view; they show up as targets.
- **Orientation, from Hi-Link's manual (section 7, figure 6):** module standing upright, long edge vertical, the end marked **Up** in the manual's figure at the top, antenna face toward the hallway. Mounted this way its left-right reading is the X axis across the doorway. Confirm on the bench: walk left to right in front of it; X must change, Y stay steady. If Y changes instead, it is on its side: turn it 90 degrees.
- **Height:** Hi-Link recommends 1.5 to 2 m. Above a 6 ft 8 in door the wall is about 2.05 to 2.1 m, just over; that is fine for walkers, not tilted. If it misses people close to the door, mount it beside the door frame at about 1.8 m instead.
- **Back of the sensor:** the manual warns it also sees a little through its back. The dropping spider is on the room side, behind it. A piece of kitchen foil on the wall behind the sensor (not touching its pins) cuts that down; the firmware lockout covers the rest.

## Trigger rule (firmware)

Fire when any target:
1. is inside the door width: |X| under `doorwidth`/2 (default 500 mm each side),
2. is approaching: speed toward the sensor above `approach` (default 0.3 m/s; sign convention confirmed on the bench),
3. will arrive soon: Y divided by speed under `leadms` (default 750 ms, about release plus drop time),
4. for 2 frames in a row.

Re-arm: existing lockout, then no target inside the window for 2 s.

Why lead time instead of a fixed distance: a fast walker triggers earlier, a slow one later, so the spider lands at the doorway for both.

## One-time app check (HLKRadarTool, optional but recommended)

1. Power the LD2450 from 5 V only. Open HLKRadarTool within arm's length; its Bluetooth range is very short.
2. Check the firmware version. Update in the app if older than V2.02.23090617 (the version ESPHome requires; a safe floor for any library).
3. Walk toward the doorway and watch your dot. It should track smoothly through the door frame.
4. **Leave the app's area detection / zones OFF.** The firmware does the window logic; zones inside the sensor would silently hide targets from it.

## Fallback: LD2410C

Setting `sensor 2410` switches the trigger back to GPIO33. Its app setup (gates) is in git history of this file; summary: max moving gate 2, max static gate 1, no-one duration 1 s, aim down 45 degrees.
