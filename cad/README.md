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
| 2 | `cad/render.py` | `docs/img/` assembly, exploded, step1 to step6, lock_detail, base_layout, fairlead_rest, fairlead_home, fairlead_exploded | Places every part where it sits in the real device and draws shaded pictures with `raster.py` (a small built-in renderer, no graphics card needed). Takes 1 to 3 minutes |
| 3 | `docs/diagrams.py` | `docs/img/wiring.png`, `install.png` | Flat drawings made with matplotlib |

Same code, same output: the pictures and STLs are rebuilt identically every time.

## Files

| File | Holds |
|---|---|
| `generate.py` | Every part except the fairlead unit: bracket, spool body, ratchet disk, finger, spacers, shims. The `PARTS` table maps file names to functions. `assembly()` places every part in its installed position |
| `fairlead.py` | Fairlead body, hinged flap, KW12-3 switch model, hinge math. Run it on its own for the flap travel report |
| `sensor_mount.py` | LD2450 radar mount: fork glued under the servo end, cradle tilting on one M3 bolt. Run it on its own for its fit report: clear of every part at every tilt from 0 to 50 degrees |
| `render.py` | All 3D pictures. One function per picture |
| `footprint_svg.py` | Laser-cutter SVG of the bracket's ceiling face with every hole, 1:1 mm, seen from below: writes `bracket_footprint.svg` in cad/ |
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
- **Thin features fail in PLA.** Keep printed walls at 1.2 mm or more near loads. Finger v1 had 0.9 mm walls and a half-width tip; v2 is 5 mm thick and 7 mm wide.
- **Tip shapes must match the teeth.** An unbeveled 7 mm finger could not seat in any tooth gap. The 20 degree bevel on the ramp side fixed it. Re-run the seating check after any finger or tooth change.
- **Nothing may stick out of the ceiling face** (y = 0). That is why the fairlead's two M3 screws are countersunk flush (owner: no glue).
- **Directions are easy to get backwards.** One-way clutch: it only lets the spool overrun in the direction the rod can drive it (flaw M1). Check any direction claim against the frame above before writing it into a doc.
- **The bracket is printed and final.** Changes should bolt or glue to it, not require reprinting it.

## Adding a new picture

Write a function in `render.py` that builds a list of `(mesh, color)` pairs from `G.assembly()` (or from parts moved apart for an exploded view), calls `raster.render(items, elev=..., azim=..., W=..., H=...)`, and saves with `save()`. Add the function to the `__main__` line at the bottom so `regen_cad.ps1` builds it. Use `rview()` so the ceiling is at the top of the picture.

## Known limits

- Python 3.10 or later. `trimesh` path functions that need `rtree` (area of a cross-section) are avoided; install `rtree` if you add one.
- Rendering is CPU only; big pictures take a minute or two.
- The owner's chat session can edit these text files but cannot write STL or PNG files into the repo. After an owner CAD change, run `regen_cad.ps1` here.
