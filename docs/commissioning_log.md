# Commissioning log

Every bench and install result, in order. One row per attempt, failures included. Steps refer to `07_commissioning.md`; open items to `08_open_items.md`.

| Date | Step | Result | Value set | Evidence |
|---|---|---|---|---|
| 2026-09-24 | build | PASS | platform espressif32@6.7.0, board nodemcu-32s | `pio run` SUCCESS, 46% flash, 17% RAM, no warnings in project code |
| 2026-09-24 | board check (V12) | NOT DONE | - | COM13 = Silicon Labs CP210x USB chip. esptool could not put the chip in flash mode ("Wrong boot mode detected (0x13)"), twice. Needs BOOT held |
