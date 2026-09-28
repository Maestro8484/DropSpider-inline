"""
DropSpider Rev C.1 - wall hinge: the owner's plan for hanging the device from the porch beam's
inside face. Existing bracket, no reprint. Two plates at 90 degrees, hinged where they meet,
a diagonal bar between their far ends at each side. Five small flat prints:

  hinge_plate   a frame screwed to the beam (4 wood screws, one at each corner): a top rail
                carrying the two hinge forks, two legs hanging down the beam with a fork at the
                bottom of each for the diagonal bars.
  hinge_clip    two, identical. Each bolts on top of the pad through the x -80 and x -56
                holes (M3, nuts under the pad) and carries a knuckle past the pad's edge.
                An M3 x 25 bolt through fork, knuckle, fork with a nut is the hinge pin.
  tie_bar       the second plate: a strip on top of the device's far edge, bolted through the
                base's two x 65 holes, with a lug hanging down at each end past the device.
  strut         two, identical. The 45 degree connector: a bar with an eye at each end, from a
                leg's bottom fork up to a tie bar lug, M3 pins. It is pushed (the device's
                weight tries to fold the hinge shut), so it must be stiff: chain or cord would
                go slack here. It sits outside the device, past the motor and past the bearing plate.

The device's top face is 8 mm below the ceiling (the hinge knuckle needs the room). Line falls
77 mm from the beam's face.

Coordinates: the assembly frame from generate.py, device in its normal place. The beam's face
is at X_OUT, the ceiling at y = CEILING_Y. +y is down.

Run on its own for the fit, clash, swing and load report: python wall_hinge.py
"""
import math
import numpy as np, trimesh
from trimesh.creation import cylinder, extrude_polygon
from shapely.geometry import Polygon

import generate as G

# ---------------- dimensions (mm) ----------------
PLATE_T = 4.0
HINGE_X, HINGE_Y = -93.0, -4.0 # hinge axis (runs along z): past the pad's edge (x -88), knuckle flush with the pad's top
KNUCKLE_R = 4.0
X_IN = HINGE_X - KNUCKLE_R - 1.0      # -98: plate inner face, 1 mm off the knuckle
X_OUT = X_IN - PLATE_T                # -102: the beam's face
CEILING_Y = HINGE_Y - KNUCKLE_R       # -8: the knuckle top touches the ceiling
RAIL_Y1 = 12.0                 # top rail y CEILING_Y..12
LEG_W = 12.0
LEG_Z = ((-48.0, -36.0), (116.0, 128.0))   # legs hang past the motor (z -32) and the bearing plate (z 106)
PLATE_Y1 = 150.0               # legs reach here (the device ends at 112; the beam is 254 deep)
HINGE_Z = (28.0, 83.0)         # the pad's hole rows: each clip sits on one
CLIP_W, CLIP_T = 12.0, 3.0     # clip width along z; plate thickness on top of the pad (y -3..0)
CLIP_X = (-92.0, -50.0)        # covers the x -80 and x -56 holes
EAR_T, EAR_GAP, EAR_R = 4.0, 0.3, 4.5
PIN_HOLE_TURN = 3.5            # an M3 bolt turns in this (prints about 3.3)
PIN_HOLE_HOLD = 3.4
STRUT_Z = (-42.0, 122.0)       # centre z of each strut, inside its leg's width
STRUT_W = 8.0                  # along z
STRUT_D = 7.0                  # in the plane of the triangle
STRUT_LOW_Y = 140.0            # bottom pin, on the leg
TIE_X = (58.0, 72.0)           # tie bar strip over the x 65 holes
TIE_T = 4.0
TIE_LUG_Y = 8.0                # top pin: lug hanging under the tie bar's ends, past the device
SCREWS = [(z, y) for z in (-42.0, 122.0) for y in (4.0, 140.0)]   # (z, y): one per leg corner, all outside the device
SCREW_D, BOLT_HOLE = 3.6, 3.4
BASE_HOLES_Z = (20.0, 90.0)


