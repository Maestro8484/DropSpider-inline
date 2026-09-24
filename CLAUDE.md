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
pio run                         # build (env nodemcu-32s, USB COM13)
pio run -t upload               # flash over USB; tools\flash_usb.bat for the owner
pio run -e ota -t upload        # flash over the network to dropspider.local
python tools\console.py COM13 status "jog 1600"   # console commands, replies captured
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

- Standard PlatformIO layout at the repo root: `platformio.ini`, `src/`, `include/`. Board `nodemcu-32s` (38-pin ESP32-S NodeMCU). Libraries: ESP32Servo, FastAccelStepper, both pinned.
- Platform pinned to `espressif32@6.7.0` (Arduino core 2.0.16). Core 3.x not tested.
- WiFi and update passwords come from `secrets.ini` (gitignored); template `secrets.ini.example`. Never commit `secrets.ini`.
- Runtime settings live in NVS (flash), set from the serial console or the web page; see `docs/04_firmware.md`.
- Limit switch on GPIO32 is a hard cut-off for any move in the rewind direction.

## Suggested backlog, in order

1. Close V1 (logic level) and V2 (servo direction) on the bench.
2. Optional: read LD2410C target distance over UART2 (GPIO16/17 already wired) for a tighter trigger.
3. Add a `test` command that runs commissioning steps 4 to 11 with prompts.

Non-blocking rewind is done: the machine runs on its own task and FastAccelStepper makes the pulses.
