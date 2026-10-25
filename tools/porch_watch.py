"""Live cycle watcher for the porch walk tests.

Streams the board's log as it happens and prints one plain line per event that
matters on a walk test: the trigger, how far away the sensor fired, the drop,
the rewind, any fault. Nothing is sent to the board; it only reads.

    python tools/porch_watch.py [host]        default 192.168.1.138
Double-click scripts/porch_watch.bat to run it in its own window; close the window to stop.
"""
import functools, json, sys, time, urllib.request

print = functools.partial(print, flush=True)

HOST = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.138"
KEEP = ("[cycle]", "[drop]", "[rewind]", "[fault", "[radar]", "[armed]", "[switch]", "[teach]", "[lock] seated", "[release]")


def get(path):
    with urllib.request.urlopen(f"http://{HOST}{path}", timeout=4) as r:
        return json.loads(r.read().decode())


def stamp():
    return time.strftime("%H:%M:%S")


def main():
    since = None
    last_fire = None
    print(f"watching {HOST} ... walk when ready (close the window to stop)")
    while True:
        try:
            s = get(f"/api/status?since={since if since is not None else 0}")
        except Exception as e:
            print(f"{stamp()}  board not answering ({e.__class__.__name__}), retrying")
            time.sleep(1.5)
            continue
        if since is None:
            st = s["settings"]
            print(f"{stamp()}  state {s['state']}, armed {s['armed']}, home {s['home']}, drops {s['drops']}, fault '{s['fault']}'")
            print(f"{stamp()}  drop {st['dropmm']} mm at {st['droprpm']} rpm | fire at {st['firecm']} cm, approach {st['approach']} cm/s, clear {st['clearcm']} cm")
            since = s["next"]
            time.sleep(0.4)
            continue
        for line in s["log"]:
            if not line.startswith(KEEP):
                continue
            print(f"{stamp()}  {line}")
            if line.startswith("[cycle] trigger: radar"):
                try:
                    r = get("/api/radar")["r"]
                    why = r.get("why")
                    if why and why != last_fire:
                        print(f"{stamp()}  FIRED AT: {why}")
                        last_fire = why
                except Exception:
                    pass
            if line.startswith("[cycle] done"):
                print(f"{stamp()}  ---- cycle {s['drops']} done, measured drop {s['measuredDrop']} mm, fault '{s['fault']}'")
        since = s["next"]
        time.sleep(0.4)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
