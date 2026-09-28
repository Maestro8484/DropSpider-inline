# Handoff: task 1, bench tests T1 to T8 of the Rev C.1 motor-led drop

What this is for: fix the spool-to-flap length for the inverted install, then run bench tests T1 to T8 with the owner, fix what fails, and log every result in `docs/commissioning_log.md`. Future work only; what is already done is in `CHANGELOG.md`.

## Ground truth first

This file is a pointer, not a record of truth. The local repo wins. If anything here disagrees with a file, the file is right and this handoff is stale: say so out loud.

Staleness check, run first:

```
git log -1 --oneline                                     # where the repo is now
git log -1 --oneline -- docs/handoff_task1_firmware.md   # when this handoff was last true
```

Same hash: nothing landed since. Different: re-run the checks below before trusting them.

## Before you start: run these checks

| Check | How |
|---|---|
| Rev C.1 is on the board | `python tools\console.py dropspider.local status`: boot line "Rev C.1 ready"; `help` lists `dropmm`, `droprpm`, `dropacc`, `dropdec`, `relms` |
| The servo is a positioning one, not a 360 | `docs/commissioning_log.md` has a V17 PASS row; if not, `servo 90`, `servo 30`, `servo 150` with nothing on the spline: it must move and hold |
| Finger angles stored | `status` shows `setlock` and `setrel`; the log has the owner's values. Recheck them with the ratchet on the rod in T3 |
| The mechanism is assembled on the bench: spool with the HF0612, ratchet, finger, motor, fairlead or `fairlead_base` with flap and KW12-3, line and bead | ask the owner, one line |

## Read first

1. `CLAUDE.md` (repo root): hard constraints. The ones that bite here: motor-led drop, never drop with the driver off; release under load winds clockwise (seen from behind the motor) about 1/12 turn while the finger swings out; servo on GPIO13; boot never auto-rewinds and EN goes HIGH first in `setup()`; armed idle = driver off, servo detached.
2. `docs/M1_fix_handoff.md`: section "Bench tests" is T1 to T8; "Firmware spec" is what the firmware on the board implements.
3. `docs/04_firmware.md`: firmware layout, console commands, update paths.
4. `docs/09_fairlead_switch.md`: V14, the switch reads OPEN at rest after the lock seat by design; home comes from the last cycle.
5. `docs/handoff_sensor_bearings.md`, "Inverted install", item 4: the spool-to-flap length.

## The work, in order

1. **Spool-to-flap length.** `include/config.h` `SPOOL_TO_EYELET_MM` is 40 (its comment still says braid; the line is 6 lb mono). The owner is building the inverted install, where it is about 72 mm with fairlead v2 (doc 09). Set it to 72, or make it a setting, and fix the comment. Check the factory `dropmm` (620) against an inverted line of about 636: the limit is line minus that length minus 30, so it must come down or the page refuses the new line. Build (`pio run`), flash over WiFi (`pio run -e ota -t upload`), report the observed output only.
2. **Bench tests T1 to T8 with the owner.** Before any motor or servo move, ask him to confirm hands and line are clear, and wait for his yes. Re-set the switch click point with its slots before T2 (flap lifted about 2 mm must click). Log each test, pass or fail, with what was seen. A test not run is written as "not run", never as a pass.
3. **Fix what fails**, one change per commit, and re-run the failed test.
4. **Close the open items the tests settle** in `docs/08_open_items.md` (V1, V2, V9, V13, V14), each with the log row as evidence. Update doc 04 and the web help text for anything changed.
5. **Finish:** changelog line, remove this task's roadmap lines, move this file to `docs/retired/`.

## Tests

T1 to T8 as written in `docs/M1_fix_handoff.md`, section "Bench tests", each logged in `docs/commissioning_log.md`.

## Done when

T1 to T8 are each logged as PASS on the bench with the spool, clutch, finger and switch fitted.

## Rules for the session

- Owner is Joe. Replies are barebones, verdict first, plain English, no excuses; see his global CLAUDE.md.
- He never types commands: the session runs them. He can double-click a .bat, change an app setting, look and answer in one line.
- One task per commit, files staged by name.
- Verify before claiming: "works" only after running it and reading the output.
