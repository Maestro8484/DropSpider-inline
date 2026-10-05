# Handoff: one-piece spool and ratchet (Rev C.3), print and fit

**Retired 2026-10-04, superseded by `docs/handoff_spool_rev_c4.md`:** the one-piece was printed and the line came off its 2 mm far wall.

The part is designed and exported (`cad/stl/spool_onepiece.stl`, plus `spool_onepiece_ribs.stl` with a crush-rib bearing hole); what is left is printing it, fitting it on the bench, and retiring the three-part stack. The design and its z table are in `docs/01_mechanical_design.md` under "Rev C.3 one-piece spool"; the code is `spool_onepiece()` in `cad/generate.py`. For a session working with the owner (Joe).

## Ground truth first

This file is a work order, not a record. The repo on disk wins: `cad/generate.py` is the source of truth for every dimension. If this file and the code disagree, the code is right and this file is stale; say so out loud. Staleness check:

```
git log -1 --oneline                                   # where the repo is now
git log -1 --oneline -- docs/handoff_spool_onepiece.md # when this file was last true
```

## Before you start

1. Run `cd cad; python generate.py` and read the "one-piece spool" block at the end of the report: every line must pass (no CLASH, seats in a tooth gap, separator clear when slid 5 mm either way, 0.00 mm2 steeper than 45 degrees, line hole open, stub clear).
2. **Finger.** Print a fresh `finger.stl` (2026-10-02: hub 2.5 mm shorter, plate still 7). The new spool is checked against it, uncut.

## The work, in order

1. **Joe prints `spool_onepiece.stl`**, as exported (ratchet face on the bed). Slicer settings are his.
2. **Bearing.** Press the HF0612 in by vise from the flange face, past the snap lip, until it stops on the shoulder (it ends 0.6 below the flange face, under the lip). Lock direction as doc 05 step 4: free clockwise, locked counterclockwise, seen from behind the motor. If the plain 10.2 hole needs sanding to go in, print `spool_onepiece_ribs.stl` instead (10.4 hole, six ribs 0.2 high reaching to 10.0, rib size from AON3D's engineering fits guide).
3. **Line.** Through the printed hole from outside, out of the window's open end at the flange face, tied round a 10 mm stub of 1.75 mm filament, stub pulled back across the hole. Check a 1 mm drill passes the hole; turn it through by hand if the hole printed shut.
4. **Stack.** Motor side: `spacer_A_nose_7_5mm` alone, nose to the spool (replaces spacer A and its 4 mm shim). 606ZZ side: spacer B plus 2.5 mm more shim than now (7.5 mm in all on the 2026-09-29 build), a 12 mm shim against the flange first. Check edge-on that the teeth sit across the finger's 7 mm, and that the stack is snug, not tight.
5. **Bench test, logged by Joe in `docs/commissioning_log.md`:** the HF0612 does not turn in the hole under a hand twist against the lock; spool free clockwise, locked counterclockwise with the rod held; the finger drops into the teeth at the lock angle with no catching.
6. **Then retire.** Move `spool_ratchet`, `spool_shield`, `spool_body` (functions and STLs) to `cad/retired/` with "Retired, superseded by spool_onepiece"; point `assembly()` at the new part (model: spacer A 2.5, spacer B 53); update doc 01's stack and print tables, doc 05 section B (no screws, the anchor hole is printed, not drilled), the build guide's spool steps and the pictures they use; delete this file's finished steps or move it to `docs/retired/`.

## Done when

The new spool is on the rod, the bearing holds, a fresh finger engages with no catching, and the docs describe the one-piece spool only.

## Rules for the session

- Make the part and stop. Slicer settings are Joe's.
- Export only the changed STL; no full rebuild, no mass picture regeneration unless Joe asks.
- Every direction is seen from behind the motor.
- Decisions go to Joe as one flat numbered list, the question in bold on each item.
- Plain English, no em dashes, no arrows.
