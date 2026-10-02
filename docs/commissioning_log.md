# Commissioning log

Every bench and install result, in order. One row per attempt, failures included. Steps refer to `07_commissioning.md`; open items to `08_open_items.md`.

| Date | Step | Result | Value set | Evidence |
|---|---|---|---|---|
| 2026-09-24 | build | PASS | platform espressif32@6.7.0, board nodemcu-32s | `pio run` SUCCESS, 46% flash, 17% RAM, no warnings in project code |
| 2026-09-24 | board check (V12) | NOT DONE | - | COM13 = Silicon Labs CP210x USB chip. esptool could not put the chip in flash mode ("Wrong boot mode detected (0x13)"), twice. Needs BOOT held |
| 2026-09-25 | board check (V12) | PASS | - | Board put in flash mode by hand (hold IO0, tap EN, let go of IO0). esptool through `tools/esptool_noreset.py`: ESP32-D0WD-V3 rev 3.1, dual core, 4 MB flash, MAC d4:e9:f4:64:e1:1c. The normal esptool port open held the chip in reset, which is why the 2026-09-24 tries failed |
| 2026-09-25 | USB flash | PASS | Rev C firmware (pre C.1) | 904144 bytes written, hash verified, restarted by RTS |
| 2026-09-25 | 3 | PASS | - | `status` over USB: state ready, sensor 0, driver off, servo off. What is wired to the board was not recorded |
| 2026-09-25 | 3a (V11 part) | PASS | DHCP | Joined MAINFRAME007 at 192.168.1.16; `http://dropspider.local/api/status` answered from the bench PC. Network firmware update not tried yet |
| 2026-09-25 | V11 network update | PASS | - | `pio run -e ota -t upload` to dropspider.local: 88 s, "Result: OK". Board back on the network 27 s later, uptime reset, state ready. No button presses needed |
| 2026-09-25 | update script, WiFi | PASS | - | `scripts/update_firmware.bat wifi`: first run failed at the upload (no retry then), next runs "Result: OK" in about 28 s. Retry added: up to 3 tries. USB path not yet run |
| 2026-09-25 | first new board | FAIL | - | First replacement board on COM13 (probably the same 30-pin model, not confirmed): USB chip seen, ESP32 silent on every try (no boot message on EN, no flash-mode reply). Set aside; likely faulty |
| 2026-09-25 | board swap to 30-pin DevKit V1 (V12) | PASS | - | esptool: ESP32-D0WD-V3 rev 3.0, 4 MB flash, MAC 3c:e9:0e:88:82:b8. Enters flash mode by itself: plain `pio run -t upload` and `scripts/update_firmware.bat usb` both flashed it, hash verified. Pin names checked against Joe's photo |
| 2026-09-25 | 3, 3a | PASS | DHCP | `status` over USB: ready. Joined MAINFRAME007 at 192.168.1.138; dropspider.local answers |
| 2026-09-25 | V11 on the 30-pin board | PASS | - | `scripts/update_firmware.bat wifi`: first try, "Result: OK" in 30 s; back on the network at 192.168.1.138, uptime reset, state ready |
| 2026-09-27 | build, Rev C.1 firmware (task 1) | PASS | - | `pio run` SUCCESS, 45.9% flash, 17.1% RAM, no warnings in project code. Motor-led drop, unload on release (M2), seat move on lock, V14 home memory, new settings dropmm, droprpm, dropacc, dropdec, relms |
| 2026-09-27 | network update, Rev C.1 | NOT DONE | - | Board not reachable: `dropspider.local` did not resolve, 192.168.1.138 did not answer, no COM13 on the PC. Board off or unplugged |
| 2026-09-27 | network update, Rev C.1 | PASS | - | Board powered, no motor or servo connected. `pio run -e ota -t upload`: "Result: OK" in 35 s. Board back at 192.168.1.138, boot line "Rev C.1 ready", all 15 settings at defaults incl. dropmm 620, droprpm 500, dropacc 120000, dropdec 60000, relms 250; `help` prints in full; home=unknown (limit not fitted). No USB port showed on the PC, so the USB path was not used
| 2026-09-27 | T1 to T8 | NOT RUN | - | waiting on the Rev C.1 flash |
| 2026-09-27 | V17 servo type | PASS | - | `servo 90`, `servo 30`, `servo 150`, nothing on the spline: owner saw it move and hold (positioning servo, not 360). Strained against its own stop at 150, switched off. Owner calls it an MG90 with about a 90 degree sweep |
| 2026-09-27 | 5, finger angles | SET | setlock 85, setrel 50, saved | Owner, on the bench with the finger on the spline: 85 = finger level, resting on the stop block; 50 = release, his call. Ratchet not on the rod, so clearance of the teeth not yet seen; T3 checks it |
| 2026-10-01 | network update, new driver pins | PASS | - | DIR 27, STEP 26, EN 25. `pio run -e ota -t upload` SUCCESS in 56 s; board back on 192.168.1.137, uptime 27 s at the first status read |
| 2026-10-01 | 4, V1 logic level (motor) | PASS | - | Driver pot 0.825 V (owner's meter). `jog 1600` twice from the web page: owner saw one smooth turn each time. `jog -1600` sent over the network: log `[jog] ran -1600 steps`, no fault (turn back not watched by the session). No buffer needed |
