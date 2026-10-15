# Changelog

Finished work, newest first, one plain line each. Shape from Keep a Changelog (keepachangelog.com). Work still to do is in `ROADMAP.md`; the full detail of any line is in the git history for that date.

## 2026-10-14

### Changed
- Reference docs 01 to 09 and `cad/README.md` now read in my own voice: "the owner", "his" and the dated owner tags are gone and the facts stand on their own, first person wherever I measured, printed, wired or ruled something, 117 passages across 10 files. Every number, part name, direction rule and date that names a print or a bench event is unchanged. `python tools/check_repo.py` ALL PASS.
- Docs sweep after the publish pass: doc 03 rewritten for the C4002 as it is (why it, where it sits, the trigger rule, its own settings, the parked LD2450 and C4001 at the bottom for the record); doc 06's sensor section and the inverted install's status (built, on the bench over the front door, the porch ahead); doc 01's Rev C.4 status (printed and benched, no longer "model only"); the disc on the line is "the stopper" in docs 01, 02, 04, 05, 07 and 09 (owner's word); doc 05 names the swivel mount; the wiring page's LED row and mount line; "repo" and "commit" out of the reference docs. README has a marked slot for the photos and video the owner will provide (roadmap line 8b).

### Added
- Publish pass, docs only (`docs/handoff_publish.md`, retired): `LICENSE` at the root (MIT for everything, owner 2026-10-14: "MIT all"; the C4002 case alone under the MakerWorld original's CC BY-NC-SA); README rewritten in the owner's voice with the C4002, the inverted install, the firmware version, the repo check and the doc map complete (the two audits and the flash 11 handoff on it); the build guide gets a firmware section for a fresh PC (VS Code, PlatformIO, `secrets.ini`, the USB flash, the version the board reports), the LED meanings, the page as flash 11 draws it, the switch presses, the radar card drawn for the C4002, the swivel mount parts, and its chips now say WORKS, BENCH ONLY, FLASH 11 or PLANNED; BOM matched to the parts on the device (C4002 in, LD2450 parked, wiring consumables added, no prices invented); doc 09 and the sensor handoff reworded so `scripts\check_repo.bat` option 2 ends ALL PASS. Two stale CAD drawings and one stale export name listed in `docs/08_open_items.md` for a CAD session.
- Web page, from the owner's audit rulings (`docs/audit_webui_horizon.md`): every button's reply shows in a strip where it was pressed (a refusal in red), a bar pinned to the bottom of the screen shows the state and the newest log line, a Last cycles card keeps the last 20 cycles through a power cut with a chip for how each rewind ended (`/api/cycles`), changed settings get an amber edge and one Save bar at the top until saved (a dot marks a value that differs from factory), Set drop length here asks first and names the number it will replace, and every card but Status folds from its heading with the browser remembering which are open. BUILT (`pio run` SUCCESS), seen working against a mock of the board's API in a browser, not flashed.
- Sleep by hand: the limit switch pressed 5 times within 4 s while nothing moves puts the device to sleep (not armed, the radar ignored); 5 presses again, Arm on the page, `arm`, or a power cycle wakes it. 3 presses still bring it home; a run of presses is judged 1.2 s after the last one, so pressing on past 3 does not start a rehome (owner: "employ a 'sleep mode' by pressing the limit switch 5 times within 4 seconds"). BUILT, not flashed.
- Blue LED while asleep (not armed, at rest): one short flash every 2 s, so an asleep device no longer looks like a dead one; off now means armed but waiting to re-arm (owner: "powered-on but asleep needs a distinctly different led indicator"). The board's red LED is not on a pin the firmware drives. BUILT, not flashed.
- Stop or Off during a teach or a bring-it-home run now ends that run; before, the flag stayed set and the next plain rewind would have finished it (a stopped teach would then have set the drop length). BUILT, not flashed.
- Firmware version stamp: every build carries a version read from git (`tools/fw_version.py` through the `build_flags` line in `platformio.ini`), shown in the boot log, the `status` line, `/api/status` as `fw` and the page's Status card. Builds that reach the board are tagged `fw-N` (tags `fw-9` and `fw-10` placed on the commits the bench log names). `scripts\update_firmware.bat` asks the board what it runs after a WiFi update (`tools/board_version.py`, MATCH or DIFFERENT). BUILT (`pio run` SUCCESS, the stamp `fw-10+3.f6a9849*` read in the binary), the board check seen working against the live board (reports "older than fw-11"), not flashed.
- Repo health check, `scripts\check_repo.bat` (`tools/check_repo.py`): passwords untracked, a LICENSE present, every doc on the README map, every handoff on the roadmap and holding future work only, no dead markdown links, every named STL present, the version stamp clean, and with option 2 a full build. Run today: 8 FAIL, all handed to `docs/handoff_publish.md`.
- VS Code files kept the PlatformIO way: `.vscode/extensions.json` (offers the PlatformIO extension) is now tracked; the two files PlatformIO regenerates on every open (`c_cpp_properties.json`, `launch.json`) and its caches stay ignored by name instead of the whole folder.
- `cad/README.md`: the `.3mf` files in `cad/stl/` are the owner's own slicer projects; no session writes one.

### Changed
- The two CAD drawings the publish pass found stale, `docs/img/assembly_iso.png` and `docs/img/inverted_install.png`, redrawn with the parts on the device: the Rev C.4 spool and cap, the C4002 in its snap-lid case on the code's fork (the owner's swivel mount is his own Fusion file, so the fork stands in for it), the line labelled as the bonded nylon thread and the disc on it as the stopper; `python cad/render.py <picture>` now draws one named picture, the legend sits beside the picture, and the build guide and README no longer call the drawings older than the radar mount. The bolted radar fork is `c4002_case_short_mount` in the code (was `ld2450_fork_screw`), matching its STL; every check script re-run clean, no STL rewritten. `assembly_iso_top.png` and the other CAD pictures still show the Rev C.2 stack.
- Every power-up arms on its own; armed is no longer a saved setting, and disarm (including the disarm every bench move does) holds only until the next power cycle. The home guard still stops a power-up with the spider down on a fault. FLASHED, VERIFIED on the restart after the flash (owner: it must come up armed after a power cut).
- The board can keep a fixed network address: page Network card, Fixed address, or console `ip <address>` and `restart`. Set to 192.168.1.138 after the router moved the board to .135 overnight. FLASHED, VERIFIED: boot log `[wifi] fixed address 192.168.1.138, router 192.168.1.1`.
- Console `restart` restarts the board (refused while a move runs).

