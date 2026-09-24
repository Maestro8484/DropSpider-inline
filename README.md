# dropspider-inline

**DropSpider, Mechanism A: In-Line Single-Axle Clutch Spool (ISCS), Rev C.**
A ceiling-mounted Halloween prop that free-falls a foam spider 0.5 to 1.2 m when someone walks through a doorway, then winds it back up and re-arms on its own. Zero power while waiting.

Sibling project name reserved: `dropspider-tiltspool` (Mechanism B, servo-driven tilt-spool free-fall). Not started. This repo is Mechanism A only.

![Installed assembly](docs/img/assembly_iso.png)

## How it works

Stepper motor -> coupler -> 6 mm rod. The spool rides the rod on a one-way clutch bearing: the motor can wind it up, but the spool spins free when the spider falls, and the motor never turns during the drop. A servo-driven finger in a ratchet holds the spool at the top with no power. A radar sensor at the door triggers the cycle.

## Repo map

| Path | What |
|---|---|
| `docs/01_mechanical_design.md` | design spec, stack-up, lock mechanism, direction rules, print settings |
| `docs/02_electrical.md` | pin map, power, driver setup, logic-level check |
| `docs/03_sensor.md` | LD2410C placement and tuning, PIR fallback |
| `docs/04_firmware.md` | cycle, serial commands, rewind math |
| `docs/05_assembly.md` | step-by-step assembly with pictures |
| `docs/06_installation.md` | doorway geometry, heights, fastening, safety |
| `docs/07_commissioning.md` | bench and on-site test checklist with pass criteria |
| `docs/08_open_items.md` | what is verified, what is not, risks |
| `cad/generate.py` | source of truth for every printed part |
| `cad/stl/` | print-ready files |
| `firmware/` | PlatformIO project, ESP32 DevKit V1 30-pin |
| `bom/BOM.csv` | every part, ordered or still to buy |
| `tools/*.ps1` | flash firmware; regenerate CAD and images |

## Quick start

1. Print the parts in `cad/stl/` (settings in doc 01).
2. Buy the "TO BUY" lines in `bom/BOM.csv`.
3. Assemble per doc 05.
4. Wire per doc 02. Set buck to 5.0 V and driver Vref to 0.85 V first.
5. `tools\flash.ps1`, then run doc 07 on the bench.
6. Install per doc 06.
