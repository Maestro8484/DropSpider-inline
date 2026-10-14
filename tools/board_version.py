"""Ask the board which firmware it runs and compare with this checkout.

    python tools/board_version.py              asks dropspider.local
    python tools/board_version.py 192.168.1.138

Prints the board's FW_VERSION (from /api/status) beside the version this
checkout would build (tools/fw_version.py). scripts/update_firmware.bat runs
it after a WiFi update so the flash reports itself. Exit code 0 when they
match, 1 when they differ, 2 when the board does not answer.
"""
import json
import sys
import time
import urllib.request

import fw_version

host = sys.argv[1] if len(sys.argv) > 1 else "dropspider.local"
local = fw_version.version()
board = None
for attempt in range(6):
    try:
        with urllib.request.urlopen(f"http://{host}/api/status", timeout=5) as r:
            s = json.load(r)
        board = s.get("fw", "older than fw-11 (no fw field)")
        up = s.get("uptime", 0) // 1000
        print(f"Board at {host}: firmware {board}, up {up} s, state {s.get('state')}, armed {s.get('armed')}, home {s.get('home')}")
        break
    except Exception as e:
        if attempt == 5:
            print(f"Board at {host} did not answer: {e}")
            sys.exit(2)
        time.sleep(10)

print(f"This checkout builds: {local}")
if board == local:
    print("MATCH: the board runs this checkout.")
    sys.exit(0)
print("DIFFERENT: the board does not run this checkout (a star means uncommitted firmware edits).")
sys.exit(1)
