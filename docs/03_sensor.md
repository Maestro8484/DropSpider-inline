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

- **On the device**, in `ld2450_cradle.stl`, which tilts on one M3 bolt between the ears of `ld2450_fork.stl`, glued under the bracket's servo end (+x). Install (ruled by the owner 2026-09-26): under a **porch ceiling, behind the porch overhang's front beam**. People walk in from outside toward the porch, so the servo end, with the radar, points **out from under the porch** toward them. The beam hides the device from them.
- **Orientation, from Hi-Link's manual (section 7, figure 6):** module standing upright, long edge vertical, **antenna side against the cradle's face plate** (two big windows, so it looks out mostly through air), **pin-header side open at the back**, header end at the bottom. The face plate faces out toward the approach. The cradle sets this. Its left-right reading (X) then runs across the walkway, its distance reading (Y) out along it. Confirm on the bench: walk left to right in front of it; X must change, Y stay steady. If Y changes instead, the board is in sideways.
- **Tilt:** set on site, 0 to 50 degrees down, by loosening the M3 nut, swinging the cradle and tightening (every angle in that range is checked clear in `cad/sensor_mount.py`). For the owner's porch (beam 10 in deep, device 12 in behind it) start at 50 degrees: the beam blocks rays shallower than about 45 degrees (doc 06). The device holds it about 2.3 m up, over Hi-Link's recommended 1.5 to 2 m, so the tilt aims the beam at people 1 to 3 m away. The radar must also see out past the porch's front beam: that depends on the porch's ceiling height, the beam's depth and how far behind it the device hangs, not yet measured. Estimate, checked only by test S3 with the live readout. Y is then the slanted distance, a little longer than the floor distance; the arrival timing (`leadms`) absorbs that.
- **Which way up:** the board slides up into the cradle's grooves from the open bottom end, antenna side toward the face plate, **header end last** so the headers end up at the bottom; it stops against the top block and a dab of hot glue holds it. Headers plus dupont plugs (24 mm deep) clear everything at every tilt from 30 to 60 degrees that way; at the top end they would hit the bracket above 40 degrees.
- **Back of the sensor:** the manual warns it also sees a little through its back. The dropping spider hangs about 95 mm behind it (line at x = -25, radar near x = 70). The firmware lockout after a scare covers that; if the falling spider ever retriggers it, a piece of kitchen foil on the cradle's back plate (not touching the pins) cuts it down.
- Keep ceiling fans and moving curtains out of its view; they show up as targets.

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
