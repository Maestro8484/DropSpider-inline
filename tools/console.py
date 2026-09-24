"""Send console commands to the DropSpider board and print the replies.

Non-interactive: runs each command in turn, waits for its answer, then exits.
Works over the USB cable or over the network.

    python tools/console.py COM13 status "jog 1600"
    python tools/console.py dropspider.local status
    python tools/console.py COM13 --listen 10          just print what the board says for 10 s

Motion commands (drop, rel, lock, rewind, jog, servo, off, stop, clear) wait for
the board's "[done]" or "refused" line, up to --timeout seconds. Everything else
waits until the board goes quiet.

Opening the USB port does not reset the board: DTR and RTS are held off.
Built on pyserial (serial port) and the Python standard library (network).
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request

MOTION = {"drop", "rel", "lock", "rewind", "jog", "servo", "off", "stop", "clear"}


def is_done(line):
    return line.startswith("[done]") or line.startswith("refused")


def run_serial(port, commands, timeout, quiet, listen):
    import serial

    ser = serial.Serial()
    ser.port = port
    ser.baudrate = 115200
    ser.timeout = 0.05
    ser.dtr = False          # held off before open so the board is not reset
    ser.rts = False
    ser.open()
    buf = b""

    def lines_for(seconds_quiet, deadline, want_done):
        nonlocal buf
        last = time.time()
        seen_done = False
        while time.time() < deadline:
            chunk = ser.read(512)
            if chunk:
                buf += chunk
                last = time.time()
                while b"\n" in buf:
                    raw, buf = buf.split(b"\n", 1)
                    line = raw.decode("utf-8", "replace").rstrip("\r")
                    print(line, flush=True)
                    if want_done and is_done(line):
                        seen_done = True
            if seen_done and time.time() - last > quiet:
                return True
            if not want_done and time.time() - last > seconds_quiet:
                return True
        return not want_done

    try:
        if listen:
            lines_for(listen + 1, time.time() + listen, False)
            return 0
        ser.reset_input_buffer()
        ok = True
        for cmd in commands:
            ser.write((cmd + "\n").encode())
            want = cmd.split()[0].lower() in MOTION
            if not lines_for(quiet, time.time() + (timeout if want else max(quiet * 4, 3)), want):
                print(f"[console.py] no [done] for '{cmd}' within {timeout} s", flush=True)
                ok = False
        return 0 if ok else 1
    finally:
        ser.close()


def run_http(host, commands, timeout, quiet, listen):
    base = f"http://{host}"

    def status(since):
        with urllib.request.urlopen(f"{base}/api/status?since={since}", timeout=5) as r:
            return json.loads(r.read())

    since = status(0)["next"]
    end = time.time() + listen if listen else None
    ok = True
    for cmd in commands or [None]:
        want = False
        if cmd:
            data = urllib.parse.urlencode({"c": cmd}).encode()
            urllib.request.urlopen(urllib.request.Request(f"{base}/api/cmd", data=data), timeout=5).read()
            want = cmd.split()[0].lower() in MOTION
        deadline = end or time.time() + (timeout if want else 2)
        done = not want
        while time.time() < deadline:
            s = status(since)
            since = s["next"]
            for line in s["log"]:
                print(line, flush=True)
                if want and is_done(line):
                    done = True
            if cmd and done and not s["log"]:
                break
            time.sleep(quiet / 2)
        if not done:
            print(f"[console.py] no [done] for '{cmd}' within {timeout} s", flush=True)
            ok = False
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="COM port (COM13) or network name (dropspider.local or an IP)")
    ap.add_argument("commands", nargs="*", help="console commands, quote ones with spaces")
    ap.add_argument("--timeout", type=float, default=30, help="seconds to wait for a motion command to finish")
    ap.add_argument("--quiet", type=float, default=0.6, help="seconds of silence that mean the reply is over")
    ap.add_argument("--listen", type=float, default=0, help="just print the board's output for this many seconds")
    a = ap.parse_args()
    if not a.commands and not a.listen:
        a.commands = ["status"]
    if a.target.upper().startswith("COM") or a.target.startswith("/dev/"):
        sys.exit(run_serial(a.target, a.commands, a.timeout, a.quiet, a.listen))
    sys.exit(run_http(a.target, a.commands, a.timeout, a.quiet, a.listen))


if __name__ == "__main__":
    main()
