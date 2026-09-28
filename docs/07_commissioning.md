# 07 - Commissioning (bench first, then installed)

Do every step on the bench, device base-down, spool hanging over the table edge so the line can drop about 0.7 m. Each step has a pass condition; do not go on until it passes. Record every result in `commissioning_log.md`.

Commands can be typed in three places, all equivalent: the web page's Console card (`http://dropspider.local`), the USB serial console at 115200, or `python tools/console.py COM13 <command>`. The web page's buttons send the same commands.

Step numbers 1 to 14 are unchanged from Rev C so the open-items table still points at the right step. Steps 3a and 3b are new. Rev C.1 changed steps 7, 8 and 10 for the motor-led drop; the full new test list T1 to T8 is in `M1_fix_handoff.md`.

| # | Do | Pass |
|---|---|---|
| 1 | 12 V on, nothing else connected: meter the buck output | 4.95 to 5.05 V |
| 2 | Motor unplugged: meter TMC2209 Vref (pot top to GND) | 0.85 V |
| 3 | Everything wired except the motor. Power up. | Console prints `ready`, `status` shows sensor 0 with nobody near |
| 3a | Open `http://dropspider.local` on a phone or PC on the same network (or the address `wifi` prints) | Page loads, state reads "ready" or "waiting for the doorway to clear", the Console card shows the log |
| 3b | Limit switch wired, `limit` still 0. Press its lever by hand, then let go, watching the status chips | Chip reads "reads pressed" while held and "reads open" when let go. If backwards: `liminv 1`. Then `limit 1`, `save` |
| 4 | Power off, plug in the motor, power on. `jog 1600` then `jog -1600` | One smooth turn each way (**V1 logic-level check**) |
| 5 | `off`. `servo 90`, then `servo 30` (or the nudge buttons) | Finger level in the teeth at 90, clear of the teeth toward the floor side at 30. Adjust with `servo <n>` until true; `setlock` / `setrel` the values (or Store as lock / Store as release), then `save` |
| 6 | With line wound and finger at lock, pull the spider down by hand | Spool does not turn; finger pressed onto the ledge, not bending the servo |
| 7 | `rel` (Rev C.1: motor on, winds about 1/12 turn while the finger swings out), then `drop` | `rel`: finger clears the teeth with no servo buzz. `drop`: motor spins, spider falls fast and stops at the set height, short of the line's end (no bounce off the end) |
| 8 | `rewind` | Spool winds the line up. If the motor turns but the spool does not (clutch slipping): `off`, `dir 0` (or 1) and repeat. If neither direction winds, the HF0612 is in the Rev C direction: flip it (05 step 4) |
| 9 | Watch the end of `rewind` | With the switch on: the bead lifts the fairlead flap, the switch clicks, the motor stops at once, no buzz; console says "stopped by the limit switch". With the switch off: the flap bottoms on the fairlead, motor buzzes briefly (skipping), then stops |
| 10 | `lock` | Finger goes in, motor eases the spool down onto a tooth, motor goes off, spider drops no more than about 13 mm and stays. The flap drops back and the switch reads open: correct by design (doc 09, V14) |
| 11 | `line <measured mm>`, `save`, then `drop` five times | All five complete, no tangles, finger always relocks. With the switch on, "Line length measured by the switch" on the page is within about 40 mm of `line` |
| 12 | `arm`, `save`. Walk toward the door from 3 m away, then walk away, then walk across the hallway | Fires only when walking toward the door, spider arriving as you reach the doorway. LD2450 tests S1 to S5 in `handoff_sensor_bearings.md` |
| 13 | Stand still in front of it after a scare | No second scare until you leave and 20 s pass |
| 14 | Hardware check after 20 cycles | Coupler set screws tight, no white stress marks on the finger or ledge, knot intact, flap swings freely on its pin, switch roller not bent, no groove worn in the fairlead bore |

Bench motion commands disarm the radar on purpose. Step 12 re-arms it.

Then mount per `06_installation.md` and repeat steps 11 to 13 in place, adjusting `line` for the resting height.

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| Motor buzzes, no turn | one coil reversed | swap black and green |
| Motor erratic or silent but holding | 3.3 V logic into 5 V driver | add the 74AHCT125 buffer (see 02) |
| Drop is slow or stutters | motor losing steps at `droprpm`, or spool rubbing a spacer | lower `droprpm`; check end play; lighter spider |
| Spider slams at the bottom | motor lost its grip while stopping | lower `dropdec`; lighter spider |
| Finger will not release, servo buzzes | tooth pinning the finger (M2) | release must run with the motor winding; check the unload move in the log |
| Spider drops at power-up | finger not seating at boot, or servo on GPIO14 | check `setlock`; servo must be on GPIO13 |
| Finger will not relock | lock angle short of the teeth | raise `setlock` a few degrees |
| Line tangles on the spool | line exits the wrong side, or slack on rewind | re-wind per 05 step 16; reduce `rpm` |
| Retriggers on people walking past or leaving | LD2450 window too wide, or running the LD2410C fallback | narrow `doorwidth`, raise `approach`; check `sensor 2450` |
| ESP32 resets when servo moves | 5 V dips | fit the 470 uF capacitor at the servo |
| Rewind stops early, fault "tripped far too early" | line snagged, or switch noise from the motor wires | clear the snag; route the switch lead away from the motor wires |
| Fault "ran without the limit switch tripping" | bead misses the flap, flap stuck, or switch unplugged | check the flap swings freely and the roller touches its tail (doc 09 step 4); check `status` shows the switch changing when the flap is lifted |
| Fault "still pressed after a drop" | switch reads backwards | `liminv` the other way, `save` |
| `jog` refused, "limit switch is pressed" | spider already home, or switch reads backwards | check 3b |
| Page will not load | board not on the network | USB console `wifi`; if it made its own network, join DropSpider-setup and use 192.168.4.1 |
| USB upload stops at "Connecting" | board not entering flash mode | hold BOOT, tap EN, let go of BOOT, upload again |
