# CLAUDE.md - dropspider-inline

Handoff from the lead mechanical engineer to the software/electrical team. Read `README.md`, then `docs/08_open_items.md`, before changing anything.

## Project

Ceiling-mounted drop-spider prop, Mechanism A (In-Line Single-Axle Clutch Spool), Rev C. Mechanical design is released. The team's job: build the firmware out, wire and commission the hardware, and close the open items V1 to V8.

## Owner preferences

- Owner is not a developer. Reports: verdict first, short, plain English, gloss any jargon in a few words.
- No em dashes, en dashes, arrows, emojis, or curly quotes in anything written for the owner.
- Windows + PowerShell. Local-first. Verify claims before stating them; say plainly what is unverified.
- Before building anything new, name the existing tool or library and say why you are or are not using it.
- Edit files in place and show complete files, not snippets.

## Commands

```powershell
tools\flash.ps1                 # build, flash, open console (pio)
tools\regen_cad.ps1             # regenerate STLs and all images
cd cad; python generate.py      # parts + clash checks only
```

## Hard constraints (do not change without the mechanical owner)

- Motor must never be back-driven during the drop: the HF0612 clutch is the design.
- Servo on GPIO13, not GPIO14 (boot pulses would drop the spider).
- Boot must never auto-rewind. Driver EN goes HIGH (off) first thing in `setup()`.
- Armed idle = driver off and servo detached.
- Snubber is mandatory; never recommend operating without it.
- `cad/generate.py` is the source of truth for geometry. Edit it, never the STLs.
- The assembly frame (y from the mount face, z from the motor plate) is used in every doc. Keep it.

## Firmware notes

- `firmware/src/main.cpp`, `firmware/include/config.h`. Library: ESP32Servo.
- Compiled clean on arduino esp32 core 2.0.9. PlatformIO may pull core 3.x; if the build breaks, pin `platform = espressif32@6.4.0`.
- Runtime settings live in NVS (flash) via the serial console; see `docs/04_firmware.md`.

## Suggested backlog, in order

1. Close V1 (logic level) and V2 (servo direction) on the bench.
2. Make rewind non-blocking so the console stays live.
3. Optional: read LD2410C target distance over UART2 (GPIO16/17 already wired) for a tighter trigger.
4. Add a `test` command that runs commissioning steps 4 to 11 with prompts.
