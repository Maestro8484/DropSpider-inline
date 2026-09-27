# cad/ - how the parts and pictures are made

Read this before changing any printed part or any picture in `docs/img`. It is the working memory for CAD in this repo.

## The short version

There is no CAD program. Every printed part is Python code. Run the code and it writes the STL files, checks them, and draws the pictures.

```powershell
pip install trimesh manifold3d shapely numpy matplotlib      # once
.\tools\regen_cad.ps1                                          # rebuild everything
```

`tools\regen_cad.ps1` runs three scripts in order:

| Step | Script | Writes | What it does |
|---|---|---|---|
| 1 | `cad/generate.py` | `cad/stl/*.stl` | Builds each part from boxes and cylinders, adds and cuts them (boolean operations, via manifold3d), turns each part to its print orientation, exports STL, then runs checks and prints a report |
| 2 | `cad/render.py` | `docs/img/` assembly, exploded, step1 to step6, lock_detail, base_layout, fairlead_rest, fairlead_home, fairlead_exploded, wall_install, inverted_install | Places every part where it sits in the real device and draws shaded pictures with `raster.py` (a small built-in renderer, no graphics card needed). Takes 1 to 3 minutes |
| 3 | `docs/diagrams.py` | `docs/img/wiring.png`, `install.png` | Flat drawings made with matplotlib |

Same code, same output: the pictures and STLs are rebuilt identically every time.

## Files

