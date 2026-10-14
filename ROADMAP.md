# Roadmap

Every piece of work still to do, in order. One line each; the handoff holds the detail. Finished work goes to `CHANGELOG.md`, problems and unknowns to `docs/08_open_items.md`, bench results to `docs/commissioning_log.md`. Rules for these files: the `repo-docs` standard in the owner's global Claude setup.

| # | Work | Whose | Status | Detail |
|---|---|---|---|---|
| 0 | Flash 11: page refinements, sleep by 5 presses, asleep LED, firmware version stamp; see each work on the board | session with the owner watching | next | `docs/handoff_flash11_page_sleep_led.md` |
| 0b | Publish: LICENSE, README and build guide in the owner's voice, doc map complete, BOM matched, clean-clone build; docs only, no code | docs session (Fable) | next, the license is the owner's call | `docs/handoff_publish.md` |
| 1 | Firmware: line between the spool and the flap is about 72 mm in the inverted install (fairlead v2) (firmware assumes 40); factory drop distance must fit the shorter line | team | next | `docs/handoff_task1_firmware.md` step 1 |
| 2 | Bench tests T1 to T8 of the Rev C.1 motor-led drop, with the mechanism assembled | team with the owner | next, needs the mechanism built | `docs/handoff_task1_firmware.md` |
| 3b | Build the inverted install: print `fairlead_base` and `fairlead_flap_inv` (fairlead v2), `ld2450_fork_screw`; drill the five base holes; braces and their holes | owner | any time; bench first | build guide sections 06 and 11, doc 06, open item V18 |
| 4 | Trigger sensor: the DFRobot C4002 as `sensor 4002`. On the bench 2026-10-10: talks, direction right, fired the drop twice. Left: foil behind it, learn the empty room, S3 count, S2 swing, S4, S5 wire pull, porch numbers | owner at the device with the session | in progress | `docs/handoff_sensor_bearings.md` |
| 5 | Hang it on the porch, walk tests, arm | owner with the team | waiting on 2, 3 and 4 | `docs/07_commissioning.md`, build guide section 12 |
| 6 | Calibrate card on the web page: walks the bench steps with Pass and Fail buttons (replaces the planned `test` console command) | team | later | build guide section 09, "Planned" |
| 7 | Enclosure for the controller board | owner | later | `docs/08_open_items.md`, Rev D candidates |
| 8 | Static IP address (DHCP only today) | team | later, only if the router moves it | `docs/08_open_items.md`, known limits |
| 9 | Spider position strip on the page: home, drop end, line end and the spider by the motor's count, labelled as such (owner 2026-10-14: "later") | team | later | `docs/audit_webui_horizon.md` approach 4 |
