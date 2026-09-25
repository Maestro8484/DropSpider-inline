# 04 - Firmware

What the code does, how to load it, and every command it takes.

## Where it lives

Standard PlatformIO layout at the repo root. Board `nodemcu-32s` (38-pin ESP32-S NodeMCU), Arduino framework, platform pinned to `espressif32@6.7.0` (Arduino core 2.0.16).

| File | What |
|---|---|
| `platformio.ini` | board, pinned versions, USB port, network update target |
| `secrets.ini` | network name, network password, update password. Not in git. Copy `secrets.ini.example` |
| `include/config.h` | every pin and fixed number, and the factory defaults |
| `src/main.cpp` | start-up order only |
| `src/machine.cpp` | the cycle, stepper, finger servo, radar pin, BOOT button, limit switch |
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
| USB | double-click `scripts\update_firmware.bat` and pick 2. It builds, then asks you to put the board in flash mode (hold IO0, tap EN, let go of IO0) and writes it through `tools/esptool_noreset.py`. VS Code's plain Upload does not work on this board: its port open holds the chip in reset. Port is COM13 in the script and `platformio.ini` |
| Web page | open `http://dropspider.local/update`, log in as `admin` with the update password, pick `.pio/build/nodemcu-32s/firmware.bin` |

The 38-pin board on the bench does not enter flash mode on its own over USB. Its BOOT button is marked IO0.

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
| Status | state, chips (armed, spider home, radar, motor powered, fault), drop count, last trigger, last rewind, line length measured by the switch |
| Run | Drop it now, Arm or Disarm, Stop, Motor and servo off, Clear fault |
| Bench: finger servo | live angle, nudge 1 or 5 degrees, go to lock or release angle, store the current angle as lock or release |
| Bench: motor | jog one turn or 1/8 turn each way, Rewind, Lock, Release |
| Settings | every tunable, applied as you change it; Save settings keeps them after power loss |
| Console | the live log and a command box |
| Network | save a different home network and restart |
| Firmware | link to the update page |

## Cycle

```
READY (armed) --radar or BOOT button--> finger out (spider free-falls)
  --settle 1.5 s--> REWIND (stops the moment the limit switch closes; without the switch,
                    fixed steps + 0.75 turn overshoot and the bead stops on the eyelet)
  --> LOCK (finger in, motor off, spool settles onto a tooth, servo off)
  --> LOCKOUT 20 s --> WAIT FOR THE DOORWAY TO CLEAR (radar LOW for 2 s) --> READY
```

- Armed and ready: driver off, servo off. Only the ESP32 and the radar draw power.
- Boot: driver off first thing, finger to lock, never rewinds on its own. If the limit switch is fitted and open at boot, the page says the spider is not home; rewind and lock by hand.
- The machine runs on its own task, so console, page and network updates stay live during a cycle. `stop` works mid-rewind.

## Limit switch

A 3-pin endstop at the eyelet, pressed by the stop bead when the spider arrives home. Wiring in `02_electrical.md`.

- Off until you turn it on (`limit 1`), so an unwired or backwards switch cannot stop a rewind early. Check it reads right first: the page shows "reads pressed" or "reads open"; press the lever by hand and watch. If backwards: `liminv 1`.
- When on, it is a hard cut-off: any motor move in the rewind direction stops within a few milliseconds of the switch closing, in every state.
- Faults it catches, each a strike (three in a row and it stops arming until `clear` or a BOOT press):
  - trips in under a quarter of the expected rewind: line snagged or broke;
  - full rewind runs and it never trips: bead missed it, or it is unplugged;
  - still pressed right after a drop: wiring or `liminv` wrong. That rewind then runs on the step count alone.
- Each good rewind from a full drop that ends on the switch reports the measured line length, to check against `line`.

## Console commands

USB serial at 115200, the web page's Console card, or `tools/console.py`. Replies from either one show on both.

| Command | Does |
|---|---|
| `help`, `status` | list commands; show state, settings, sensor, limit switch, rewind steps |
| `arm`, `disarm` | let the radar fire it, or ignore the radar |
| `drop` | full cycle now (works when disarmed) |
| `rel` | finger out only: spider drops, no rewind |
| `rewind` | rewind only; motor stays on until `lock`; stops at the limit switch |
| `lock` | finger in, motor off, settle |
| `jog <n>` | move n microsteps (1600 = one turn), + = rewind direction, motor stays on. Refused winding in with the switch pressed |
| `servo <deg>` | move the finger live, to find angles; it holds there |
| `stop` | halt everything now, abort any cycle, leave the motor powered as it was |
| `off` | motor and servo off |
| `clear` | forget faults and re-arm the cycle |
| `setlock <deg>`, `setrel <deg>` | store finger angles (0 to 180) |
| `line <mm>` | braid length from the spool knot to the stop bead (100 to 3000) |
| `rpm <n>` | rewind speed, 30 to 600, default 240 |
| `dir <0/1>` | flip rewind direction |
| `settle <ms>`, `rearm <ms>` | hang time, lockout time |
| `limit <0/1>`, `liminv <0/1>` | limit switch fitted; switch reads backwards |
| `wifi` | where the board is on the network |
| `save`, `defaults` | write settings to flash; reload factory values (not saved) |

- Settings apply immediately; `save` keeps them through power loss. Bad values (out of range, not a whole number) are refused and nothing changes.
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

The 40 mm is braid that stays between spool and eyelet. The 0.75 turn overshoot guarantees the bead reaches the eyelet. With the limit switch on, the rewind stops at the switch instead; without it, the motor slips (skips steps, a short buzz, harmless at 0.6 A) for the rest.

Speed ramps up over 600 steps and down at the end of a counted move. A stop by the limit switch is instant, no ramp down.

## Known limits

- No stall detection: needs the driver's UART line, which the carrier does not expose.
- Radar UART pins (GPIO16, 17) are wired but unused. Future: read target distance directly instead of OUT.
- The update page and network upload use one shared password from `secrets.ini`. Fine on a home network; not for anything public.
- Static IP address: not yet.
