# 03 - Sensor

## Choice: LD2410C mmWave radar (primary), AM312 mini PIR (fallback)

| | LD2410C (installed) | AM312 PIR (fallback) |
|---|---|---|
| How it sees | 24 GHz radar, motion and breathing | body heat moving across its view |
| Range control | yes, in 0.75 m steps ("gates") set from a phone app | no, only by masking the lens |
| Fires on a slow or still person | yes | no |
| False triggers | sees through thin doors and drywall, so range must be limited | sunlight, HVAC vents |
| Wiring | VCC 5 V, GND, OUT to GPIO33 | VCC 3.3 V to 5 V, GND, OUT to GPIO33 |

Firmware is identical for both: it only watches GPIO33 for a rising edge (LOW to HIGH).

## Placement (see `06_installation.md` picture)

- Top center of the door opening, on the **hallway side** of the header, 1 m lead back to the controller.
- Aim down about 45 degrees, toward where people approach.
- Goal: fire when the person is 0.75 to 1.5 m from the door. At walking pace (about 1.2 m/s) and a drop of about 0.5 s, the spider arrives as they reach the doorway.

## LD2410C setup (one time, phone app)

The LD2410C has Bluetooth. Install **HLKRadarTool** (Android/iOS), power the sensor, connect.

1. **Max moving distance gate: 2** (about 1.5 m). This is the trigger range.
2. **Max static distance gate: 1**. Stops a person standing in the hallway from holding OUT high.
3. **No-one duration (unmanned delay): 1 s**, the shortest. OUT drops soon after the doorway clears.
4. Leave gate sensitivities at default first. Raise the gate 0 and 1 thresholds if it fires on people on the other side of the wall.
5. Turn Bluetooth off in the app when done if the option is present.

## Firmware behavior around the sensor

- Trigger = OUT goes HIGH and stays HIGH for 60 ms, only while armed and idle.
- After each scare: lockout (default 20 s), then the sensor must read LOW for 2 s before it re-arms. A group lingering in the doorway gets one scare, not a loop.

## Fallback: AM312

If the radar misbehaves, swap in an AM312 (same three wires). Put it in a 20 mm long tube (a drinking straw piece or printed sleeve) to narrow its view to the approach. It has a fixed 2 s hold, fine for this use.