def zcyl(r, z0, z1, x, y, sections=48):
    c = cylinder(radius=r, height=z1 - z0, sections=sections); c.apply_translation([x, y, (z0 + z1) / 2]); return c


def fork(x, y, zc, w, face_x):
    """Two ears round a w wide knuckle centred on zc, hole along z at (x, y), joined to a face at face_x (the ears reach from face_x to the hole)."""
    ears = []
    for s in (-1, 1):
        zi = zc + s * (w / 2 + EAR_GAP); z0, z1 = sorted((zi, zi + s * EAR_T))
        lo, hi = sorted((face_x, x))
        ears.append(G.U(zcyl(EAR_R, z0, z1, x, y), G.bx(lo - 0.5 if face_x < x else lo, hi + 0.5 if face_x > x else hi, y - EAR_R, y + EAR_R, z0, z1)))
    return ears


def hinge_plate():
    bx = G.bx
    z_lo, z_hi = LEG_Z[0][0], LEG_Z[1][1]
    rail = bx(X_OUT, X_IN, CEILING_Y, RAIL_Y1, z_lo, z_hi)
    legs = [bx(X_OUT, X_IN, CEILING_Y, PLATE_Y1, z0, z1) for z0, z1 in LEG_Z]
    parts = [rail] + legs; cuts = []
    for zc in HINGE_Z:
        parts += fork(HINGE_X, HINGE_Y, zc, CLIP_W, X_IN)
        cuts.append(zcyl(PIN_HOLE_HOLD / 2, zc - 20, zc + 20, HINGE_X, HINGE_Y))
    for zc in STRUT_Z:
        parts += fork(HINGE_X, STRUT_LOW_Y, zc, STRUT_W, X_IN)
        cuts.append(zcyl(PIN_HOLE_HOLD / 2, zc - 20, zc + 20, HINGE_X, STRUT_LOW_Y))
    for z, y in SCREWS:
        c = cylinder(radius=SCREW_D / 2, height=PLATE_T + 2, sections=48)
        c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        c.apply_translation([(X_OUT + X_IN) / 2, y, z]); cuts.append(c)
    return G.D(G.U(*parts), *cuts)


def hinge_plate_print():
    """Beam face down; forks stand up as walls, their holes run level."""
    m = hinge_plate()
    m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [0, 1, 0]))   # -x (into the beam) -> down
    m.apply_translation(-m.bounds[0]); return m


def hinge_clip(zc=HINGE_Z[0]):
    bx = G.bx
    z0, z1 = zc - CLIP_W / 2, zc + CLIP_W / 2
    plate = bx(CLIP_X[0], CLIP_X[1], -CLIP_T, 0, z0, z1)
    knuckle = G.U(zcyl(KNUCKLE_R, z0, z1, HINGE_X, HINGE_Y), bx(HINGE_X, CLIP_X[0] + 0.5, -CLIP_T, 0, z0, z1))
    return G.D(G.U(plate, knuckle), zcyl(PIN_HOLE_TURN / 2, z0 - 1, z1 + 1, HINGE_X, HINGE_Y),
               *[G.vcyl(BOLT_HOLE / 2, 10, -5, x, zc) for x in (-80.0, -56.0)])


def hinge_clip_print():
    """On its end (a z face on the bed): the pin hole is vertical and clean, the plate holes bridge."""
    m = hinge_clip(); m.apply_translation(-m.bounds[0]); return m


def tie_bar():
    """Strip on top of the base's far edge, bolted at the x 65 holes; a lug under each end carries a strut pin."""
    bx = G.bx
    z_lo, z_hi = STRUT_Z[0] - STRUT_W / 2 - EAR_GAP - EAR_T, STRUT_Z[1] + STRUT_W / 2 + EAR_GAP + EAR_T
    strip = bx(TIE_X[0], TIE_X[1], -TIE_T, 0, z_lo, z_hi)
    parts, cuts = [strip], []
    for zc in STRUT_Z:
        for s in (-1, 1):
            zi = zc + s * (STRUT_W / 2 + EAR_GAP); z0, z1 = sorted((zi, zi + s * EAR_T))
            parts.append(G.U(bx(65 - EAR_R, 65 + EAR_R, -0.5, TIE_LUG_Y, z0, z1), zcyl(EAR_R, z0, z1, 65, TIE_LUG_Y)))
        cuts.append(zcyl(PIN_HOLE_HOLD / 2, zc - 20, zc + 20, 65, TIE_LUG_Y))
    cuts += [G.vcyl(BOLT_HOLE / 2, 10, -6, 65, z) for z in BASE_HOLES_Z]
    return G.D(G.U(*parts), *cuts)


