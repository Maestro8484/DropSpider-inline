# Handoff: task 1 firmware (M1 fix, motor-led drop) and bench tests T1 to T8

What this is for: a fresh session builds the Rev C.1 firmware in `docs/M1_fix_handoff.md`, flashes it over WiFi, and runs bench tests T1 to T8 with the owner, logging each in `docs/commissioning_log.md`.

## Ground truth first

This file is a pointer, not a record of truth. The local repo wins. If anything here disagrees with a file, the file is right and this handoff is stale: say so out loud.

Staleness check, run first:

```
git log -1 --oneline                                     # where the repo is now
git log -1 --oneline -- docs/handoff_task1_firmware.md   # when this handoff was last true
```

Same hash: nothing landed since. Different: re-verify each state line below.

## Read before touching anything

1. `CLAUDE.md` (repo root): hard constraints. The ones that bite here: motor-led drop, never drop with the driver off; release under load winds CCW about 1/12 turn while the finger swings out; servo on GPIO13; boot never auto-rewinds and EN goes HIGH first in `setup()`; armed idle = driver off, servo detached.
2. `docs/M1_fix_handoff.md`: the spec. Section "Firmware spec" is the work; section "Bench tests" is T1 to T8.
3. `docs/04_firmware.md`: how the firmware is laid out, console commands, update paths.
4. `docs/09_fairlead_switch.md`: V14, the limit switch reads OPEN at rest after the lock seat by design; infer home from the last cycle, not the boot reading.

## State facts, recorded 2026-09-27, each with how it was checked

| Fact | How checked |
|---|---|
| Task 1 firmware not started: none of `dropmm`, `droprpm`, `dropacc`, `dropdec`, `relms` exist in `src/` or `include/` | grep over `src` and `include` |
| Firmware structure: machine on its own FreeRTOS task with a request queue (`src/machine.cpp`); one console command set for serial and web (`src/console.cpp`, `src/web.cpp`); settings in NVS (`src/settings.cpp`); ArduinoOTA and web Update | reading `src/` |
| Libraries pinned: ESP32Servo, FastAccelStepper (hardware step pulses; `forceStopAndNewPosition` used for the limit cut-off). Separate accel and decel for the powered drop: check FastAccelStepper supports it BEFORE designing around it, and report | `platformio.ini`; the separate-decel question is open |
| Board: 30-pin ESP32 DevKit V1, env `nodemcu-32s`, USB COM13; OTA env `ota` to `dropspider.local` | `platformio.ini`, `CLAUDE.md` |
| The owner updates by double-clicking `scripts\update_firmware.bat` (WiFi, 3 tries, then USB). He does not type commands | `CLAUDE.md`, global rules |
| Console from this PC: `python tools\console.py dropspider.local status` or `COM13` | `docs/04_firmware.md` |
| WiFi and update passwords come from `secrets.ini` (gitignored). Never commit it | `CLAUDE.md` |

## Hardware changed since the spec was written (all 2026-09-26, owner)

| Change | What it means for task 1 |
|---|---|
| Finger now presses straight onto the SG90 spline (no horn), 7 mm plate | Lock and release angles must be found again on the bench (`servo <deg>`, then store). Old stored angles are meaningless |
| The owner's spare SG90 has no hard stop by hand: likely a 360 degree continuous-rotation servo | **Before T3, confirm the fitted servo is a 180 degree positioning one**: `servo 90`, `servo 30`, `servo 150` with no finger fitted; it must move to a spot and hold. A 360 one keeps spinning and cannot lock the spool |
| Line is 6 lb nylon monofilament, no elastic, no braid | `line` value = barrel knot to bead, line straight not pulled. The line's stretch is the only shock absorber if the motor loses grip |
| Fairlead switch face moved 0.8 mm; KW12-3 mounted flat, no washers | Re-set the switch click point with the slots before T2 (flap lifted about 2 mm must click) |
| Flap hinge pin is an M2 bolt | none |

## The work, in order

1. Check FastAccelStepper for separate acceleration and deceleration on a move (and how to switch profiles mid-cycle); report what it supports in one line before designing.
2. Implement the spec: unload plus release sequence (wind about 1/12 turn CCW while the finger swings out), powered motor-led drop to `dropmm` at `droprpm` with `dropacc` / `dropdec`, lock seat move, `rel` with the motor on, the new NVS settings with console and web fields, V14 home inference stored in NVS. Boot never rewinds.
3. Build (`pio run`), then flash over WiFi (`pio run -e ota -t upload`). Report the result as observed output only.
4. Bench tests T1 to T8 with the owner. **Before any motor or servo move, ask him to confirm hands and line are clear, and wait for his yes.** Log each test, pass or fail, with what was seen, in `docs/commissioning_log.md`. A test not run is written as "not run", never as a pass.
5. Update doc 04 and the web help text for the new settings and commands.

## Rules for the session

- Owner is Joe. Replies are barebones, verdict first, plain English, no excuses; see his global CLAUDE.md.
- He never types commands: the session runs them. He can double-click a .bat, change an app setting, look and answer in one line.
- One task per commit, files staged by name.
- Verify before claiming: "works" only after running it and reading the output.
