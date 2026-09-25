"""Run esptool with the USB serial control lines held off.

Why: on the 38-pin NodeMCU on the bench, esptool's normal port open asserts
RTS, which holds the ESP32 in reset (EN low), so a board already put in flash
mode by hand (hold BOOT, tap EN, let go of BOOT) never answers. This opens the
port with DTR and RTS off, then hands every argument to esptool unchanged.

    python tools/esptool_noreset.py --port COM13 --before no_reset --after no_reset flash_id

esptool is the one PlatformIO ships (tool-esptoolpy); nothing else is installed.
"""
import os
import sys

import serial

ESPTOOL = os.path.join(os.path.expanduser("~"), ".platformio", "packages", "tool-esptoolpy")
sys.path.insert(0, ESPTOOL)

_orig = serial.serial_for_url


def _quiet_open(url, *args, **kwargs):
    kwargs["do_not_open"] = True
    port = _orig(url, *args, **kwargs)
    port.dtr = False
    port.rts = False
    port.open()
    return port


serial.serial_for_url = _quiet_open

import esptool  # noqa: E402

if __name__ == "__main__":
    esptool._main()