def tie_bar_print():
    """Top face down; the lugs stand up at the ends, pin holes level."""
    m = tie_bar()
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [0, 0, 1]))   # x -> -x, y -> -y: top face (y -4) now lowest
    m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))
    m.apply_translation(-m.bounds[0]); return m


def strut(zc=STRUT_Z[0]):
    """Bar with an eye at each end, in the x-y plane at zc, from the leg's bottom pin to the tie bar's lug pin."""
    a = np.array([HINGE_X, STRUT_LOW_Y]); b = np.array([65.0, TIE_LUG_Y])
    d = b - a; L = np.linalg.norm(d); u = d / L; n = np.array([-u[1], u[0]]) * STRUT_D / 2
    poly = Polygon([tuple(a + n), tuple(b + n), tuple(b - n), tuple(a - n)])
    bar = extrude_polygon(poly, STRUT_W); bar.apply_translation([0, 0, zc - STRUT_W / 2])
    eyes = [zcyl(EAR_R, zc - STRUT_W / 2, zc + STRUT_W / 2, *p) for p in (a, b)]
    return G.D(G.U(bar, *eyes), *[zcyl(PIN_HOLE_TURN / 2, zc - 10, zc + 10, *p) for p in (a, b)])


def strut_print():
    """Flat, on its side face."""
    m = strut(); m.apply_translation(-m.bounds[0]); return m


def _pin(x, y, zc, half=14):
    return zcyl(1.5, zc - half, zc + half, x, y, 24)


def swing(m, deg):
    """Turn a device part about the hinge axis; positive drops the far end (folds it down)."""
    m = m.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(deg), [0, 0, 1], point=[HINGE_X, HINGE_Y, 0]))
    return m


def assembly_hinge():
    A = dict(G.assembly())
    A["hinge_plate"] = hinge_plate(); A["tie_bar"] = tie_bar()
    for i, zc in enumerate(HINGE_Z):
        A[f"hinge_clip_{i}"] = hinge_clip(zc); A[f"pin_h{i}"] = _pin(HINGE_X, HINGE_Y, zc)
    for i, zc in enumerate(STRUT_Z):
        A[f"strut_{i}"] = strut(zc); A[f"pin_l{i}"] = _pin(HINGE_X, STRUT_LOW_Y, zc, 10); A[f"pin_t{i}"] = _pin(65, TIE_LUG_Y, zc, 10)
    return A


def porch():
    beam = G.bx(X_OUT - 90, X_OUT, CEILING_Y, CEILING_Y + 254, -100, 220)
    ceiling = G.bx(X_OUT - 90, 200, CEILING_Y - 12, CEILING_Y, -100, 220)
    return {"beam": beam, "ceiling": ceiling}


# ---------------- numbers ----------------
DEVICE_MASS_G, LINE_SNAP_N, LINE_X, DEVICE_CG_X, SAFETY, PLA_E = 480.0, 27.0, -25.0, -5.0, 3.0, 3000.0


