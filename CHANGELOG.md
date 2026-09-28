# Changelog

Finished work, newest first, one plain line each. Shape from Keep a Changelog (keepachangelog.com). Work still to do is in `ROADMAP.md`; the full detail of any line is in the git history for that date.

## 2026-09-28

### Added
- Radar handoff: four things the firmware must handle in the inverted install (radar axes, the spider in the radar's view, aluminum, the longer line between spool and flap).
- `ROADMAP.md`, this changelog, and a doc map in the README: each file has one job.

### Changed
- HF0612 one-way bearing holes opened (owner: 10.0 would not take it, the disk's 10.6 took the stub only after sanding): `spool_body` 10.7 tight press, `spool_ratchet` center hole 11.0 slip. Both STLs re-exported; reprint both.
- Build guide: the HF0612 labelled as the one-way bearing everywhere, drawn as its own part in the exploded view, and a new cut-away picture of every part on the rod; the title bar is plain text again.
- Build guide covers only the inverted install; the ceiling install stays in doc 06. Web page picture matched to the firmware; radar chip marked not live until task 2; finger angles 85 and 50.
- Build guide: no separate power board. The expansion board and the 5 V buck are hot-glued beside the main board; 12 V runs straight from the jack.
- Task 1 handoff cut down to the work still to do.

### Removed
- Wall-install drafts (hinge plate, hinge clip, tie bar, strut, braced shelf) to `cad/retired/` and `docs/retired/`.
- Inverted-install handoff to `docs/retired/`: design, checks, docs and the Fable check all done; building it is on the roadmap.

## 2026-09-27

### Added
- Firmware Rev C.1: motor-led drop, release under load (wind 1/12 turn while the finger swings out), seat move on lock, home remembered from the last cycle, settings `dropmm`, `droprpm`, `dropacc`, `dropdec`, `relms`. Flashed over WiFi.
- Inverted install (owner's plan, approved): device turned over on two 6 in steel corner braces on the beam's inside face, line out through the base. `cad/inverted.py`, `fairlead_base.stl`, the drilling template `bracket_footprint_inverted.svg`, doc 06 section, open item V18. CAD-checked, not built.
- Radar fork bolted with 2x M3 (`ld2450_fork_screw.stl`), no glue; ears 4 mm thick, 12 mm across.

### Changed
- 606ZZ bearing seat drawn at 17.0 mm (16.8 would not take the bearing even heated).
- Flap: the prong beside the line slot widened from 1.2 to 3.8 mm.
- Rule: after a CAD change, export and check only the part that changed; no full rebuilds.

### Fixed
- Inverted install, from the Fable check: brace bolt zones, lead routing, a boss under the short block screw, 7 mm line hole.

### Logged
- Servo is a positioning MG90, not a 360 one; finger angles set to 85 (lock) and 50 (release).

## 2026-09-26

### Changed
- Line is 6 lb nylon monofilament, no elastic, no braid.
- Finger presses straight onto the servo spline, no horn; socket drawn 5.0 mm.
- Fairlead: no glue, 2x countersunk M3; one flat mounting face; body reinforced; flap hinge pin is an M2 bolt.
- Radar on the device in a cradle that tilts on one M3 bolt; porch measured (8 ft ceiling, 10 in beam, device 12 in behind it), tilt 50 degrees.
- Fit-check fixes on every part (holes print small on the owner's printer).

### Fixed
- The fairlead bore was never cut; the part printed solid.

### Added
- Laser-cutter drawing of the bracket's ceiling face with every hole.

## 2026-09-25

### Added
- Build guide: one page for wiring, assembly, power-up and web setup; protoboard layout.
- `scripts/update_firmware.bat`: double-click update by WiFi or USB. `tools/esptool_noreset.py` for USB flashing.
- Rev C.1 owner design and docs: clutch direction fix (M1), finger release fix (M2), LD2450, fairlead with KW12-3 switch.

### Changed
- Board in use is the 30-pin ESP32 DevKit V1. 5 V supply is a fixed-5 V MP1584EN buck.

### Logged
- Board identified by esptool, first USB flash, joined the home WiFi, network updates work.

## 2026-09-24

### Added
- Firmware: web page (console, bench controls, settings, network setup), network firmware updates, limit switch hard cut-off, three-strike fault stop. The machine runs on its own task, so a rewind no longer blocks the console.
- `tools/console.py`: console commands over USB or the network.
- Standard PlatformIO layout, pinned platform, passwords kept out of git.
- Rev C handoff baseline.