| File | Holds |
|---|---|
| `generate.py` | Every part except the fairlead unit: bracket, spool body, ratchet disk, finger, spacers, shims. The `PARTS` table maps file names to functions. `assembly()` places every part in its installed position |
| `fairlead.py` | Fairlead body, hinged flap, KW12-3 switch model, hinge math. Run it on its own for the flap travel report |
| `sensor_mount.py` | LD2450 radar mount: fork glued under the servo end, cradle tilting on one M3 bolt. Run it on its own for its fit report: clear of every part at every tilt from 0 to 50 degrees |
| `inverted.py` | Inverted install (doc 06 alternative, approved 2026-09-27): the device turned over on two steel corner braces. `bracket_inverted()` (the 3 drilled holes), `fairlead_base()` (doc 09's unit as a block under the base, exported as `fairlead_base.stl`), the radar turned over under the servo end, brace stand-ins, a board box, `assembly_inverted()`, `porch()` and `view_inv()` (pictures with the floor down). Run it on its own for its report: watertight, face flat, clash (braces and board box included), radar view, line path, spool clearance, flap stops and roller push, screw heads, loads, heights |
| `wall_hinge.py` | Superseded by `inverted.py`, kept for reference. Wall install draft (the owner's earlier plan): hinge plate frame for the beam, two clips for the pad, a tie bar across the device's far end, two struts. `assembly_hinge()` places them on the device. Run it on its own for its report: watertight, clash, six pins, screwdriver paths, swing, strut load and buckling |
| `wall_mount.py` | Superseded, kept for reference. Fallback wall install: one braced shelf (212 cm3) that keeps the device at the ceiling with no cords, plus `ld2450_fork_screw` for putting the radar under the beam. Not in the print list; `python wall_mount.py` for its report |
| `render.py` | All 3D pictures. One function per picture |
| `footprint_svg.py` | Laser-cutter SVG of the bracket's ceiling face with every hole, 1:1 mm, seen from below: writes `bracket_footprint.svg` in cad/, and `bracket_footprint_inverted.svg` with the three holes drilled for the inverted install |
| `raster.py` | The renderer (hidden surfaces, shading, outlines) |
| `stl/` | Print-ready output. Never edit these by hand |
| `retired/` | Obsolete parts kept for reference. Do not print |

## The coordinate frame (every doc uses it)

Units: millimeters.
- **y = 0** is the ceiling face of the bracket. **+y** points down toward the floor.
- **z = 0** is the outer face of the motor plate. **+z** runs along the rod toward the 606ZZ bearing plate.
- **Rod axis** at x = 0, y = 40. Servo tower on **+x**. Electronics pad on **-x**.
- **Line** leaves the spool at x = -25, z = 45 and runs straight down (+y) through the fairlead.
- "Clockwise seen from the 606ZZ end" = looking from +z toward the motor, x to the right, y up.
- Inverted install (`inverted.py`): the same frame, so y = 0 is the base's outer face and +y points UP in the porch. The line leaves the spool at x = 25, z = 45 and runs through the base (-y). Its pictures use `view_inv()` so the floor is down.

## Checks the scripts run (read the report every time)

| Check | Where | Pass |
|---|---|---|
| Every part is a closed solid (watertight, printable) | generate.py | `watertight=True` on every line |
| Nothing touches the spinning spool, 2 mm clearance | generate.py | `0.0 mm3 overlap` for bracket, fairlead_body, servo |
| No clashes between moving and fixed parts | generate.py | no `CLASH` lines |
| Finger tip reaches into the tooth root | generate.py | `engaged: True` |
| Finger seats in a tooth gap (rotates the ratchet through one tooth pitch in 0.25 degree steps) | generate.py | `True (window 6.75 to 11.75 deg)` for the Rev C.1 finger |
| Flap hard stop and switch travel | `python fairlead.py` | hard stop about 14.75 deg; roller push at least 3.4 mm |
| Line path open through the fairlead bore and the flap slot | `python fairlead.py` | `line path clear ... True` twice (a flipped bore once printed solid) |
| Wall hinge: plate, clips, tie bar and struts clear every part and each other; six pins line up; four screwdriver paths clear; swing clear to 65 degrees | `python wall_hinge.py` | `clear every device part and each other`, `all 6 pins ... True`, four `clear` screw lines, `swing: clear ... down to 65 degrees` |

## Changing a part: the routine

1. Edit the part's function in `generate.py` or `fairlead.py`. Keep dimensions as named constants at the top where they already are.
2. Run `python generate.py` (and `python fairlead.py` for fairlead changes). Read the report. Any `CLASH`, `watertight=False`, or lost clearance means stop.
3. Run `python render.py` and look at the affected pictures.
4. Update the doc that describes the part (01 for the spool, finger and bracket, 09 for the fairlead).
5. Tell the owner which STL changed and whether an already-printed part is now out of date.
6. Geometry changes need the owner's approval (CLAUDE.md hard constraints).

## Lessons already learned (do not repeat these)

- **Print orientation lives in code.** Parts that must print a certain way have a `*_print()` function that turns them before export. Never ask the owner to rotate in the slicer.
- **Recesses face up.** A recess on the bed side leaves a ceiling with nothing under it; Bambu Studio reports "floating regions" or "isolated object". The finger v1 failed this way.
- **No overhangs on the spool.** The spool is two parts (body and ratchet disk) so both print flat with zero supports and no scars in the line channel. The spool hub must end flush with its flange; a stub under the flange forced supports once.
- **Thin features fail in PLA.** Keep printed walls at 1.2 mm or more near loads. Finger v1 had 0.9 mm walls and a half-width tip; the current finger is 7 mm wide with a 7 mm plate.
- **Tip shapes must match the teeth.** An unbeveled 7 mm finger could not seat in any tooth gap. The 20 degree bevel on the ramp side fixed it. Re-run the seating check after any finger or tooth change.
- **Nothing may stick out of the ceiling face** (y = 0). That is why the fairlead's two M3 screws are countersunk flush (owner: no glue).
- **Directions are easy to get backwards.** One-way clutch: it only lets the spool overrun in the direction the rod can drive it (flaw M1). Check any direction claim against the frame above before writing it into a doc.
- **The bracket is printed and final.** Changes should bolt or screw to it, not require reprinting it. No glue (owner 2026-09-26).

- **Printed holes come out small on the owner's printer.** A 4.8 mm socket printed 4.5; a 10.0 spacer in a 10.2 hole was too tight. Draw slide fits 0.2 to 0.3 mm a side bigger, and free-turning pins about 0.25 mm a side. A fit check (2026-09-26) found 9 fits wrong; see the git log.
- **A boolean cut can silently miss.** The fairlead bore once sat at y -78 because of a sign flip, so the part printed solid. Every functional void now has a check that fails if it misses (line path check, flatness check in `fairlead.py`).
- **A face something mounts on must be one plane.** Check the distinct levels of the faces under it (the switch face and the fairlead's mounting face each had a 0.8 to 1 mm step the owner had to shim).
- **A recess on the bed side needs stepped bridging**, or it prints a roof over air. The finger's screw-head recess uses it: two strips, then a square, then the round hole.
- **Every member starts on the bed plane**, and ribs run the full height to both ends.
- **`lbl()` in render.py takes render-world coordinates, (x, z, -y), not assembly coordinates.** A label given (x, y, z) lands somewhere else on the page (wall_install.png, 2026-09-27).
- **An L-bracket with two end braces cannot print on its side** (the prior-art advice for a strong corner): the second brace would hang over air. It prints shelf-down with the plate and braces standing; the braces keep the corner's layer bonds under 1 MPa, so the weaker orientation costs nothing that matters.

## Adding a new picture

Write a function in `render.py` that builds a list of `(mesh, color)` pairs from `G.assembly()` (or from parts moved apart for an exploded view), calls `raster.render(items, elev=..., azim=..., W=..., H=...)`, and saves with `save()`. Add the function to the `__main__` line at the bottom so `regen_cad.ps1` builds it. Use `rview()` so the ceiling is at the top of the picture.

## Known limits

- Python 3.10 or later. `trimesh` path functions that need `rtree` (area of a cross-section) are avoided; install `rtree` if you add one.
- Rendering is CPU only; big pictures take a minute or two.
- The owner's chat session can edit these text files but cannot write STL or PNG files into the repo. After an owner CAD change, run `regen_cad.ps1` here.
