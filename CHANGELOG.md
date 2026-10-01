# Changelog

Finished work, newest first, one plain line each. Shape from Keep a Changelog (keepachangelog.com). Work still to do is in `ROADMAP.md`; the full detail of any line is in the git history for that date.

## 2026-09-30

### Changed
- `fairlead_flap_inv`: owner's redesign. The tab runs 3.7 mm further toward the hinge and a sloped web fills the notch beside the prong, so the side has no step for the line to catch; the line slot runs 1.4 mm deeper. Source (`cad/inverted.py`) now builds it to within 3.5 mm3 of his STL; his STL is kept as the print file. All inverted checks unchanged (clashes, line path, hard stop 14.75, roller push 4.13, rest 9.5).
- Doc 02: motor part number 11HS12-0674S, 5.6 ohm coil check, female jumper ends on the bare leads.

## 2026-09-29

### Added
- `bearing_retainer`: thin 2 mm plate on the end plate's outside face that stops a loose 606ZZ walking out; 12 mm hole for the rod, 2x M3 into pilots drilled through the end plate. No clashes in either install.
- Build note (owner's build): about 4 mm of shim on the motor side of the spool and 5 mm on the 606ZZ side for a snug, free stack.

### Changed
- Ratchet disk is now a plain 7 mm plate, teeth full height, flat both faces (owner: no lip); it prints with the shield face on the bed, so the counterbores need no bridging. 0.4 edge breaks on the bearing holes where they print on the bed. Assembly order: screw the three together first, then press the HF0612 through all three.
- Spool stack (owner): new `spool_shield`, a flat 1.5 mm disc 64 mm across between the ratchet disk and the spool body, so the line cannot reach the teeth. No boss and recess any more (it left a 1 mm gap at the rim): all three sit on flat faces, centred by the HF0612 running through all three 10.3 holes and the 3 screws. Ratchet gets a 1 mm flat plateau so the shield clears the finger by 1 mm; spool body shortened to keep the stack length, line channel now 3.5 mm. Finger seating, clashes and the inverted checks unchanged. `spool_ratchet`, `spool_shield`, `spool_body` exported.

## 2026-09-28

### Added
- Radar handoff: four things the firmware must handle in the inverted install (radar axes, the spider in the radar's view, aluminum, the longer line between spool and flap).
- `ROADMAP.md`, this changelog, and a doc map in the README: each file has one job.

### Changed
- HF0612 holes in `spool_body` and the `spool_ratchet` center both 10.3 (owner: same diameter in both; 10.0 would not go in, 10.2 tight, 10.7 loose). Both STLs re-exported. Was: `spool_body` 10.3 (owner: 10.0 would not go in, 10.2 tight, 10.7 loose). Only `spool_body.stl` re-exported.
- Spool body and ratchet disk spoked (3 spokes, 3 windows): 18.3 to 8.0 and 16.1 to 9.5 cm3, every mating face unchanged. Fairlead block rounded (column edges r 1.5, as the build123d trial) with 3 through-windows: 15.7 to 12.8 cm3, all inverted checks unchanged. Build guide pictures redrawn with both.
- Every clockwise and counterclockwise in the docs, the build guide, the pictures and the firmware comment is now seen from behind the motor (owner): spider falling counterclockwise, winding clockwise, the HF0612 locks when the rod turns clockwise. Mirror of the old 606ZZ-end wording; nothing on the parts changed.
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
