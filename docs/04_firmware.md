# 04 - Firmware

What the code does, how to load it, and every command it takes.

## Where it lives

Standard PlatformIO layout at the repo root. Board in use: 30-pin ESP32 DevKit V1 (PlatformIO board `nodemcu-32s`, same chip as the 38-pin NodeMCU-32S), Arduino framework, platform pinned to `espressif32@6.7.0` (Arduino core 2.0.16).

| File | What |
|---|---|
| `platformio.ini` | board, pinned versions, USB port, network update target |
| `secrets.ini` | network name, network password, update password. Not in git. Copy `secrets.ini.example` |
| `include/config.h` | every pin and fixed number, and the factory defaults |
| `src/main.cpp` | start-up order only |
| `src/machine.cpp` | the cycle, stepper, finger servo, trigger (radar rule or the OUT pin), BOOT button, limit switch |
| `src/console.cpp` | the text commands, shared by the USB console and the web page |
| `src/web.cpp` | WiFi, the web page, network firmware updates |
| `src/settings.cpp` | tunables saved in flash |

Libraries, both pinned in `platformio.ini`, both downloaded by PlatformIO on the first build:

| Library | Why this one |
|---|---|
| ESP32Servo 3.0.6 | servo pulses from the ESP32's own PWM hardware |
| FastAccelStepper 0.33.14 | step pulses from the ESP32's pulse hardware with speed ramps, so a rewind does not freeze the console or the web page. The Rev C handoff timed each pulse by hand and froze everything for 2 to 3 s |

WiFi, web server, mDNS (the `dropspider.local` name), ArduinoOTA (network upload) and Update (upload page) are all built into the ESP32 core. No other libraries.

## Load the firmware

First time on a new PC: install VS Code and its PlatformIO extension, copy `secrets.ini.example` to `secrets.ini` and fill it in, then open this folder in VS Code.

| Way | How |
|---|---|
| Network | board must be on the network already. Double-click `scripts\update_firmware.bat` and pick 1, or VS Code env `ota` and Upload. No buttons. It retries up to 3 times, because the first try sometimes drops |
| USB | double-click `scripts\update_firmware.bat` and pick 2. It builds and loads it; the 30-pin board goes into flash mode by itself. If a board does not (the first 38-pin board did not), the script asks you to hold BOOT (marked IO0 on some boards), tap EN, let go of BOOT, and writes through `tools/esptool_noreset.py`. Port is COM13 in the script and `platformio.ini` |
| Web page | open `http://dropspider.local/update`, log in as `admin` with the update password, pick `.pio/build/nodemcu-32s/firmware.bin` |

The 30-pin DevKit V1 in use enters flash mode on its own, so VS Code's plain Upload works too. The first 38-pin board did not.

Every network update switches the motor and servo off first. After any update the board restarts and, as always, does not rewind on its own.

## Network

- Joins the home network in `secrets.ini` by DHCP (the router hands out the address). Static address: not yet.
- A different network saved from the web page's Network card wins over `secrets.ini`. Save it empty to go back.
- If it cannot join in 15 s it makes its own network `DropSpider-setup` (password `dropspider`), page at `192.168.4.1`.
- Page at `http://dropspider.local` or at the address printed on the USB console at start-up (`wifi` command prints it again).

## The web page

The web page is the console on your phone or PC. Every button sends a console command, and the page's Console card shows everything the board prints, so the page and the USB console always agree.

