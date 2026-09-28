# CLAUDE.md - dropspider-inline

Handoff from the lead mechanical engineer to the software/electrical team. Read `README.md`, then `docs/08_open_items.md`, before changing anything.

**Work still to do, in order: `ROADMAP.md`.** Each task's detail is its handoff (`docs/handoff_task1_firmware.md` for the T1 to T8 bench tests, `docs/handoff_sensor_bearings.md` for the LD2450 radar); finished work is in `CHANGELOG.md`. Doc roles follow the owner's `repo-docs` standard: a handoff holds future work only, and moves to `docs/retired/` when done. The owner is building the inverted install (doc 06, V18): device turned over on steel corner braces on the porch beam; the braces and their holes are his.

Firmware, doc 02, doc 04 and web help text are the team's to change. Rev C.1 rule from the owner: existing hardware only, no new purchases.

**CAD and pictures:** read `cad/README.md` before touching any part, STL or image. It holds the coordinate frame, the rebuild routine (`tools\regen_cad.ps1`), the checks to read after every run, and the lessons already learned. After a CAD change, update only what the change touches (owner 2026-09-27: "stop updating everything all at once - just the parts that need updating"): export only the changed part's STL, run the checks (they only print) and confirm they pass, change only a shared dimension if the owner named every part it affects. No full rebuild, no mass picture or build-guide regeneration unless he asks.

## Project

Drop-spider prop for a porch (the owner is building the inverted install, turned over on the beam; the ceiling install is still in doc 06), Mechanism A (In-Line Single-Axle Clutch Spool), Rev C.1. Mechanical design is released. The team's job: build the firmware out, wire and commission the hardware, and close the open items in `docs/08_open_items.md`.

## Owner preferences

- Owner is not a developer. Reports: verdict first, short, plain English, gloss any jargon in a few words.
- No em dashes, en dashes, arrows, emojis, or curly quotes in anything written for the owner.
- Windows + PowerShell. Local-first. Verify claims before stating them; say plainly what is unverified.
- Before building anything new, name the existing tool or library and say why you are or are not using it.
- Edit files in place and show complete files, not snippets.

## Commands

```powershell
pio run                         # build (env nodemcu-32s, USB COM13)
scripts\update_firmware.bat     # the owner's update: WiFi (3 tries) or USB (automatic; falls back to BOOT + EN buttons)
pio run -e ota -t upload        # flash over the network to dropspider.local
python tools\console.py COM13 status "jog 1600"   # console commands, replies captured
tools\regen_cad.ps1             # regenerate STLs and all images
cd cad; python generate.py      # parts + clash checks only
```

## Hard constraints (do not change without the mechanical owner)

- Motor-led drop (Rev C.1): the motor is powered for the whole cycle and spins ahead of the spool on the drop; the HF0612 lets the spool lag but never overrun it. Never drop with the driver off: the owner measured too much drag on the unpowered motor.
- Release under load must wind the spool CCW about 1/12 turn while the finger swings out (M2). A bare servo release with the spider hanging jams.
- Servo on GPIO13, not GPIO14 (boot pulses would drop the spider).
- Boot must never auto-rewind. Driver EN goes HIGH (off) first thing in `setup()`.
- Armed idle = driver off and servo detached.
- The line must stretch: 6 lb nylon monofilament, whose stretch is the shock absorber (owner 2026-09-26, elastic snubber dropped). Never recommend braid or fluorocarbon without the 150 mm elastic snubber back at the barrel.
- `cad/generate.py` is the source of truth for geometry. Edit it, never the STLs.
- The assembly frame (y from the mount face, z from the motor plate) is used in every doc. Keep it.

## Firmware notes

- Standard PlatformIO layout at the repo root: `platformio.ini`, `src/`, `include/`. Board in use: 30-pin ESP32 DevKit V1 (PlatformIO board `nodemcu-32s`, same chip; the 38-pin NodeMCU-32S also works). Libraries: ESP32Servo, FastAccelStepper, both pinned.
- Platform pinned to `espressif32@6.7.0` (Arduino core 2.0.16). Core 3.x not tested.
- WiFi and update passwords come from `secrets.ini` (gitignored); template `secrets.ini.example`. Never commit `secrets.ini`.
- Runtime settings live in NVS (flash), set from the serial console or the web page; see `docs/04_firmware.md`.
- Limit switch on GPIO32 is a hard cut-off for any move in the rewind direction.
