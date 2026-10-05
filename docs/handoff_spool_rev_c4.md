# Handoff: spool Rev C.4 on the bench, the line must stay on the spool

Print, fit and bench-test the Rev C.4 spool (`spool_onepiece` plus `spool_cap`), the bonded nylon thread and the 30 g spider, then close open item V22. For the owner (Joe) at the bench, with a session to log results and update docs.

## Ground truth first

This file is a work order, not a record. The repo on disk wins: `cad/generate.py` and `cad/inverted.py` are the source of truth for every dimension below, and doc 01 describes the design. If this file and the code disagree, the code is right and this file is stale; say so out loud. Staleness check:

```
git log -1 --oneline                                  # where the repo is now
git log -1 --oneline -- docs/handoff_spool_rev_c4.md  # when this file was last true
```

## Before you start

1. Run `cd cad; python generate.py`: every line of the one-piece spool and cap block must pass (cap flat on the body, screws pass and the pilots have their wall, feed point centred on the barrel, finger clear and seats, stub clear).
2. Run `cd cad; python inverted.py`: the PTFE guide tube block must pass (tube clear of the spool body and cap at every angle, line path clear).
3. Read open item V22 in `docs/08_open_items.md`: still open, waiting on the bench test below.

## Read first

1. `docs/01_mechanical_design.md`, section "Rev C.4 spool": parts, z table, cap, stack, line.
2. `docs/05_assembly.md`, section B (bearing, anchor the line before the cap, cap, wind), step 9 (stack), step 17 (spider), steps 24a and 24b (PTFE tube).
3. `docs/09_fairlead_switch.md`, the PTFE guide tube paragraph.

## The work, in order

1. **Print** `spool_onepiece.stl` (ratchet face down) and `spool_cap.stl` (line-side face down), both as exported, no supports. 3x M3x8 to hand. Slicer settings are Joe's.
2. **Assemble the spool** per doc 05 section B: HF0612 from the far face past the lip, direction check, line anchored through the printed hole with the filament stub BEFORE the cap, cap screwed on with 3x M3x8 and checked flat with no gap at the barrel's edge, wind clockwise seen from behind the motor under light hand tension.
3. **Stack:** against the C.3 stack, take one `shim_2mm` out on the 606ZZ side (0.25 mm of play left). If the 2026-10-04 stopgap is fitted (old `spool_shield` disc plus a 2 mm shift shim), both come out. Check edge-on that the teeth sit across the finger.
4. **Line and spider:** bonded nylon upholstery thread, size 69 (Tex 70), black; 2.2 m on the barrel (1.5 m spare under the working line). Spider brought to about 30 g with weight added inside it.
5. **PTFE guide tube, optional:** the wedge trial first, no print (doc 05 step 24a), tip 11 mm above the base's inner face. Print `fairlead_base_ptfe.stl` only if the wedged tube walks or wobbles (step 24b).
6. **Bench test** (below), logged in `docs/commissioning_log.md`.
7. **When it passes:** close V22 in `docs/08_open_items.md` (one line: date, what fixed it), one line in `CHANGELOG.md`, remove roadmap line 3, move this file to `docs/retired/` with its Retired line.
8. **If wraps still nest or climb:** the two held levers (owner 2026-10-04), each a design decision for Joe before any CAD: a deep-groove spool (44 mm barrel, so the motor-side wall is 6 mm; costs the firmware's `BARREL_DIA_MM` and moves the line 3 mm), or a slack take-up arm. If loose loops form on the spool during the drop or the bounce, that is slack reaching the spool: the spider stopped or bounced before the motor did (the one-way bearing stops the spool running on past the motor, so this is not a baitcaster backlash). That is a firmware matter (the stop rate `dropdec`, the hang time `settle`) for `docs/handoff_task1_firmware.md`, not this spool.

## Tests

- Bench, logged by Joe in `docs/commissioning_log.md`: 2.2 m of thread on (1.5 m spare), the 30 g spider, ten drops and rewinds. Pass: no wrap leaves the barrel.
- A phone slow-motion video of one drop. Pass: no loose loops on the spool during the drop or the bounce.
- Cap fit at assembly: screwed on, no gap at the barrel's edge anywhere round, and the spool still spins free by hand with the stack snug. Logged with the bench test.

## Done when

Ten drops and rewinds on the bench with no line off the spool, logged, and V22 closed.

## Rules for the session

- Make the parts and stop. Slicer settings are Joe's; deliver STLs only.
- Export only the changed STLs; no full rebuild, no mass picture regeneration.
- Every direction is seen from behind the motor.
- Decisions go to Joe as one flat numbered list, the question in bold on each item.
- Plain English, no em dashes, no arrows.