| Card | What is on it |
|---|---|
| Status | state, chips (armed, spider home, trigger: radar rule or OUT pin on GPIO33, motor powered, fault), drop count, last trigger, last rewind, last drop as measured by the rewind, limit switch (open or closed, and closures counted since power-up) |
| Radar | the C4002's readings: chips (talking or silent, who is in view, would fire, OUT pin, direction word swapped), a distance strip with the moving person (dot, 4 s trail, arrow for the direction) and the still person, the red zone where the trigger rule passes at the current speed, the 3 m clear line, the sensor's own detect range as dashed lines, a ripple per frame; rows for distance, speed, direction (with the raw word), time to arrive, confidence, rule state (one reading or two in a row), doorway clear, light, the last drop the sensor fired and what it saw, the OUT pin, sensor software. Controls beside what they set: walking speed that fires (`approach`), fire distance (`firecm`), lead time (`leadms`), clear distance (`clearcm`), re-arm anyway after (`clearms`), direction reads backwards (`radarinv`), what fires the drop (`sensor`); the sensor's own detect range with Set and Read, range step, motion and presence sensitivity, how long it keeps a person, Learn the empty room, Save settings. A check line under them says how long the spider takes from the trigger to the bottom (measured on the last drop) and where a person walking at 100 cm/s, and at the speed seen now, is when it lands at the current fire distance. A 60 s timeline (nearest person, rule would fire, OUT pin, limit switch, motor). Show 3 m or 6 m, freeze |
| Run | Drop it now, Arm or Disarm, Stop, Motor and servo off, Clear and re-arm |
| Bench: finger servo | live angle, nudge 1 or 5 degrees, go to lock or release angle, store the current angle as lock or release |
| Bench: motor | jog one turn or 1/8 turn each way, Rewind, Lock, Release |
| Settings | every tunable, applied as you change it; Save settings keeps them after power loss |
| Console | the live log and a command box |
| Network | save a different home network and restart |
| Firmware | link to the update page |

## Cycle (Rev C.1, motor-led drop)

```
READY (armed) --radar or BOOT button-->
  RELEASE: driver on; finger swings out while the motor winds the spool up 1/12 turn (M2),
           wait relms (250 ms)
  DROP:    motor unwinds dropmm at up to droprpm, starting at dropacc and stopping at dropdec;
           the spool falls behind it on the clutch and can never pass it. Motor holds at the bottom
  --settle 1.5 s--> REWIND (stops the moment the limit switch closes; without the switch,
                    the drop + 0.75 turn overshoot and the bead stops on the eyelet)
  --> LOCK (finger in; seat move lets the spool down 1.2/12 turn at 30 rpm onto a tooth,
            the clutch slips once it lands; driver off; servo off 0.7 s later)
  --> LOCKOUT 20 s --> WAIT FOR THE DOORWAY TO CLEAR (nobody within 3 m, or OUT pin LOW, for 2 s) --> READY
```

- The driver is on from the release to the end of the lock. Never drop with the driver off: the unpowered motor drags too much for a clean fall.
- Armed and ready: driver off, servo off. Only the ESP32 and the radar draw power.
- Boot: driver off first thing, finger to lock, never rewinds on its own. See "Home at boot" below.
- The machine runs on its own task, so console, page and network updates stay live during a cycle. `stop` works mid-drop and mid-rewind.

## The drop's two rates

FastAccelStepper 0.33.14 has one acceleration value per move, not separate start and stop rates. It does recompute the stop when the acceleration is changed mid-move (`setAcceleration` then `applySpeedAcceleration`). So the drop starts at `dropacc`, and the machine task, every 2 ms, works out how far the stop at `dropdec` needs from the current speed. When the move gets that close, plus a margin of 10 ms of travel and 50 steps, it switches to `dropdec`. The margin matters: switched too late, the library overshoots the end and reverses back to it.

If `dropdec` is set equal to or above `dropacc`, no switch happens and the whole drop uses `dropacc`.

Unit check: one microstep = pi x 50 mm / 1600 = 0.098 mm of line. 1 m/s is about 610 rpm. 100000 steps/s^2 is about 1 g at the barrel.

Drop steps = dropmm / 0.098 mm + the steps the unload actually wound up. `dropmm` can never be set closer than 30 mm to the barrel knot (at most `line` - 70). If a smaller `line` is stored than the drop allows, the drop is cut to fit and says so in the log.

## Limit switch

A 3-pin endstop at the eyelet, pressed by the stop bead when the spider arrives home. Wiring in `02_electrical.md`.

