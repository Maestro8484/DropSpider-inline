# 07 - Commissioning (bench first, then ceiling)

Do every step on the bench, device base-down, spool hanging over the table edge so the line can drop about 0.7 m. Each step has a pass condition; do not go on until it passes. Record every result in `commissioning_log.md`.

Commands can be typed in three places, all equivalent: the web page's Console card (`http://dropspider.local`), the USB serial console at 115200, or `python tools/console.py COM13 <command>`. The web page's buttons send the same commands.

Step numbers 1 to 14 are unchanged from Rev C so the open-items table still points at the right step. Steps 3a and 3b are new.

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
| 7 | `rel` | Spider free-falls the full length, snubber stretches, bounces. Motor shaft does not turn |
| 8 | `rewind` | Spool winds the line up. If it turns the wrong way (clutch just slips): `off`, `dir 0` (or 1) and repeat |
| 9 | Watch the end of `rewind` | With the switch on: motor stops the moment the bead presses the switch, no buzz; console says "stopped by the limit switch". With the switch off: bead reaches the eyelet, motor buzzes briefly (skipping), then stops |
| 10 | `lock` | Finger goes in, motor goes off, spider drops no more than about 13 mm and stays |
| 11 | `line <measured mm>`, `save`, then `drop` five times | All five complete, no tangles, finger always relocks. With the switch on, "Line length measured by the switch" on the page is within about 40 mm of `line` |
| 12 | `arm`, `save`. Walk up to the sensor from 3 m away | Triggers between 0.75 and 1.5 m (tune gates in the app) |
| 13 | Stand still in front of it after a scare | No second scare until you leave and 20 s pass |
| 14 | Hardware check after 20 cycles | Coupler set screws tight, no white stress marks on the finger or ledge, knot intact, limit switch lever not bent |

Bench motion commands disarm the radar on purpose. Step 12 re-arms it.

Then mount per `06_installation.md` and repeat steps 11 to 13 in place, adjusting `line` for the resting height.

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| Motor buzzes, no turn | one coil reversed | swap black and green |
| Motor erratic or silent but holding | 3.3 V logic into 5 V driver | add the 74AHCT125 buffer (see 02) |
| Spool will not free-fall | HF0612 backwards, or spool rubbing a spacer | flip bearing; check end play |
| Spider drops at power-up | finger not seating at boot, or servo on GPIO14 | check `setlock`; servo must be on GPIO13 |
| Finger will not relock | lock angle short of the teeth | raise `setlock` a few degrees |
| Line tangles on the spool | line exits the wrong side, or slack on rewind | re-wind per 05 step 16; reduce `rpm` |
| Retriggers on people behind a wall | radar range too long | lower max gates, raise gate 1 and 2 thresholds |
| ESP32 resets when servo moves | 5 V dips | fit the 470 uF capacitor at the servo |
| Rewind stops early, fault "tripped far too early" | line snagged, or switch noise from the motor wires | clear the snag; route the switch lead away from the motor wires |
| Fault "ran without the limit switch tripping" | bead misses the lever, or switch unplugged | adjust the switch position; check `status` shows it changing when pressed |
| Fault "still pressed after a drop" | switch reads backwards | `liminv` the other way, `save` |
| `jog` refused, "limit switch is pressed" | spider already home, or switch reads backwards | check 3b |
| Page will not load | board not on the network | USB console `wifi`; if it made its own network, join DropSpider-setup and use 192.168.4.1 |
| USB upload stops at "Connecting" | board not entering flash mode | hold BOOT, tap EN, let go of BOOT, upload again |
