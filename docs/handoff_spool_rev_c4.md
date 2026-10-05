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

1. Run `cd cad; python generate.py`: every line of the one-piece spool and cap block must pass (lugs drop in and the cap sits flat, screws pass and the pilots have their wall, bearing hole plain with no lip, feed point centred on the barrel, finger clear and seats, stub clear).
2. Run `cd cad; python inverted.py`: the PTFE guide tube block must pass (tube clear of the spool body and cap at every angle, fits the ptfe block, line path clear).
3. Read open item V22 in `docs/08_open_items.md`: still open, waiting on the bench test below.

## Read first

1. `docs/01_mechanical_design.md`, section "Rev C.4 spool": parts, z table, cap with lugs and screws, bearing hole, stack, line. Pictures `docs/img/spool_c4.png` and `spool_c3_vs_c4.png` (drawn before the lugs came back; the cap in them is right apart from the three small lugs).
2. `docs/05_assembly.md`, section B (bearing, anchor the line before the cap, lugs in, screw the cap on, wind), step 9 (stack), step 17 (spider), steps 24a and 24b (PTFE tube).
3. `docs/09_fairlead_switch.md`, the PTFE guide tube paragraph, and `docs/img/ptfe_tube_path.png`.

## What the owner found on the C.3 print (2026-10-05), already designed out

- The 9.9 snap lip at the far face of the bearing hole printed too tight; he carved it out with a deburring tool. His words: "the entire bushing should just be the narrower smaller diameter". C.4: one plain 10.2 hole from the shoulder through the far face, 0.4 lead-in, no lip; the press fit holds the bearing and spacer B bears on its far end. If the 10.2 hole itself prints tight, the one number is `OP_BORE` in `cad/generate.py`. The crush-rib variant is gone; there is one spool STL.
- A cap held only by the rod stack would lift up to the stack's end play and the 0.29 mm thread would wedge in the crack at the barrel's corner. C.4: three lugs 1.5 mm tall drop into the spoke windows (owner: keep them, they align the cap and hold the anchored thread in its window), then 3x M3x8 into pilots in the spokes clamp the seam shut; the stack stays snug, never tight, so the spool spins free when the clutch is unlocked.

- The rod spacers must touch the spool only at the bearing, never the plastic round it (owner 2026-10-05; he opened his printed cap's hole to 10 mm). C.4: the cap's centre hole is 11.0 (was 7.0), spacer B passes through and bears on the bearing's far end; spacer A's 8 mm nose already bears only inside the bearing's 10 mm, on the 2.25 mm shoulder the bearing sits on. The bearing pressed in with some force and fits tightly (owner), so `OP_BORE` stays 10.2.

## The work, in order

1. **Print** `spool_onepiece.stl` (ratchet face down) and `spool_cap.stl` (outer face down, lugs up), both as exported, no supports. 3x M3x8 to hand (the C.2 stack's screws).
2. **Assemble the spool** per doc 05 section B: one-way bearing from the far face until it stops on the shoulder (plain hole, no lip), direction check, line anchored through the printed hole with the filament stub BEFORE the cap, cap lugs into the windows (a file stroke on a lug's side if one will not go), 3x M3x8 in, cap checked flat with no gap at the barrel's edge anywhere round, wind clockwise seen from behind the motor under light hand tension.
3. **Stack:** keep the C.3 stack as it is, no shim out: spacer B passes through the cap's 11 mm hole onto the bearing's far end (0.36 mm of play). Owner's printed cap: hole opened to 10 mm by hand; open it to about 11 so spacer B cannot touch it. Look first that the bearing's steel rim stands higher than its cage. If the 2026-10-04 stopgap is fitted (old `spool_shield` disc plus a 2 mm shift shim), both come out. Check edge-on that the teeth sit across the finger, and that the spool still spins free by hand.
4. **Line and spider:** bonded nylon upholstery thread, size 69 (Tex 70), black; 2.2 m on the barrel (1.5 m spare under the working line). Spider brought to about 30 g with weight added inside it.
5. **PTFE guide tube, optional:** the wedge trial first, no print (doc 05 step 24a), tip 11 mm above the base's inner face. Print `fairlead_base_ptfe.stl` (solid, no windows) only if the wedged tube walks or wobbles (step 24b).
6. **Bench test** (below), logged in `docs/commissioning_log.md`.
7. **When it passes:** close V22 in `docs/08_open_items.md` (one line: date, what fixed it), one line in `CHANGELOG.md`, remove roadmap line 3, move this file to `docs/retired/` with its Retired line.
8. **If the bearing hole is wrong:** report the printed size and whether the bearing slipped or would not go; change `OP_BORE` only, export `spool_onepiece` only, note it in doc 01's table and cad/README's fit lesson.
9. **If wraps still nest or climb:** the two held levers (owner 2026-10-04), each a design decision for Joe before any CAD: a deep-groove spool (44 mm barrel, so the motor-side wall is 6 mm; costs the firmware's `BARREL_DIA_MM` and moves the line 3 mm), or a slack take-up arm. If loose loops form on the spool during the drop or the bounce, that is slack reaching the spool: the spider stopped or bounced before the motor did (the one-way bearing stops the spool running on past the motor, so this is not a baitcaster backlash). That is a firmware matter (the stop rate `dropdec`, the hang time `settle`) for `docs/handoff_task1_firmware.md`, not this spool.

## Tests

- Bench, logged by Joe in `docs/commissioning_log.md`: 2.2 m of thread on (1.5 m spare), the 30 g spider, ten drops and rewinds. Pass: no wrap leaves the barrel.
- A phone slow-motion video of one drop. Pass: no loose loops on the spool during the drop or the bounce.
- Cap fit at assembly: lugs drop in, screwed on, no gap at the barrel's edge anywhere round, and the spool still spins free by hand with the stack snug. Logged with the bench test.
- Bearing fit: pressed in by hand or light clamp, no carving; holds under more than the spider's weight. Logged with the bench test.

## Done when

Ten drops and rewinds on the bench with no line off the spool, logged, and V22 closed.

## Known stale, left on purpose

The build guide's exploded and cut-away pictures (`exploded.png`, `rod_section.png`) and the labels in `cad/render.py` still show the old three-plate stack and "3 lb line"; `spool_c4.png` and `spool_c3_vs_c4.png` show the cap without its lugs. Re-render only if the owner asks.