def load_report():
    W = DEVICE_MASS_G / 1000 * 9.81
    M = W * (DEVICE_CG_X - HINGE_X) + LINE_SNAP_N * (LINE_X - HINGE_X)        # N mm about the hinge, snap included
    a = np.array([HINGE_X, STRUT_LOW_Y]); b = np.array([65.0, TIE_LUG_Y]); h = np.array([HINGE_X, HINGE_Y])
    d = b - a; L = np.linalg.norm(d); lever = abs(d[0] * (h[1] - a[1]) - d[1] * (h[0] - a[0])) / L
    ang = math.degrees(math.atan2(-d[1], d[0]))
    F = M / lever
    I = STRUT_W * STRUT_D ** 3 / 12
    Pcr = math.pi ** 2 * PLA_E * I / L ** 2
    print(f"struts: {L:.0f} mm long at {ang:.0f} degrees, lever about the hinge {lever:.0f} mm")
    print(f"  push in both together: {W * (DEVICE_CG_X - HINGE_X) / lever:.0f} N standing, {F:.0f} N on a line snap, x{SAFETY:.0f} safety {F * SAFETY:.0f} N")
    print(f"  one strut {STRUT_D:.0f} x {STRUT_W:.0f} buckles at about {Pcr:.0f} N: margin x{Pcr / (F * SAFETY / 2):.0f} per strut on the safety load")
    print(f"device top {-CEILING_Y:.0f} mm below the ceiling: spider bottom at rest = spider height + {115 - CEILING_Y:.0f} mm below the ceiling; the beam's bottom edge is at 254")


if __name__ == "__main__":
    for name, fn, n in (("hinge_plate", hinge_plate, 1), ("hinge_clip", hinge_clip, 2), ("tie_bar", tie_bar, 1), ("strut", strut, 2)):
        m = fn()
        print(f"{name:12s} watertight={m.is_watertight} size={np.round(m.extents, 1).tolist()} vol={m.volume / 1000:.1f}cm3  print {n}")
    for name, fn in (("plate", hinge_plate_print), ("clip", hinge_clip_print), ("tie_bar", tie_bar_print), ("strut", strut_print)):
        p = fn(); down = (p.face_normals[:, 2] < -0.7) & (p.triangles_center[:, 2] > 0.01)
        print(f"  {name} print: footprint {np.round(p.extents[:2], 1).tolist()}, height {p.extents[2]:.1f}, overhang off the bed {p.area_faces[down].sum():.0f} mm2")
    A = assembly_hinge()
    print("--- clash check, overlap volume in mm3 (none listed = clear) ---")
    new = [k for k in A if k.startswith(("hinge", "pin", "strut", "tie"))]
    bad = False
    for k in new:
        for j, part in A.items():
            if j == k or k.startswith("pin") or j.startswith("pin"): continue
            v = G.I(A[k], part).volume
            if v > 0.5: print(f"CLASH {k} x {j}: {v:.1f}"); bad = True
    if not bad: print("plate, clips, tie bar and struts clear every device part and each other")
    pins_ok = all(G.I(A[k], A[j]).volume < 0.05 for k in A if k.startswith("pin") for j in ("hinge_plate", "tie_bar", "hinge_clip_0", "hinge_clip_1", "strut_0", "strut_1"))
    print(f"all 6 pins pass through their holes (forks, knuckles, lugs, eyes): {pins_ok}")
    print(f"pad edge x -88 to the plate: {-88 - X_IN:.0f} mm; line falls {LINE_X - X_OUT:.0f} mm from the beam's face")
    for i, (z, y) in enumerate(SCREWS):
        shaft = cylinder(radius=3.0, height=220, sections=32)
        shaft.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        shaft.apply_translation([X_IN + 0.2 + 110, y, z])
        hits = [k for k, part in A.items() if k != "hinge_plate" and not k.startswith(("strut", "pin")) and G.I(shaft, part).volume > 0.5]
        print(f"screw {i + 1} at y {y:.0f} z {z:.0f}: straight screwdriver path (struts not yet on) is {'clear' if not hits else 'BLOCKED by ' + str(hits)}")
    dev = [k for k in A if k not in new and not k.startswith("ld2450")] + ["tie_bar"]
    for deg in np.arange(0, 91, 5.0):                       # struts off: the device hangs on the hinge and is swung up
        hits = [k for k in dev if G.I(swing(A[k], deg), A["hinge_plate"]).volume > 0.5]
        if hits: print(f"swing: clear of the plate from level down to {deg - 5:.0f} degrees; at {deg:.0f} {hits} touch the plate (hang it at less than that and swing up)"); break
    else: print("swing: clear of the plate from level to straight down")
    load_report()