- Off until you turn it on (`limit 1`), so an unwired or backwards switch cannot stop a rewind early. Check it reads right first: the page shows "reads pressed" or "reads open"; press the lever by hand and watch. If backwards: `liminv 1`.
- When on, it is a hard cut-off: any motor move in the rewind direction stops within 2 ms of the switch closing, in every state. An interrupt latches the first closure of any length, so a flap shaken by a stalled motor still stops it (2026-10-06: two rewinds wound on against the top with the switch never seen).
- Every motor move ends in a lock: finger in, the spool let down onto a tooth, motor off. After the switch stops a rewind or a jog, the finger goes in first, the driver is switched off and on again with the finger in (a dead stop in the driver's quiet mode can leave it in a state it cannot leave on its own, TMC2209 datasheet p42; the owner found the motor nearly free with the driver "on" after one, 2026-10-06), then the seat move is the 1/8 turn back-off (about 20 mm) so the bead rests clear of the flap and the eyelet. A plain lock seats 1.2/12 turn. The spider never hangs on the motor alone: every time it did on 2026-10-06 it ran the whole line. If the switch cuts the release's unload short, the driver is reset there, at the top, before anything moves down. `rel` is the one move that leaves the finger out, held by the powered servo, for the jog that follows.
- Switching the driver on from off: enable, one microstep up and back, then 200 ms still. The driver's standstill tuning needs the run current, and with the standstill current cut on (the expansion board's DIP 3 off) only a step pulse brings it back; the settle alone tuned at half current. A second rewind or up-jog straight after is refused: the bead flicks the flap as it passes, so from the top the switch is never seen. That includes the 1/12 turn unload at the release; if the switch cuts it short, the log says `unload cut short by the limit switch`.
- Faults it catches, each a strike (three in a row and it stops arming until `clear` or a BOOT press):
  - trips in under a quarter of the expected rewind: line snagged or broke;
  - full rewind runs and it never trips: bead missed it, or it is unplugged. The spider is then pulled hard against the top, so this one does not wait for three: the motor backs down 1/8 turn, locks, and stops on the fault. Send `clear` when it is fixed. The motor never loses power before the finger is holding (owner 2026-10-06). Same for a switch still pressed after a drop;
  - still pressed right after a drop: wiring or `liminv` wrong. That rewind then runs on the step count alone.
- Each cycle's rewind that ends on the switch reports how far the spider dropped, to check against `dropmm`.
- Lost steps on the stop: if that rewind runs more than 20 mm past the drop (allowing one unload for the seat), the log says `lost steps?`. It means the spool got ahead of the motor at the stop and the line's stretch caught the spider. Not a fault on its own; lower `dropdec` or `droprpm` if it repeats.

### Home at boot (V14)

After the lock seat the bead drops off the flap, so the switch reads open with the spider home. That is by design. The firmware remembers, in flash, that the last lock followed a rewind the switch stopped. At boot:

- switch pressed, or that memory says home: no message, ready;
- switch open and that memory says home: log `switch open, spider home from the last lock`, ready;
- switch open and home not known: the page says the spider is not home; rewind and lock by hand. Boot still never rewinds.

Any drop, release, jog, finger move, rewind start, or a stop part way through something forgets home until the next switch-stopped rewind and lock. `status` shows `home=yes` or `home=unknown`.

## Console commands

USB serial at 115200, the web page's Console card, or `tools/console.py`. Replies from either one show on both.

