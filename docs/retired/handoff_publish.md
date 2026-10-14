# Handoff: make the repo publishable, in the owner's voice, touching no code

**Retired 2026-10-14, done:** LICENSE in place, README and build guide in the owner's voice, doc map complete, BOM matched, `scripts\check_repo.bat` option 2 ALL PASS. Record: `CHANGELOG.md` 2026-10-14, `docs/commissioning_log.md`. The push to GitHub is the owner's own click.

Work order: bring this repo to the state where a stranger can clone it, read it, print it, wire it, build the firmware and flash it from the build guide alone, with the README and build guide written in the owner's voice. A docs-only session: it edits `README.md`, `docs/`, `cad/README.md`, `bom/`, a `LICENSE`, and nothing under `src/`, `include/`, `cad/*.py`, `tools/` or `scripts/`. If a check needs a code change, it writes one line in `docs/08_open_items.md` and moves on.

**Ground truth:** the repo on disk wins over this file. Staleness check: `git log -1 --oneline` against `git log -1 --oneline -- docs/handoff_publish.md`; a different hash means work landed after this was written, read `CHANGELOG.md` for it.

## Before you start (checks to run now, not recorded facts)

- `python tools/check_repo.py` runs and prints a PASS or FAIL list. Its FAIL lines are the first half of this task list; rerun it after every fix.
- `git status` is clean apart from `cad/stl/DropSpider-inline-v3-invert.3mf` and anything another live session holds (`.git/claude-sessions/` lists live sessions). Stage by name only.
- The owner has answered the license question (item 1 below). If not, do everything else and leave the LICENSE file for last.

## Read first

1. `README.md` top to bottom: it is the front door and the doc map, and it is the file most in need of the owner's voice.
2. `docs/build_guide/build_guide.src.html` sections 01 to 12 (the source; `tools/make_build_guide.py` builds the single-file page from it).
3. `CHANGELOG.md` 2026-10-13 and 2026-10-14, for what changed since the README was last rewritten.
4. The owner's voice: his words quoted in `CLAUDE.md`, `docs/08_open_items.md` and the bench log. Short, direct, maker terms kept (firmware, flashed, mmWave), no software-process words, no hedging.

## The work, in order

1. **LICENSE** at the root, the license the owner picked (see Rules). One file, standard text, his name and the year. Then the README's one-line "License" section.
2. **check_repo FAIL lines:** every doc under `docs/` on the README map with its role (the two audits as **reference**, the flash 11 handoff as **handoff**); retired names out of current docs (`docs/09_fairlead_switch.md` line 3 names the retired line guide part by its STL name); handoff lines the checker flags as finished-work words reworded as checks to run now. Rerun until the only FAIL left is one the owner owns.
3. **README rewrite in the owner's voice.** Keep the shape (what it is, how it works, repo map, build in N steps, status). Fix what is stale: the sensor is the DFRobot C4002, not the LD2450; the install the owner is building is inverted on the porch beam; the handoff rows for `handoff_spool_rev_c4.md` and `M1_fix_handoff.md` point where those files now live. Add: the firmware version scheme in two lines (`docs/04_firmware.md`, "Firmware version"), the repo check (`scripts\check_repo.bat`), and a "Printing" line that the STLs are the deliverable and the `.3mf` files are the owner's own slicer projects.
4. **Build guide, complete from a fresh PC.** Walk sections 01 to 12 of `build_guide.src.html` against the current docs and add what a stranger lacks: install VS Code and PlatformIO, clone, copy `secrets.ini.example` to `secrets.ini`, double-click `scripts\update_firmware.bat`; the version the board then reports; the inverted install as the primary install, the ceiling one second; the sleep and rehome switch presses; the page as it is now (reply strips, bottom bar, Last cycles, Save bar). Rebuild the page with `python tools/make_build_guide.py` and open `docs/build_guide/build_guide.html` in the browser pane to read it through once.
5. **BOM:** `bom/BOM.csv` lines match the parts the guide names (the C4002 in, the LD2450 marked parked or out, the size 69 thread, the KW12-3, the steel corner braces for the inverted install). No prices invented; a part with no known source gets "owner's stock".
6. **Pictures:** every image the README and guide reference exists in `docs/img` and shows the current parts (the C4002 case and swivel mount, the inverted install). A stale picture is listed in `docs/08_open_items.md` for a CAD session; this session regenerates none.
7. **Clean-clone build, automated:** `scripts\check_repo.bat` option 2 (docs, then `pio run`) ends ALL PASS, with the LICENSE in place and no star on the version. Log the result.
8. **Close:** one changelog line under Added for the publish pass, this file to `docs/retired/` with its Retired line, the roadmap line dropped. The push to GitHub is the owner's own click, not this session's: say the repo is ready and stop.

## Tests

| Step | Pass mark | Logged in |
|---|---|---|
| 2, 7 | `python tools/check_repo.py --build` prints ALL PASS | `docs/commissioning_log.md`, one row |
| 3 | README read aloud sounds like the owner; no sentence the checker or the changelog contradicts | reviewer's eye, the owner's one-line yes |
| 4 | a reader with the guide alone reaches a flashed board reporting its version | the owner's one-line yes after reading the guide |
| 5 | every part named in the guide is a BOM line and the reverse | same row as 2 |

## Done when

`scripts\check_repo.bat` option 2 ends ALL PASS, the README and build guide read in the owner's voice and describe the device as it is, and the owner has said the repo may be pushed.

## Rules for the session

- No code. `src/`, `include/`, `cad/*.py`, `tools/`, `scripts/` stay untouched; a needed code change is one line in `docs/08_open_items.md`.
- The license is the owner's choice and his name goes on it. Advised, not decided: MIT for the firmware and tools, CC BY 4.0 for the docs, pictures and CAD (`cad/c4002_case.py` credits a CC BY-NC-SA MakerWorld layout, so that part's share-alike terms are named in the LICENSE file). If he says one license for everything, MIT for all of it with the CC BY-NC-SA credit kept.
- His voice, his words where he has said them; never a sentence that reads as written by an assistant. No em dashes, arrows, emojis or curly quotes anywhere in the repo's prose.
- Stage by name; another session may be live. Never commit `secrets.ini`. Never push.
- Reports: verdict first, short, plain English.
