"""Firmware version stamp, read from git at build time.

PlatformIO runs this through the build_flags line in platformio.ini
(build_flags = !python tools/fw_version.py) and takes what it prints as
compiler flags. It prints one define, FW_VERSION, which the firmware shows
in the boot log, the console status line, /api/status and the web page.

The version scheme: every build that reaches the board gets a git tag fw-N
(fw-9, fw-10, ...), N being the flash count the bench log has used all along.
A build between tags reads fw-10+3.f6a9849: three commits past fw-10, at
commit f6a9849. A trailing star means the firmware files (src, include,
platformio.ini, secrets.ini.example) have edits not yet committed, so the
build is not reproducible from any commit.

Run by hand to see the stamp:  python tools/fw_version.py --show
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FW_PATHS = ["src", "include", "platformio.ini", "secrets.ini.example"]


def git(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return ""


def version():
    desc = git("describe", "--tags", "--long", "--always", "--match", "fw-*")
    if not desc:
        return "unknown"
    # fw-10-3-gf6a9849  ->  fw-10+3.f6a9849 ;  f6a9849 alone when no tag exists yet
    parts = desc.rsplit("-", 2)
    if len(parts) == 3 and parts[2].startswith("g"):
        tag, ahead, sha = parts[0], parts[1], parts[2][1:]
        v = tag if ahead == "0" else f"{tag}+{ahead}.{sha}"
    else:
        v = "untagged." + desc
    if git("status", "--porcelain", "--", *FW_PATHS):
        v += "*"
    return v


if __name__ == "__main__":
    v = version()
    if "--show" in sys.argv:
        print(v)
    else:
        print(f'-D FW_VERSION=\\"{v}\\"')
