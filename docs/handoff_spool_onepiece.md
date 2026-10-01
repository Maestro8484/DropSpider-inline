# Handoff: one-piece spool and ratchet (Rev C.3)

Redesign the three-part spool stack (`spool_ratchet`, `spool_shield`, `spool_body`) as one part that prints with no supports, grips the HF0612 one-way bearing so it cannot turn in its hole, and keeps the line separator out of the finger's reach. For a CAD session working with the owner (Joe).

## Ground truth first

This file is a work order, not a record. The repo on disk wins: `cad/generate.py` is the source of truth for every dimension below. If this file and the code disagree, the code is right and this file is stale; say so out loud. Staleness check:

```
git log -1 --oneline                                   # where the repo is now
git log -1 --oneline -- docs/handoff_spool_onepiece.md # when this file was last true
```

## Before you start

1. **Which part slips, the bearing in its hole or the clutch on the rod?** Joe reports "the one-way bearing slips a bit". Ask him to draw one marker line across the HF0612's outer ring and the spool face, run a few drops or turn it by hand against the lock, and look. Line split at the ring edge = the bearing turns in the plastic, so this redesign fixes it (step 3). Line still whole but the spool slips on the rod = the clutch slipping on the rod, which a printed part cannot fix; stop and report it instead.
2. **What is left of the finger.** Joe cut about 5 mm off the finger's face with flush cutters so it stopped catching the separator disc. Ask whether he cut its thickness (along the rod) or its length (toward the teeth), and how much finger now sits on the ratchet teeth (look edge-on at the lock angle). Either cut means less tooth engagement than the design's 7 mm; the new spool must let a fresh, uncut `finger.stl` work.
3. **"About 1 mm smaller diameter."** Joe's words, tied to the bearing slipping. The bearing is 10.0 mm across, so a 9.3 hole cannot take it; read it as the bearing hole going tighter (10.3 now). Confirm with him in one line before designing: "bearing hole tighter, 10.3 to about 10.2 with crush ribs, yes?"
4. Run `cd cad; python generate.py` and confirm every check passes before changing anything, so a later failure is yours.

## Read first

1. `CLAUDE.md`, especially the direction rule (every clockwise is seen from behind the motor) and "edit `cad/generate.py`, never the STLs".
2. `cad/README.md`: frame, rebuild routine, checks, lessons (the HF0612 press-fit history is there: 10.0 would not take it, 10.2 tight, 10.7 loose, 10.3 chosen).
3. `cad/generate.py`: `spool_ratchet`, `spool_shield`, `spool_body`, `ratchet_poly`, `spoke_windows`, `hole_chamfer`, `finger`, the finger seating check, and `assembly()`.
4. `docs/01_mechanical_design.md`, the stack table (z 30 to 106) and the print table.
5. `docs/05_assembly.md` steps 1 to 9 and the build guide's spool steps, which this part changes.

## The work, in order

1. **One part, three zones along the rod.** Ratchet (12 teeth, tip r 33, root r 29, ramps rise clockwise and steep faces block counterclockwise, seen from behind the motor; keep `ratchet_poly`), then a separator, then the barrel and the far flange. No screws, no counterbores. The HF0612 presses in from the flange side as now.
2. **Separator smaller than the finger's reach.** Today's shield is r 32, out past the finger's tip (closest approach r 29.38), so when Joe shimmed the stack along the rod the finger rode onto it. Make the separator r 28 or less (at least 1 mm inside the finger tip), so the finger can overlap it along the rod and never touch it. It only has to keep the line off the teeth: about 720 mm of 6 lb mono is under 5 turns on the r 25 barrel, one layer. Check that claim against the line length in doc 06 and say the margin in the report.
3. **Bearing hole that grips.** Standard printed press-fit: crush ribs (small ribs that the bearing shaves flat as it goes in) rather than a plain round hole. Starting point: 10.4 hole with 6 to 8 ribs reaching in to 10.0 or 10.1, plus the existing 0.4 lead-in chamfer at the flange side. Name the source you borrow the rib sizes from (guard 2: prior art first).
4. **Prints with no supports, lying on one face.** Recommended: ratchet face on the bed (the teeth are plain vertical walls; the separator and barrel are smaller, so they stand on it with no overhang). The far flange then overhangs the barrel: give its underside a 45 degree chamfer, or keep it no wider than a 45 degree slope allows. The barrel is only about 3.5 mm wide today; there is room to widen it along the rod (Joe's build needed about 4 mm of shim on the motor side and 5 mm on the 606ZZ side, and spacer B is 50 mm), so take width from the shims rather than steepening the chamfer. Every hole edge on the bed gets the 0.4 chamfer.
5. **Keep the light-weight windows** (`spoke_windows`) if they still print with no bridging in this orientation; they run straight through along the rod, so they should.
6. **Fit the stack along the rod.** Total length, spacer A and spacer B (or new shims) must put the ratchet teeth across the finger's full 7 mm with the separator clear. Write the new z table.
7. Export only the new part's STL, `spool_onepiece.stl`. Move `spool_ratchet`, `spool_shield` and `spool_body` to `cad/retired/` with a one-line "Retired, superseded by spool_onepiece" note, once Joe has the new one in hand.

## Tests

Run in the model, results in the session report and the changelog line:

- `python generate.py`: finger seating check passes (seats in a tooth gap), no clashes, swept clearance clear, with a fresh uncut finger.
- Finger to separator: no contact with the stack slid 5 mm either way along the rod (Joe's shim range).
- Overhang report for the print orientation: nothing off the bed steeper than 45 degrees except the windows' straight walls.
- `python inverted.py`: line path and every inverted check unchanged.

On the bench, logged by Joe in `docs/commissioning_log.md`: the HF0612 presses in by vise and does not turn in the hole under a hand twist against the lock; spool free clockwise and locked counterclockwise with the rod held (seen from behind the motor); finger drops into the teeth at the lock angle with no catching.

## Done when

`spool_onepiece.stl` is printed, the bearing holds, the finger engages a fresh uncut finger with no catching, and the docs say so.

## Rules for the session

- Make the part and stop. Slicer settings are Joe's; answer slicer questions only when he asks.
- Export only the changed STL; no full rebuild, no mass picture regeneration unless Joe asks. Update only the build guide steps and pictures this part touches.
- Every direction is seen from behind the motor.
- Decisions go to Joe as one flat numbered list, the question in bold on each item.
- Plain English, no em dashes, no arrows.