## 2026-10-13

### Changed
- Pressing the limit switch 3 times fast now brings the spider home from anywhere (lower 1/2 turn, wind slowly to the switch, clear the fault, re-arm) instead of setting the drop length; setting the length stays on the page button. FLASHED 2026-10-13, not yet exercised.
- Rewinds after a drop finish at 80 rpm over their last 2 1/4 turns, and a rewind that misses the switch gets one slow second try before the fault. FLASHED 2026-10-13; the second try VERIFIED by the board 2026-10-14 (drop 139: first pass missed the switch, the slow try closed it). 41 radar drops overnight, no fault.
- The owner's radar mount redesign is in the STL folder: `c4002_case_base_extended.stl` (19 mm longer pivot to case) and `c4002_case_Swivel_mount.stl` (swivels left and right); the old fork is `c4002_case_short_mount.stl`. Docs and the export name follow.

### Added
- The log up to the last fault survives a power cut: `lastlog`, page button Last fault log. BUILT, not flashed.

## 2026-10-12

### Added
- Teach the drop length: with the spider hanging where a drop should stop, press the limit switch 3 times fast (or the page button Set drop length here, or `teach`); it winds up to the switch, counts the steps and saves them as `dropmm`. FLASHED, not yet exercised.
- Setting `clearms` (re-arm anyway after waiting this long for the doorway to clear) and the page button Clear and re-arm. VERIFIED on the board.

### Changed
- A still radar reading no longer holds the re-arm; only someone moving does. Lockout after a drop set to 0 and `clearms` to 1000 at the owner's ask, so it re-arms about 1 s after the lock.
- Blue LED: solid = armed and ready, fast blink = fault or spider not home, slow blink = moving.
- Drop now 700 mm at 600 rpm (was 620 at 500): the spider goes about 2 in farther and each millimeter is about 10 percent quicker. 700 rpm was tried and lost about 10 cm of drop to skipped steps.