| Command | Does |
|---|---|
| `help`, `status` | list commands; show state, settings, sensor, limit switch, rewind steps |
| `arm`, `disarm` | let the radar fire it, or ignore the radar |
| `drop` | full cycle now (works when disarmed): unload and release, powered drop, settle, rewind, lock |
| `rel` | unload and release only (steps 1 to 3 of the drop): the motor winds up 1/12 turn while the finger swings out, then stays on holding the spider. `jog` lowers it; `off` lets it slide down on the motor's drag |
| `rewind` | rewind only, then locks (finger in, seated, motor off); stops at the limit switch |
| `lock` | finger in, seat move onto a tooth, motor off, servo off |
| `jog <n>` | move n microsteps (1600 = one turn), + = rewind direction, then locks (finger in, seated, motor off). Finger out first: unless the servo is powered and holding it at the release angle, the release runs (finger out with the 1/12 turn unload), then the jog. Refused winding in with the switch pressed |
| `servo <deg>` | move the finger live, to find angles; it holds there |
| `stop` | halt everything now, abort any cycle, leave the motor powered as it was |
| `off` | motor and servo off |
| `clear` | forget faults and re-arm the cycle; during the lockout or the wait for the doorway to clear, re-arm now (page button Clear and re-arm) |
| `setlock <deg>`, `setrel <deg>` | store finger angles (0 to 180) |
| `line <mm>` | line length from the barrel knot to the stop bead, line straight not pulled (100 to 3000). Refused if it would leave `dropmm` reaching the knot |
| `dropmm <mm>` | how far the spider drops, 100 to `line` - 70, default 620 |
| `droprpm <n>` | drop top speed, 100 to 900, default 500 |
| `dropacc <n>` | drop start rate, microsteps/s^2, 20000 to 400000, default 120000 |
| `dropdec <n>` | drop stop rate, 10000 to 200000, default 60000 (about 0.6 g). Keep low: the motor has to stop the spider |
| `relms <ms>` | finger travel time before the drop starts, 100 to 600, default 250 |
| `sensor <4002/2410>` | 4002 (default): the C4002 over serial fires the drop, its OUT pin on GPIO33 takes over if the serial link is silent for 1 s. 2410: the OUT pin only (any active-high sensor: LD2410C, PIR, step mat) |
| `approach <cm/s>` | the moving person must be coming closer at least this fast, 10 to 150, default 30 |
| `leadms <ms>` | fire when the person's distance divided by speed is under this, 200 to 2000, default 750 |
| `firecm <cm>` | fire when someone approaching at `approach` or faster is within this straight-line distance from the sensor, 0 to 1100, default 120; 0 = off. The owner's rule (2026-10-10, "less timed and more proximity-based"): on a 2 m overhead mount the lead-time rule could not fire at a slow pace. The page's card says where the person is when the spider lands at the current number |
| `clearcm <cm>` | the doorway counts as clear, and the device re-arms, when nobody moving reads closer than this for 2 s, 50 to 1100, default 300. Was fixed at 300 until the office bench, where a screen at 2.2 m held it. Since 2026-10-11 a still reading never holds it: it cannot fire the rule, and on the bench one at 25 to 70 cm held the device 44 s |
| `clearms <ms>` | re-arm anyway after waiting this long for the doorway to clear, 0 to 600000, default 30000; 0 = wait for clear. Safe because the rule still wants a fresh approach to fire (owner 2026-10-11: "a better self-resetting clear fault function") |
| `radarinv <0/1>` | 1 = the radar's direction word reads backwards on this mount: approaching and away are swapped before the rule. Bench 2026-10-10: the word is right as built (2 = approaching), so this stays 0; it is there for a mount that reads otherwise |
| `rpm <n>` | rewind speed, 30 to 600, default 240 |
| `dir <0/1>` | flip rewind direction |
| `settle <ms>`, `rearm <ms>` | hang time, lockout time |
| `limit <0/1>`, `liminv <0/1>` | limit switch fitted; switch reads backwards |
| `wifi` | where the board is on the network |
| `radar` | what the C4002 sees now: frames a second, bad frames, version, detect range, the moving person (distance, speed, direction, time to arrive), the still person, and whether the trigger rule passes. "no result frames yet" with 0 bytes means nothing is arriving on RX2 (GPIO16) |
| `radar probe` | watch every free pin for 0.4 s and say which one carries the sensor's signal; listen there if it is not RX2 |
| `radar version` | ask the sensor its software and hardware version |
| `radar range [closest farthest]` | read the sensor's own detect range, or set it, in cm, 0 to 1100, then restart the sensor so it takes (bench 2026-10-10: without the restart the old range stays). Kept in the sensor, rounded to its range step. Set the closest value past the hanging spider if it ever reads it (at rest it did not, 2026-10-10). Refused while a move is running |
| `radar res [80/20]` | the sensor's range step (DFRobot "resolution mode"): 80 cm steps to 11.6 m, or 20 cm steps to 4.9 m. 20 lets a close cut-off land where it is set. Kept in the sensor |
| `radar sens motion\|presence [low/mid/high]` | the sensor's own sensitivity for the moving reading and the still reading (DFRobot threshold groups). Lower motion if a pet or the swinging spider fires it, lower presence if furniture or a screen holds the doorway busy. Kept in the sensor; ships mid and mid |
| `radar delay [s]` | how long the sensor keeps reporting a person after it last saw one (DFRobot "target disappear delay"). Ships at 15 s, which held the doorway busy; set to 2 on the bench. Kept in the sensor |
| `radar calib <delay s> <listen s>` | the sensor learns the empty room (DFRobot "environment calibration"): waits, then listens with nobody in view and sets its own per-step thresholds, which then show as sensitivity "custom". It counts down in the log every 5 s and on the page as a chip. The page's button does 10 s then 30 s |
| `radar out [1/2/3]` | read or set what the OUT pin goes high on: 1 motion, 2 presence, 3 either. Kept in the sensor |
| `radar reset` | the sensor's factory settings, then a restart; the firmware asks it to report again 1.5 s later. Refused while a move is running |
| `radar raw` | the last 96 bytes heard on RX2 as hex, oldest first: FA F5 AA A5 starts a packet; its 8th byte 04 = a result, 02 or 03 = a reply |
| `radar baud` | try a detect-range read at each speed the sensor knows (115200 first, then 57600, 230400, 460800, 500000, 921600, 1000000); if it answers at another speed, set it back to 115200 and restart it |
| `radar cmd r|w <cmd> [hex]` | one DFRobot protocol command by hand, r = read request, w = write request, command byte then data bytes, the reply logged as hex. Bench experiments only. Known commands: 82 version (data 01 software, 00 hardware), 83 report period in tenths of a second, 86 detect range, A0 OUT pin rule, 21 speed, 00 restart, 02 then 80 factory reset |
| `save`, `defaults` | write settings to flash; reload factory values (not saved) |

