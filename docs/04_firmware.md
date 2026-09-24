# 04 - Firmware

Location: `firmware/` (PlatformIO, Arduino framework, board `esp32dev`). One source file `src/main.cpp`, constants in `include/config.h`. Only external library: ESP32Servo.

## Build and flash (Windows, PowerShell)

```powershell
pip install platformio
cd firmware
pio run -t upload
pio device monitor
```

Or run `tools\flash.ps1`, which does the same and opens the console.

## Cycle

```
IDLE (armed) --sensor edge or BOOT button--> RELEASE finger (spider free-falls)
  --settle 1.5 s--> REWIND (fixed steps + 0.75 turn overshoot, bead stops on eyelet)
  --> LOCK (finger in, motor off, spool settles onto a tooth, servo off)
  --> LOCKOUT 20 s --> WAIT_CLEAR (sensor LOW for 2 s) --> IDLE
```

Power states: armed and idle = driver off, servo off. Only the ESP32 and radar draw power.

Boot: driver off, finger to LOCK, never rewinds on its own. The spider is assumed to be up.

## Serial console, 115200 baud

| Command | Does |
|---|---|
| `help`, `status` | list commands; show settings, sensor state, computed rewind steps |
| `arm`, `disarm` | enable or ignore the sensor |
| `drop` | full cycle now |
| `rel` | finger out only: spider drops, no rewind |
| `rewind` | rewind only; motor stays on until `lock` |
| `lock` | finger in, motor off, settle |
| `jog <n>` | move n microsteps (1600 = one turn), + = rewind direction, motor stays on |
| `off` | motor and servo off |
| `servo <deg>` | move the finger live, to find angles |
| `setlock <deg>`, `setrel <deg>` | store finger angles |
| `line <mm>` | braid length from the spool knot to the stop bead |
| `rpm <n>` | rewind speed, 30 to 600, default 240 |
| `dir <0/1>` | flip rewind direction |
| `settle <ms>`, `rearm <ms>` | hang time, lockout time |
| `save`, `defaults` | write settings to flash; reload factory values |

Settings apply immediately; `save` keeps them through power loss.

## Rewind math

steps = ((line - 40 mm) / (pi x 50 mm) + 0.75 turn) x 200 x 8

The 40 mm is braid that stays between spool and eyelet. The 0.75 turn overshoot guarantees the bead reaches the eyelet; the motor then slips (skips steps, a short buzz, harmless at 0.6 A) for the remainder.

## Known limits

- Rewind is blocking: the console does not respond for the 2 to 3 s of a rewind.
- No stall detection: needs the driver's UART line, which the carrier does not expose.
- Radar UART pins are wired but unused. Future: read moving-target distance directly instead of OUT.
