# Roadmap

Every piece of work still to do, in order. One line each; the handoff holds the detail. Finished work goes to `CHANGELOG.md`, problems and unknowns to `docs/08_open_items.md`, bench results to `docs/commissioning_log.md`. Rules for these files: the `repo-docs` standard in the owner's global Claude setup.

| # | Work | Whose | Status | Detail |
|---|---|---|---|---|
| 1 | Firmware: line between the spool and the flap is about 72 mm in the inverted install (fairlead v2) (firmware assumes 40); factory drop distance must fit the shorter line | team | next | `docs/handoff_task1_firmware.md` step 1 |
| 2 | Bench tests T1 to T8 of the Rev C.1 motor-led drop, with the mechanism assembled | team with the owner | next, needs the mechanism built | `docs/handoff_task1_firmware.md` |
| 3 | One-piece spool and ratchet: no supports, bearing hole that grips (the HF0612 slips a bit), separator inside the finger's reach (the finger caught the shield and was cut back) | team with the owner | later: the owner keeps the current stack (2026-10-01) | `docs/handoff_spool_onepiece.md` |
| 3b | Build the inverted install: print `fairlead_base` and `fairlead_flap_inv` (fairlead v2), `ld2450_fork_screw`; drill the five base holes; braces and their holes | owner | any time; bench first | build guide sections 06 and 11, doc 06, open item V18 |
| 4 | LD2450 radar as the trigger, including the spider-in-view problem; tests S1 to S5 | team | waiting on T1 to T8 | `docs/handoff_sensor_bearings.md` |
| 5 | Hang it on the porch, walk tests, arm | owner with the team | waiting on 2, 3 and 4 | `docs/07_commissioning.md`, build guide section 12 |
| 6 | Calibrate card on the web page: walks the bench steps with Pass and Fail buttons (replaces the planned `test` console command) | team | later | build guide section 09, "Planned" |
| 7 | Enclosure for the controller board | owner | later | `docs/08_open_items.md`, Rev D candidates |
| 8 | Static IP address (DHCP only today) | team | later, only if the router moves it | `docs/08_open_items.md`, known limits |