- Settings apply immediately; `save` keeps them through power loss. Bad values (out of range, not a whole number) are refused and nothing changes. `dir`, `rpm` and the drop settings are refused while the motor runs.
- **The motor never turns with the finger in** (owner 2026-10-01). `jog` and `rewind` swing the finger out first, with the 1/12 turn unload, unless it is already out; a drop releases before it unwinds. The one exception is the lock's seat move, which lets the spool down onto the finger on purpose.
- Any bench motion (`rel`, `lock`, `rewind`, `jog`, `servo`, `stop`, `off`) disarms the radar so nothing fires with hands in the frame. Send `arm` when done.
- Motion commands are refused while a cycle runs; `stop` and `off` always work.
- Each motion command ends with a `[done] ...` or `refused: ...` line. `tools/console.py` waits for it.

## tools/console.py

Sends commands and prints the replies, then exits. Needs pyserial (`tools/requirements.txt`).

```
python tools/console.py COM13 status "jog 1600"
python tools/console.py dropspider.local status
python tools/console.py COM13 --listen 10
```

Opening the port does not reset the board.

## Rewind math

steps = ((line - 40 mm) / (pi x 50 mm) + 0.75 turn) x 200 x 8

In a cycle the rewind is the drop's steps + 0.75 turn instead, if that is less: the spool is only down as far as the drop went.

The 40 mm is line that stays between spool and eyelet. The 0.75 turn overshoot guarantees the bead reaches the eyelet. With the limit switch on, the rewind stops at the switch instead; without it, the motor slips (skips steps, a short buzz, harmless at 0.6 A) for the rest.

Speed ramps up over 600 steps and down at the end of a counted move. A stop by the limit switch is instant, no ramp down.

## Known limits

- No stall detection: needs the driver's UART line, which the expansion board does not expose.
- The C4002 reports one moving and one still person, not several: two people walking in together read as one. Its result frame layout (18 data bytes, packed) is taken from DFRobot's code, not a protocol sheet: the Python port and the ESPHome component decode it byte by byte that way, the Arduino library copies the bytes over a padded C struct (20) and the ESPHome component has that copy commented out. The firmware logs the count it sees at the first frame; 18 is right, anything else means `radar raw` and a look. Not yet seen on a real sensor.
- The direction word: DFRobot's two code enums say 0 away, 1 none, 2 approaching; its Home Assistant tutorial yaml says 0 approaching, 2 away. The firmware follows the code; `radarinv 1` (the page's "Direction reads backwards" tick) swaps it if the walk test says otherwise.
- The report-period command is sent 1.5 s after boot and again every 5 s while no result frames arrive, so a sensor that boots slower than the board, or loses power on its own, still comes up without a restart. Whether the sensor keeps its period through a power cut is not known.
- The update page and network upload use one shared password from `secrets.ini`. Fine on a home network; not for anything public.
- Static IP address: not yet.
