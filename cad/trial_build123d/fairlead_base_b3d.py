"""
Trial (owner 2026-09-28): the inverted fairlead block v2 rebuilt in build123d (a real CAD kernel, via the
text-to-cad skill's cadgen), to compare with the trimesh version in cad/inverted.py fairlead_base().

Same frame and numbers as cad/inverted.py (assembly frame, mm): y 0 = base's outer face, block below it.
Outputs STEP (opens in Fusion, FreeCAD, any CAD program as a solid) and STL next to this script.
Run with the cadgen Python: C:/Users/SuperMaster/cadgen-venv/Scripts/python fairlead_base_b3d.py
"""
import math
from cadgen import build123d as bd
from cadgen import step, stl

# ---- numbers copied from cad/inverted.py (v2) ----
LINE_X, LINE_Z = 25.0, 45.0
BLOCK_SCREWS = [(32.0, 28.0), (32.0, 83.0)]
PIN_Y, HINGE_Z = -30.2, 58.0
FLAP_TOP = -30.8
STOP_Y = -26.0
COL = (19.0, 31.0, 39.0, 68.0)
GAP_X = (31.0, 34.0)
PLATE_X = (34.0, 37.0)
PLATE_Z = (37.0, 58.0)
PLATE_Y0 = -20.0
SW_HOLE_Y = -13.4
SW_SLIDE = 2.5
SW_HOLES_Z = (42.25, 51.75)


def bx(x0, x1, y0, y1, z0, z1):
    return bd.Box(x1 - x0, y1 - y0, z1 - z0).moved(bd.Location(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))


def xcyl(r, x0, x1, y, z):
    return bd.Cylinder(r, x1 - x0, rotation=(0, 90, 0)).moved(bd.Location(((x0 + x1) / 2, y, z)))


def ycyl(r, y0, y1, x, z):
    return bd.Cylinder(r, y1 - y0, rotation=(90, 0, 0)).moved(bd.Location((x, (y0 + y1) / 2, z)))


def bore():
    """Same profile as inverted.bore_inv(): flared top, 3.2 throat, flared bottom; revolved about the line."""
    h = -STOP_Y + 0.5
    pts = [(0, 0.0)]
    for k in range(9):
        t = k / 8; pts.append((1.6 + 3.0 * (1 - t) ** 2, -5.0 * t))
    pts.append((1.6, -(h - 5.0)))
    for k in range(1, 9):
        t = k / 8; pts.append((1.6 + 1.4 * t ** 2, -(h - 5.0 + 5.0 * t)))
    pts.append((0, -h))
    face = bd.make_face(bd.Polyline(*pts, close=True))          # in the XY plane, axis = Y
    return bd.revolve(face, bd.Axis.Y).moved(bd.Location((LINE_X, 0.05, LINE_Z)))


def block(fillet=False):
    x0, x1, z0, z1 = COL
    col = bx(x0, x1, STOP_Y, 0, z0, z1)
    if fillet:   # what a real CAD kernel adds: round the bore column's four long edges (1.5 mm)
        col = bd.fillet(col.edges().filter_by(bd.Axis.Y), radius=1.5)
    body = (bx(19, 37, -4, 0, 24, 93)
            + sum((bx(28.5, 36, -11, 0, z - 4, z + 4) for _, z in BLOCK_SCREWS[1:]), bx(28.5, 36, -11, 0, BLOCK_SCREWS[0][1] - 4, BLOCK_SCREWS[0][1] + 4))
            + col
            + bx(29.0, 36.0, PIN_Y - 2.5, 0, HINGE_Z - 3.0, HINGE_Z + 3.0)
            + bx(24.0, x1, FLAP_TOP + 0.2, STOP_Y, 63.5, 67.5)
            + bx(PLATE_X[0], PLATE_X[1], PLATE_Y0, 0, PLATE_Z[0], PLATE_Z[1])
            + bx(GAP_X[0], GAP_X[1], PLATE_Y0, 0, PLATE_Z[0], PLATE_Z[0] + 2)
            + bx(GAP_X[0], GAP_X[1], PLATE_Y0, 0, PLATE_Z[1] - 2, PLATE_Z[1]))
    cuts = bore() + xcyl(0.95, 28.5, 37, PIN_Y, HINGE_Z)
    for z in SW_HOLES_Z:
        cuts += (xcyl(1.2, GAP_X[0] - 0.5, PLATE_X[1] + 1, SW_HOLE_Y - SW_SLIDE, z)
                 + xcyl(1.2, GAP_X[0] - 0.5, PLATE_X[1] + 1, SW_HOLE_Y + SW_SLIDE, z)
                 + bx(GAP_X[0] - 0.5, PLATE_X[1] + 1, SW_HOLE_Y - SW_SLIDE, SW_HOLE_Y + SW_SLIDE, z - 1.2, z + 1.2))
    for x, z in BLOCK_SCREWS:
        cuts += ycyl(1.25, -11, 1, x, z)
    part = body - cuts
    part.label = "fairlead_base_b3d"
    return part


@step(out="fairlead_base_b3d.step")
@stl(out="fairlead_base_b3d.stl")
def fairlead_base_b3d():
    return block()


@step(out="fairlead_base_b3d_rounded.step")
@stl(out="fairlead_base_b3d_rounded.stl")
def fairlead_base_b3d_rounded():
    return block(fillet=True)


if __name__ == "__main__":
    import os
    fairlead_base_b3d_rounded() if os.environ.get('VARIANT') == 'rounded' else fairlead_base_b3d()