### Fixed
- No drop starts unless the spider is home. A power-up with the spider down used to arm and fire, leaving it hanging part way; it now stops on a fault. VERIFIED at power-up.

## 2026-10-10

### Fixed
- C4002 radar code audited on Fable against DFRobot's three decoders (Arduino library, Python port, ESPHome component in DFRobot's fork), read that day, none linked. The result frame is now decoded as 18 data bytes packed, the way the Python port and the ESPHome component read it (the Arduino library copies the bytes over a padded 20-byte C struct; the ESPHome component has that copy commented out). Four fixes in `src/radar.cpp`: the "two readings in a row" count resets after a gap of 0.5 s between frames, so a reading from before a dropout cannot pair with the first one after it; the report-period command is sent again every 5 s while no frames arrive (it was sent once at 1.5 s and never again, so a sensor booting slower than the board stayed silent until a power cycle); a status byte of 3 (both a moving and a still person, in the Arduino library's enum) now counts as both instead of as nobody, which would have read the doorway as clear; the version string is kept free of quote marks before it goes into the page's JSON. New setting `radarinv` (0 or 1): swaps approaching and away before the rule, because DFRobot's code enums say 2 = approaching and its Home Assistant tutorial says 0; test S2 decides it from the page, no rebuild. What the radar saw when a drop fired is kept and shown. Frame sync, checksum, length guards, the `leadms` arithmetic (no divide at speed 0), the silent-link fallback to the OUT pin and back, and the armed-and-idle gate on the trigger were read and found right. `pio run` passes. NOT yet run on a sensor.

### Added
- First bench of the C4002, office doorway mount (6 ft 10 in up, 55 degrees down), owner at the device, every run in `docs/commissioning_log.md`. VERIFIED on the sensor: 18 data bytes per result frame, 10 frames a second, 0 bad in over 100,000 frames; the direction word is right as built (2 = approaching, negative speed = approaching); the sensor keeps its report period through a power cut; the silent-link fallback to the OUT pin and the return both fire when the sensor restarts; the radar fired the drop twice (drops 27 and 28), each a clean cycle to the switch and the lock. Three firmware changes came out of it, all flashed: `firecm`, a fire distance (owner: "less timed and more proximity-based"), because on a 2 m overhead mount the lead-time rule could not fire at a slow pace (the reading is slant range and the speed toward the sensor fades under it); `clearcm`, the clear distance as a setting, because a screen at 2.2 m held the device in "waiting for the doorway to clear"; and `radar range` restarts the sensor, because the range does not take until it does. Four of the sensor's own settings got console commands and card controls, all from DFRobot's library: range step (`radar res`), sensitivity (`radar sens`), how long it keeps a person (`radar delay`, shipped at 15 s, set to 2) and learn the empty room (`radar calib`). The card also says where a person is when the spider lands (trigger to bottom measured each drop). Current draw not measured (owner's call). Still owed: foil behind the sensor (walking out of the office from behind it triggers it), the room calibration, S3's run count, S2's swing test, S4, the S5 wire pull, porch numbers.

### Changed
- Web page, radar card rebuilt (`src/web.cpp`): the controls sit beside what they set. Walking speed that fires, lead time, "Direction reads backwards" (a tick), what fires the drop (a pick list), and the sensor's own detect range as two fields with Set and Read, plus Save settings, all on the card; those rows left the Settings card. New rows: the last drop the sensor fired and what it saw, and the OUT pin. The health line names the data byte count per frame and flags any count but 18. Help text cut to four sentences. Checked in a browser against a mock board, not on the device.

### Added
- `cad/c4002_case.py` and `cad/stl/c4002_case_base.stl`, `c4002_case_lid.stl`: the C4002 radar case on the existing radar fork, drawn after a MakerWorld enclosure (CC BY-NC-SA, credit and the original download in `cad/ref/c4002_enclosure/`). Inside 22.75 x 31.5, body 10 tall, no screws (two buttons and a far ledge under the board, four lid posts on top), snap lid, knuckle and 15 mm wire opening on the same end, a 20.8 mm square opening in the floor so no PLA sits in front of the antenna, prints flat with no supports. Model checks: lid and board fit, every post reaches the board, clear of the fork at every tilt 0 to 90 degrees with the antenna toward the floor. Not yet printed.

### Changed
- Radar wiring in doc 02, `docs/wiring_guide.html` and the build guide moved from the LD2450 to the C4002: VIN to 5 V, GND, TX to GPIO16, RX to GPIO17, and OUT to GPIO33 as the wired backup trigger (the firmware already reads it: `sensor 4002` fires from it when the serial link is quiet for 1 s). Build guide also: parts list, pin map, protoboard pin for D33, header pins to solder, the radar card's pinout, and the mount step for the new case. Doc 02 records the three C4001 answers (PLA over the antenna, UART switch, address switch) and that the SEN0610 has no OUT pin. Firmware unchanged; `pio run` passes.

## 2026-10-08

### Changed
- `docs/handoff_sensor_bearings.md` rewritten as the work order for the sensor on hand: the DFRobot C4001 as `sensor 4001` (its 9600 baud `$DFDMD` text lines and plain-word commands, read from DFRobot's MIT library), with the C4002 as the second pass when it arrives and S1 to S5 written for both. The LD2450 design and why it was parked moved to `docs/retired/handoff_sensor_ld2450.md`; the inverted-install notes stay with the task. README doc map, CLAUDE.md, doc 03, doc 07 step 12 and roadmap line 4 point at the new shape. Firmware untouched.

## 2026-10-07

### Added

- C4002 radar firmware (`src/radar.cpp` rewritten, `machine.cpp`, `settings.cpp`, `console.cpp`, `web.cpp`): the DFRobot Fermion C4002 is the trigger. The firmware asks it to report every 0.1 s at boot, decodes its result frames (moving person's distance, speed, direction, still person's distance), and fires the drop when two readings in a row show someone approaching at `approach` cm/s or faster who would arrive within `leadms` (distance divided by speed), while armed and ready; the doorway is clear when nobody is within 3 m for 2 s. New settings `sensor` (4002 default, 2410 = OUT pin only), `approach` (30), `leadms` (750). If the serial link is silent for 1 s the fault is logged and the sensor's OUT pin on GPIO33 carries the trigger until frames return. Web radar card redrawn as a distance strip with the rule's red zone, readings, would-fire and doorway rows, 60 s timeline. Console: `radar`, `radar probe`, `radar version`, `radar range`, `radar out`, `radar reset`, `radar raw`, `radar baud`, `radar cmd r|w`. Protocol from DFRobot's MIT library (read, not linked: its receive blocks and cannot resync a stream). Builds on espressif32@6.7.0. NOT yet run on a sensor: the part is shipping; the result frame layout (20 data bytes, padded as the library reads it) and the direction word are checked on the bench (S1, S2). The LD2450 commands (`radar wake`, Hi-Link `radar cmd`) are gone with the parser.
- `radar wake` and `radar reset` console commands (`src/radar.cpp`): the first talks to the LD2450 over TX2 (version, tracking mode, area setting, end configuration, restart), the second puts its stored settings back to factory and restarts it. Written for a radar that is powered and silent; each step logs the reply bytes. Also `radar raw` (the last 96 bytes heard, as hex) and `radar baud` (find which speed the module answers at, set it back to 256000 if a firmware update moved it). And `radar cmd <hex>`: one protocol command by hand inside enable and end configuration, for bench experiments. Command frames from Hi-Link's operation manual and ESPHome's ld2450 component (protocol facts only, no code copied).

### Fixed
- Spider runaway on every downward move: closed. At the device the driver chip's logic supply turned out to be unconnected since the first build (the expansion board's V row, read 2.7 V by leakage through the signal wires, 1.8 mV with them off, against the chip's 3.0 V minimum); it is now fed from the ESP32's 3V3 pin. With that wire, the lock-after-every-move firmware of 2026-10-06, the standstill current cut switched off (switch 1 ON), Vref 0.935 V and `dropacc` 80000: one `jog -1600` came down one turn and held on the finger, and ten page drops each fell, held, wound back to the switch and locked, owner watching ("it all looks good"). Line length set to 1333 mm after the owner shortened the line. `docs/handoff_spider_runaway.md` retired. Which of the five changes carries how much weight was not separated. spreadCycle (20K at R7) left for later by the owner's word.
- V22 closed: the line stayed on the Rev C.4 spool through the same ten drops (owner: "no line came off"). `docs/handoff_spool_rev_c4.md` retired, roadmap line 3 removed.

### Changed
- Doc 02: the expansion board has no regulator; its V row is the driver's logic supply and must be fed from the ESP32's 3V3 pin. Found with a meter at the device: the row read 2.7 V by leakage through the signal wires and 1.8 mV with them off, against the chip's 3.0 V minimum. The audit carries it as the measured cause behind the runaway's up-down asymmetry. Doc 02 also records the switch mapping (switch 1 is the module's RX pin, switch 3 is MS1 and stays OFF). Wire NOT yet fitted; nothing tested under it.

## 2026-10-06

### Fixed
- Spider runaway on every downward move: audited (`docs/audit_spider_runaway.md`, Codex cold audit folded in). The motor lets go, not the chain: a dead stop at the switch in the driver's quiet mode leaves the TMC2209 in a state it cannot leave on its own (datasheet p42), the firmware never reset it, and the owner found the motor nearly free with the driver reported on. Firmware: every motor move now ends in a lock (finger in, seated, motor off); after a switch stop the finger goes in first, the driver is switched off and on with the finger in, then the 1/8 turn back-off seats the spool; a switch-cut unload resets the driver at the top; switching the driver on nudges one microstep so its standstill tuning runs at run current; a detached servo no longer counts as finger out; the lost-steps log line no longer names the stop as the cause. `dropacc` 80000 saved on the board (0.8 g, the spool rides the rod). Doc 04. Flashed over the network. NOT yet seen holding the spider: the jog -1600, switch-stop and ten-drop tests in the handoff are owed.

- Limit switch: two `rewind`s wound the spider up and on against the top, the switch never read, and the motor held it there powered. The switch now also has an interrupt, so one closure of any length stops the wind within 2 ms; after a stop the motor backs off until the switch opens (at most 6.5 mm) and holds without strain; a rewind that runs its full count with the switch fitted and never closed lets the spider down onto the finger, turns the motor off and stops on the fault at once (was three strikes, motor left holding). Each closure is logged and counted (`status`, the page). Doc 04. Flashed over the network, DEPLOYED; switch response with the spider NOT yet seen.

- Limit switch, inverted install: the bead flicks the flap as it passes and the flap falls back behind it, so the switch only blips (the interrupt catches it). A second `rewind` or up-`jog` right after the switch stopped one is now refused: twice it started above the flap and wound against the top. A switch stop or a full-count rewind now backs down 1/8 turn and holds with the motor on and the finger out; a stall stops on the fault and waits for `lock`. The motor never loses power before the finger holds (owner: the spider fell when it did). DEPLOYED.

### Added
- `radar probe` and a probe by itself 3 s after power-up when RX2 hears nothing: reads the free pins for the LD2450's signal and listens on whichever carries it (swapped wires handled). First run on the board: no signal on any free pin. Not yet seen finding a live signal.
- Radar card on the web page: live top-down map of the LD2450's targets with trails, door window and would-fire preview, a ripple per frame, and a 60 s timeline of people, trigger line, limit switch and motor. `radar` console command, `/api/radar`. Parser written to Hi-Link's manual (`src/radar.cpp`). Watch only: the drop is still fired by GPIO33. Drawn correctly against made-up walkers on the PC; the board has heard 0 bytes from the radar so far. Doc 04.

## 2026-10-05

### Changed
- `spool_cap.stl`: centre hole 11.0 (was 7.0), so spacer B passes through and bears on the one-way bearing's far end, never the cap (owner: the rod spacers touch the spool only at the bearing; he opened his printed cap's hole to 10 mm). The 606ZZ-side stack now fills 53.36: keep the C.3 stack, no shim out (0.36 play). Model checks pass, spacer B clear of the plastic even 0.35 off centre. Doc 01, doc 05 steps 1 and 9, handoff, cad/README. REPO-ONLY.
- Spool bearing hole: one plain 10.2 diameter from the shoulder through the far face with a 0.4 lead-in, no snap lip (owner: the C.3 lip printed too tight and he carved it out with a deburring tool; "the entire bushing should just be the narrower smaller diameter"); the screwed-on cap keeps the bearing in. `spool_onepiece_ribs.stl` (crush-rib hole) dropped: one spool STL. Owner's word for the HF0612 from now on: the one-way bearing. Doc 01, doc 05, build guide, cad/README.
- `fairlead_base_ptfe.stl` drawn without the lightening windows (owner: "faster print time > material usage"; 15.7 cm3, was 12.8). The rule is in CLAUDE.md: no windows, pockets or hollows to save filament unless a slice shows they cut print time. The installed `fairlead_base.stl` keeps its windows. Doc 09, doc 05 step 24b; `docs/img/ptfe_tube_path.png` shows the tube's path.
- `cad/generate.py` no longer writes any STL when run: it only checks. `python generate.py --export <part>` writes that part, and only if its geometry changed; `--export-all` is the full rebuild for `tools/regen_cad.ps1`. Every STL's file date set back to its last real change. `fairlead_flap_inv.stl` restored to the owner's own Fusion file (commit 94d2076), which a check run had overwritten on 2026-10-04. CLAUDE.md, cad/README.md.

## 2026-10-04

### Added
- `spool_cap.stl` (Rev C.4): the spool's far wall as a flat disc, r 32, 2.0 thick, 7 mm above the barrel and vertical (the C.3 one-piece's far wall was 2 mm tall and a 45 degree ramp, and the line came off over it onto the rod and spacer, owner). Three lugs drop into the spoke windows (owner 2026-10-05: keep them, they align the cap and hold the anchored thread in its window) and 3x M3x8 into pilots in the spokes clamp it (owner: a cap held only by the snug rod stack could lift up to the end play and a 0.29 mm thread would wedge in the crack). Prints outer face down, lugs up, no supports. REPO-ONLY.
- `fairlead_base_ptfe.stl` and the PTFE guide tube option (owner's idea): a 4 mm OD PTFE tube up through the base hole cuts the line's free span from 36 mm to 25 mm and sets the feed point square on the barrel; tip 11 mm above the base's inner face, 2 mm outside the cap. Trial first by wedging the tube in the plain block's tapered mouth; the ptfe block (straight 4.3 bore, tube cut 41 mm) only if it walks. Doc 09, doc 05 steps 24a and 24b. Model checks pass; REPO-ONLY.

### Changed
- `spool_onepiece.stl` to Rev C.4: separator 3.75 thick (was 1.5) so the 3.5 mm barrel runs z 43.25 to 46.75, centred on the line's feed point (z 45) with 1.75 to spare each side; the body ends flat at the barrel's far edge, 14.25 long (was 14.5 with the ramp and rim); line hole now at z 45.0. Bearing seat, shoulder, lip and teeth as C.3. Body plus cap 16.25, z 32.5 to 48.75. All model checks pass (finger clear slid 5 mm either way, finger seats 7.00 to 11.75 degrees, 2 mm swept clearance, stub clear, no supports). Not printed or benched. Doc 01, doc 05 section B, build guide.
- Stack for Rev C.4 on the owner's build: one `shim_2mm` out on the 606ZZ side against the C.3 stack (spacer B fills 51.25, was 53.0; 0.25 play); the 2026-10-04 stopgap (old `spool_shield` disc plus a 2 mm shift shim) comes out. Doc 05 step 9, build guide.
- Spool assembly order: the line is anchored through the printed hole with the filament stub BEFORE the cap goes on, because the cap closes the windows' far ends. Doc 05 section B.
- Line: bonded nylon upholstery thread, size 69 (Tex 70), black, 0.29 mm, 11 lb, about 22 percent stretch (owner; WAWAK spec), replacing 3 lb nylon monofilament, whose coil memory sprang loose wraps off the barrel. 2.2 m is 14 wraps, 1.2 layers on the barrel. Estimated peak if the motor loses grip, 30 g spider, full 0.7 m fall: near 11 N against a 49 N break; the thread is no longer a fuse below the anchors. CLAUDE.md, BOM, docs 01, 05, 06, 08 (V4), the firmware and sensor handoffs, build guide.
- Spider brought to about 30 g (owner: weight added inside the 13 g spider, so the wraps lie at about twice the tension); keep under 60 g until the bench says more. The 30 g and 60 g line-strength limits are gone. Docs 01, 05, 06, build guide.
- `cad/README.md`: spool lesson, files table and a checks row for the cap.
- Spare line: wind about 1.5 m under the working line (two drops' worth, owner), `line` set to the working length only. Doc 05 step 5, doc 06 heights.
- Line: 2 to 4 lb nylon monofilament, 3 lb in use (owner; was 6 lb, which he never had). Spider about 13 g (owner). Worst case if the motor loses grip, 13 g spider, full 0.7 m fall (estimate): 3 lb peaks near 4.1 N against a 13 N break. Spider limit now 30 g on 2 to 3 lb line, 60 g on 4 lb. CLAUDE.md, BOM, docs 01, 05, 06, 08, handoffs and build guide updated.

## 2026-10-02

### Added
- `spacer_A_nose_7_5mm.stl` (owner): motor-side spacer for the one-piece spool, 12 mm on the coupler with an 8 mm nose 1 mm long at the spool end, so it rubs close to the rod while the spool freewheels; replaces spacer A plus shims on the owner's build (6 + 4 less 2.5). The spool's motor-side hole is now 7.0 (was 8.5) so the nose bears on its face.
- Print table: spool parts at cross hatch 15% (were gyroid 40%); the spool is nearly all walls.
- `spool_onepiece.stl` (Rev C.3): ratchet, separator, barrel and flange as one part, no screws, 14.5 mm long (the owner's assembled stack measured 14.6), prints ratchet face down with no supports. Teeth 7 mm straight across the finger; separator r 28 and flange r 27, 1.4 mm or more inside the finger's reach, clear with the part slid 5 mm either way; finger seats (7.00 to 11.75 deg). HF0612 (owner measured 9.99 x 11.89) in a 10.2 hole held both ways: printed shoulder on the motor side, 9.9 snap lip at the flange face. `spool_onepiece_ribs.stl` has six crush ribs instead of the plain hole. Line hole printed in (teardrop, leaning the way the line wraps), 10 mm filament stub checked clear at every angle. Not yet printed or fitted; the three-part stack stays in service. Inverted checks unchanged.
- `finger.stl`: floor between the screw-head seat and the spline tip 3.5 mm (was 1.5; owner: too thin for the horn screw). Head recess now 3 mm deep, same 7.4 across; spline socket and finger position unchanged; same stepped bridging, no new overhang.
- `finger.stl`: hub onto the servo spline 2.5 mm shorter (owner), plate still 7 mm thick and the spline grip unchanged, so the finger sits 2.5 mm nearer the servo (z 32.5 to 39.5). Whatever spool is on the rod moves 2.5 mm toward the motor with it. No clashes; seats in a tooth gap.

## 2026-10-01

### Changed
- Firmware: the motor never turns with the finger in (owner rule). `jog` and `rewind` run the release first (finger out with the 1/12 turn unload) unless the finger is already out; the lock's seat move is the one exception. Flashed by WiFi; `jog 400` logged the finger going out first, then the move; `jog -400` with the finger already out went straight to the move.
- Line anchor: a 1 mm hole drilled through the barrel skin into a spoke window, line tied round a 10 mm stub of 1.75 mm filament inside, CA on the knot (was an arbor knot with CA, which can turn on the smooth barrel). Doc 05 step 5 and the build guide.
- Owner keeps the current spool stack; the one-piece spool handoff is now for later, with the bearing hole 0.1 smaller (10.2) and a built-in line anchor hole. Open item V21: the slip only shows above the spider's weight, so the limit switch must be on before arming.
- Inverted install turned end for end to match the owner's build (photo): servo end at the beam, pad end away from it. Radar fork moves to the pad end, 2x M3 drilled at x -80, z 38.5 and 72.5; nothing blocks its view, its centre line passes under the beam (409 mm below the ceiling), the cradle clears every part from 20 to 90 degrees. Line now 54 mm from the beam's face (was 117). Model, drilling template, install picture, doc 05, doc 06 and build guide updated.
- Driver pins: DIR GPIO27, STEP GPIO26, EN GPIO25 (were STEP 25, DIR 26, EN 27), so D27, D26, D25 match the expansion board's DIR, STEP, EN columns and a 3-wire ribbon goes straight across (owner). Firmware built; not yet flashed (board not connected). Doc 02, wiring guide, wiring picture and build guide updated; expansion board wires go on the S row, ground to any G, V empty.

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
