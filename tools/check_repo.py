"""Repo health check: is this repo ready for someone else to clone and build?

    python tools/check_repo.py            the document and file checks, a few seconds
    python tools/check_repo.py --build    the same, then a full firmware build (pio run)

Or double-click scripts/check_repo.bat. Every check prints PASS or FAIL with
the file and line it is about. Exit code 1 when anything fails.

What it checks:
  secrets      secrets.ini is not tracked by git; secrets.ini.example is
  license      a LICENSE file exists at the root
  doc map      every file in docs/ (not docs/retired, docs/img, docs/build_guide)
               is named in the README repo map
  handoffs     every docs/handoff_*.md has a ROADMAP.md line, every roadmap
               handoff link exists, and no handoff carries finished-work words
  links        every relative markdown link in *.md (root, docs/) points at a
               file that exists
  stl          every .stl name written in docs/ or README exists in cad/stl
  version      tools/fw_version.py prints a version; a star means uncommitted
               firmware edits
  build        (--build only) pio run ends in SUCCESS
"""
import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
fails = 0


def report(ok, what, detail=""):
    global fails
    print(("PASS  " if ok else "FAIL  ") + what + (": " + detail if detail else ""))
    if not ok:
        fails += 1


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def read(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


# secrets
tracked = git("ls-files").split("\n")
report("secrets.ini" not in tracked, "secrets: secrets.ini is not tracked by git")
report("secrets.ini.example" in tracked, "secrets: secrets.ini.example is tracked")

# license
report(bool(glob.glob("LICENSE*")), "license: a LICENSE file exists at the root",
       "" if glob.glob("LICENSE*") else "none found; the owner picks the license")

# doc map
readme = read("README.md")
for p in sorted(glob.glob("docs/*.md")):
    name = p.replace("\\", "/")
    report(name in readme or "`" + name.split("/")[-1] in readme, "doc map: " + name + " is named in README.md")

# handoffs
roadmap = read("ROADMAP.md")
finished_words = re.compile(r"(where it stands|state facts|\bcompleted\b|\bwas changed\b|\[x\]|\bpassed on\b|\bverified on\b)", re.I)
for p in sorted(glob.glob("docs/handoff_*.md")):
    name = p.replace("\\", "/")
    report(name in roadmap, "handoffs: " + name + " has a ROADMAP.md line")
    hits = [i + 1 for i, line in enumerate(read(p).splitlines()) if finished_words.search(line)]
    report(not hits, "handoffs: " + name + " holds future work only",
           "" if not hits else "finished-work words on lines " + ", ".join(map(str, hits)))
for m in re.finditer(r"`(docs/handoff_[^`]+\.md)`", roadmap):
    report(os.path.exists(m.group(1)), "handoffs: roadmap link " + m.group(1) + " exists")

# links
link = re.compile(r"\[[^\]]*\]\(([^)\s#]+)(?:#[^)]*)?\)")
for p in sorted(glob.glob("*.md") + glob.glob("docs/*.md")):
    base = os.path.dirname(p)
    for i, line in enumerate(read(p).splitlines()):
        for m in link.finditer(line):
            t = m.group(1)
            if re.match(r"[a-z]+:", t):
                continue
            target = os.path.normpath(os.path.join(base, t))
            report(os.path.exists(target), "links: " + p + " line " + str(i + 1) + " -> " + t)

# stl names
have = {os.path.basename(s) for s in glob.glob("cad/stl/*.stl")}
for p in sorted(["README.md"] + glob.glob("docs/*.md")):
    if p.endswith("commissioning_log.md"):
        continue   # history: old rows name parts that have since been retired
    for i, line in enumerate(read(p).splitlines()):
        for name in set(re.findall(r"`([A-Za-z0-9_.-]+\.stl)`", line)):
            report(name in have, "stl: " + p + " line " + str(i + 1) + " names " + name)

# version
v = subprocess.run([sys.executable, "tools/fw_version.py", "--show"], capture_output=True, text=True).stdout.strip()
report(bool(v) and v != "unknown", "version: tools/fw_version.py prints a version", v)
report(not v.endswith("*"), "version: firmware files are all committed", v)

# build
if "--build" in sys.argv:
    pio = os.path.expanduser("~/.platformio/penv/Scripts/pio.exe")
    if not os.path.exists(pio):
        pio = "pio"
    r = subprocess.run([pio, "run"], capture_output=True, text=True)
    report(r.returncode == 0 and "SUCCESS" in r.stdout, "build: pio run",
           (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else "")

print()
print("ALL PASS" if fails == 0 else str(fails) + " FAIL")
sys.exit(1 if fails else 0)
