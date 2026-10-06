# Handoff: spool Rev C.4 on the bench, the line must stay on the spool

Print, fit and bench-test the Rev C.4 spool (`spool_onepiece` plus `spool_cap`, 3x M3x8), the bonded nylon thread and the 30 g spider, then close open item V22. For the owner (Joe) at the bench, with a session to log results and update docs.

## Ground truth first

This file is a work order, not a record. The repo on disk wins: `cad/generate.py` and `cad/inverted.py` are the source of truth for every dimension below, and doc 01 describes the design. If this file and the code disagree, the code is right and this file is stale; say so out loud. Staleness check:

```
git log -1 --oneline                                  # where the repo is now
git log -1 --oneline -- docs/handoff_spool_rev_c4.md  # when this file was last true
```

## Rules that bit this week (read before touching anything)

- `python generate.py` only checks; it writes no STL. Export one part with `python generate.py --export spool_onepiece`. Never `--export-all`, never `regen_cad.ps1`, never touch `fairlead_flap_inv.stl` (the owner's own file). The owner reads STL file dates in File Explorer to know what to print.
- Print time beats material: no lightening windows or hollows unless a slice shows they cut time.
- The one-way bearing is called that, never HF0612, in anything the owner reads.
- Every direction is seen from behind the motor. Slicer settings are the owner's. Decisions to him as one flat numbered list, the question in bold on each item.

## Before you start

1. Read the newest rows of `docs/commissioning_log.md`: they say how the device is installed and what the board last reported.
2. Read the board now: `curl -s http://dropspider.local/api/status` (it is on the network, at 192.168.1.137 if the name does not answer). Note `home`, `limit`, `armed`, `fault`. If `home` is unknown, the first job is step 1 of the work below.
3. Ask Joe in one line which of these are true on the spool he has fitted, and log the answer: cap hole opened to about 11 mm; the bearing's steel rim stands higher than its cage; the C.3 stack kept (no shim out) and the spool spins free by hand; 2.2 m of bonded nylon thread on; spider about 30 g; PTFE tube wedged or not used. Anything not done is done before the drops.
4. Run `cd cad; python generate.py` and `python inverted.py`: the one-piece spool and cap block and the PTFE tube block must pass. They only print; they write nothing.
5. Read open item V22 in `docs/08_open_items.md`: still open, waiting on the bench test below.

## Read first

1. `docs/01_mechanical_design.md`, section "Rev C.4 spool": parts, z table, cap with lugs and screws, bearing hole, stack, line. Pictures `docs/img/spool_c4.png` and `spool_c3_vs_c4.png` (drawn before the lugs came back; the cap in them is right apart from the three small lugs).
2. `docs/05_assembly.md`, section B (bearing, anchor the line before the cap, lugs in, screw the cap on, wind), step 9 (stack), step 17 (spider), steps 24a and 24b (PTFE tube).
3. `docs/09_fairlead_switch.md`, the PTFE guide tube paragraph, and `docs/img/ptfe_tube_path.png`.

## What the owner found on the C.3 print (2026-10-05), already designed out

- The 9.9 snap lip at the far face of the bearing hole printed too tight; he carved it out with a deburring tool. His words: "the entire bushing should just be the narrower smaller diameter". C.4: one plain 10.2 hole from the shoulder through the far face, 0.4 lead-in, no lip; the press fit holds the bearing and spacer B bears on its far end. If the 10.2 hole itself prints tight, the one number is `OP_BORE` in `cad/generate.py`. The crush-rib variant is gone; there is one spool STL.
- A cap held only by the rod stack would lift up to the stack's end play and the 0.29 mm thread would wedge in the crack at the barrel's corner. C.4: three lugs 1.5 mm tall drop into the spoke windows (owner: keep them, they align the cap and hold the anchored thread in its window), then 3x M3x8 into pilots in the spokes clamp the seam shut; the stack stays snug, never tight, so the spool spins free when the clutch is unlocked.

- The rod spacers must touch the spool only at the bearing, never the plastic round it (owner 2026-10-05; he opened his printed cap's hole to 10 mm). C.4: the cap's centre hole is 11.0 (was 7.0), spacer B passes through and bears on the bearing's far end; spacer A's 8 mm nose already bears only inside the bearing's 10 mm, on the 2.25 mm shoulder the bearing sits on. The bearing pressed in with some force and fits tightly (owner), so `OP_BORE` stays 10.2.

## The work, in order

Commands go to the board over the network: `curl -s -X POST http://dropspider.local/api/cmd --data-urlencode "c=<command>"` (the same as typing it on the web page). Anything that moves the motor or the servo is sent only after Joe says in this conversation that he is at the device and the doorway is clear.

1. **Home it, only once the limit switch is proven:** on 2026-10-06 the switch never registered and two rewinds stalled the spider against the top (session "Spool limit switch safety" is changing the firmware's limit response). Before any rewind, Joe presses the flap by hand while status is read: `limit` must read 1 while held and 0 when let go. Then `rewind` (finger out first, winds up until the limit switch stops it), then `lock`. Read status after each: `home` known, `limit` 1 after the rewind, driver off and servo off after `lock`. If the rewind stops without the switch, stop and ask Joe what he saw.
2. **Fix anything from check 3 above** that is not done, per doc 05 section B and step 9. Printed cap with a 10 mm hole: open it to about 11 with the deburring tool. Cage standing proud of the rim: report it before the stack goes back on (spacer B would rub it).
3. **PTFE guide tube, optional:** the wedge trial first, no print (doc 05 step 24a), tip 11 mm above the base's inner face. Print `fairlead_base_ptfe.stl` (solid, no windows) only if the wedged tube walks or wobbles (step 24b).
4. **Bench test** (below): ten `drop` cycles, one at a time, status read after each (`drops` counts up, `fault` empty, `home` known after the rewind). Joe watches the spool; one row per drop in `docs/commissioning_log.md`, failures included.
5. **If a wrap leaves the barrel:** stop, log which drop and where the wrap went (over the cap, over the separator, onto the rod), and go to step 9 below.
6. **When it passes:** close V22 in `docs/08_open_items.md` (one line: date, what fixed it), one line in `CHANGELOG.md`, remove roadmap line 3, move this file to `docs/retired/` with its Retired line.
7. **If the bearing hole is wrong:** report the printed size and whether the bearing slipped or would not go; change `OP_BORE` only, export `spool_onepiece` only, note it in doc 01's table and cad/README's fit lesson.
8. **If wraps still nest or climb:** the two held levers (owner 2026-10-04), each a design decision for Joe before any CAD: a deep-groove spool (44 mm barrel, so the motor-side wall is 6 mm; costs the firmware's `BARREL_DIA_MM` and moves the line 3 mm), or a slack take-up arm. If loose loops form on the spool during the drop or the bounce, that is slack reaching the spool: the spider stopped or bounced before the motor did (the one-way bearing stops the spool running on past the motor, so this is not a baitcaster backlash). That is a firmware matter (the stop rate `dropdec`, the hang time `settle`) for `docs/handoff_task1_firmware.md`, not this spool.

## Tests

- Bench, logged by Joe in `docs/commissioning_log.md`: 2.2 m of thread on (1.5 m spare), the 30 g spider, ten drops and rewinds. Pass: no wrap leaves the barrel.
- A phone slow-motion video of one drop. Pass: no loose loops on the spool during the drop or the bounce.
- Cap fit at assembly: lugs drop in, screwed on, no gap at the barrel's edge anywhere round, and the spool still spins free by hand with the stack snug. Logged with the bench test.
- Bearing fit: pressed in by hand or light clamp, no carving (the press-in is logged); holds under more than the spider's weight. Logged with the bench test.

## Done when

Ten drops and rewinds on the bench with no line off the spool, logged, and V22 closed.

## Known stale, left on purpose

The build guide's exploded and cut-away pictures (`exploded.png`, `rod_section.png`) and the labels in `cad/render.py` still show the old three-plate stack and "3 lb line"; `spool_c4.png` and `spool_c3_vs_c4.png` show the cap without its lugs. Re-render only if the owner asks.
