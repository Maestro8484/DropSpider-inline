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
