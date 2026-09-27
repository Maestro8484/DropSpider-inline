"""
DropSpider Rev C.1 - wall hinge: the owner's plan for hanging the device from the porch beam's
inside face. Existing bracket, no reprint. Three small flat prints and two M3 bolts:

  hinge_plate   one strip screwed to the beam (4 wood screws). Two forks at its bottom edge
                are the hinge; two eyes at its top edge take the cords.
  hinge_clip    two, identical. Each bolts on top of the pad through the x -80 and x -56
                holes (M3 with nuts under the pad) and carries a knuckle past the pad's edge.
                An M3 x 25 bolt through fork, knuckle, fork with a nut is the hinge pin.
  cords         thin paracord or light chain from the device's far-end holes (x 65, z 20 and
                z 90: tie through the hole or round an M3 bolt in it) up to the plate's eyes.

Why the device sits below the ceiling: a cord can only pull. To hold the far end up it must
run UP from the device to an anchor above the hinge, and the anchor cannot be above the
ceiling. So the plate is PLATE_H tall, the hinge is at its bottom, the eyes at its top, and
the device's top face hangs PLATE_H below the ceiling. Smaller PLATE_H: cords flatter, more
tension, spider hides better. The report prints the tension for the number chosen.

Coordinates: the assembly frame from generate.py, device in its normal place. The ceiling is
at y = -PLATE_H. The beam's face is at X_OUT. +y is down.

Run on its own for the fit, clash, swing and cord report: python wall_hinge.py
"""
import math
import numpy as np, trimesh
from trimesh.creation import cylinder

import generate as G

# ---------------- dimensions (mm) ----------------
PLATE_H = 45.0                 # ceiling to the device's top face. Spider hides behind a 254 beam if spider height + 115 + PLATE_H < 254
PLATE_T = 4.0
HINGE_X, HINGE_Y = -93.0, -4.0 # hinge axis (runs along z): past the pad's edge (x -88), knuckle flush with the pad's top
KNUCKLE_R = 4.0
X_IN = HINGE_X - KNUCKLE_R - 1.0      # -98: plate inner face, 1 mm off the knuckle
X_OUT = X_IN - PLATE_T                # -102: the beam's face
Z_PLATE = (12.0, 100.0)
HINGE_Z = (28.0, 83.0)         # the pad's hole rows: each clip sits on one
CLIP_W = 12.0                  # clip width along z
CLIP_T = 3.0                   # clip plate thickness, on top of the pad (y -3..0)
CLIP_X = (-92.0, -50.0)        # covers the x -80 and x -56 holes
EAR_T = 4.0
EAR_GAP = 0.3                  # ear to knuckle, each side (tightening the nut locks the hinge, which is wanted once the cords are on)
EAR_R = 4.5
PIN_HOLE_KNUCKLE = 3.5         # M3 bolt turns in this (prints about 3.3)
PIN_HOLE_EAR = 3.4
EYE_HOLE = 4.0                 # cord or a small chain link
SCREWS = [(z, y) for z in (45.0, 67.0) for y in (-PLATE_H + 7, -8.0)]   # (z, y): between the hinges, above the device
SCREW_D = 3.6
BOLT_HOLE = 3.4
DEVICE_TIE = [(65.0, 20.0), (65.0, 90.0)]   # (x, z) the base's two mount holes: the cords tie here


def zcyl(r, z0, z1, x, y, sections=48):
    c = cylinder(radius=r, height=z1 - z0, sections=sections); c.apply_translation([x, y, (z0 + z1) / 2]); return c


def hinge_plate():
    bx = G.bx
    body = bx(X_OUT, X_IN, -PLATE_H, 1.0, *Z_PLATE)
    parts, cuts = [body], []
    for zc in HINGE_Z:
        for s in (-1, 1):                                       # a fork: two ears round the clip's knuckle
            zi = zc + s * (CLIP_W / 2 + EAR_GAP)
            z0, z1 = sorted((zi, zi + s * EAR_T))
            ear = G.U(zcyl(EAR_R, z0, z1, HINGE_X, HINGE_Y),
                      bx(X_IN - 0.5, HINGE_X, HINGE_Y - EAR_R, HINGE_Y + EAR_R, z0, z1))
            parts.append(ear)
        cuts.append(zcyl(PIN_HOLE_EAR / 2, zc - 20, zc + 20, HINGE_X, HINGE_Y))
        eye = bx(X_IN - 0.5, X_IN + 8, -PLATE_H, -PLATE_H + 8, zc - 3, zc + 3)   # eye lug at the top edge
        parts.append(eye)
        cuts.append(zcyl(EYE_HOLE / 2, zc - 5, zc + 5, X_IN + 4, -PLATE_H + 4))
    for z, y in SCREWS:
        c = cylinder(radius=SCREW_D / 2, height=PLATE_T + 2, sections=48)
        c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        c.apply_translation([(X_OUT + X_IN) / 2, y, z]); cuts.append(c)
    return G.D(G.U(*parts), *cuts)


def hinge_plate_print():
    """Beam face down; ears and eyes stand up as walls, their holes run level."""
    m = hinge_plate()
    m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [0, 1, 0]))   # -x (into the beam) -> down
    m.apply_translation(-m.bounds[0]); return m


def hinge_clip(zc=HINGE_Z[0]):
    bx = G.bx
    z0, z1 = zc - CLIP_W / 2, zc + CLIP_W / 2
    plate = bx(CLIP_X[0], CLIP_X[1], -CLIP_T, 0, z0, z1)
    knuckle = G.U(zcyl(KNUCKLE_R, z0, z1, HINGE_X, HINGE_Y), bx(HINGE_X, CLIP_X[0] + 0.5, -CLIP_T, 0, z0, z1))
    m = G.U(plate, knuckle)
    return G.D(m, zcyl(PIN_HOLE_KNUCKLE / 2, z0 - 1, z1 + 1, HINGE_X, HINGE_Y),
               *[G.vcyl(BOLT_HOLE / 2, 10, -5, x, zc) for x in (-80.0, -56.0)])


def hinge_clip_print():
    """On its end (a z face on the bed): the pin hole is vertical and clean, the plate holes bridge."""
    m = hinge_clip()
    m.apply_translation(-m.bounds[0]); return m


def _pin(zc):
    return zcyl(1.5, zc - 14, zc + 14, HINGE_X, HINGE_Y, 24)


def cords(A_device_tie=DEVICE_TIE):
    """Thin cylinders from each far-end hole up to its eye, for pictures and the tension numbers."""
    out = {}
    for (x, z), zc in zip(A_device_tie, HINGE_Z):
        a = np.array([x, -1.0, z]); b = np.array([X_IN + 4, -PLATE_H + 4, zc])
        v = b - a; L = np.linalg.norm(v)
        c = cylinder(radius=1.0, height=L, sections=12)
        c.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], v / L))
        c.apply_translation((a + b) / 2); out[f"cord_{zc:.0f}"] = c
    return out


def swing(m, deg):
    """Turn a device part about the hinge axis; positive drops the far end (folds it down)."""
    m = m.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(deg), [0, 0, 1], point=[HINGE_X, HINGE_Y, 0]))
    return m


def assembly_hinge():
    A = dict(G.assembly())
    A["hinge_plate"] = hinge_plate()
    for i, zc in enumerate(HINGE_Z):
        A[f"hinge_clip_{i}"] = hinge_clip(zc); A[f"pin_{i}"] = _pin(zc)
    A.update(cords())
    return A


def porch():
    ceiling_y = -PLATE_H
    beam = G.bx(X_OUT - 90, X_OUT, ceiling_y, ceiling_y + 254, -100, 220)
    ceiling = G.bx(X_OUT - 90, 200, ceiling_y - 12, ceiling_y, -100, 220)
    return {"beam": beam, "ceiling": ceiling}


# ---------------- numbers ----------------
DEVICE_MASS_G, LINE_SNAP_N, LINE_X, DEVICE_CG_X, SAFETY = 480.0, 27.0, -25.0, -5.0, 3.0


def cord_report():
    W = DEVICE_MASS_G / 1000 * 9.81
    M = (W * (DEVICE_CG_X - HINGE_X) + LINE_SNAP_N * (LINE_X - HINGE_X)) / 1000   # N m about the hinge, snap included
    a = np.array([DEVICE_TIE[0][0], -1.0]); b = np.array([X_IN + 4, -PLATE_H + 4]); h = np.array([HINGE_X, HINGE_Y])
    d = b - a; lever = abs(d[0] * (h[1] - a[1]) - d[1] * (h[0] - a[0])) / np.linalg.norm(d)   # hinge to the cord's line, mm
    ang = math.degrees(math.atan2(-d[1], -d[0]))
    T = M * 1000 / lever
    print(f"cords: rise {-d[1]:.0f} over {-d[0]:.0f} mm ({ang:.0f} degrees), lever about the hinge {lever:.0f} mm")
    print(f"  standing: {W * (DEVICE_CG_X - HINGE_X) / lever:.0f} N total in the two cords; with a line snap: {T:.0f} N; x{SAFETY:.0f} safety {T * SAFETY:.0f} N (paracord holds over 2000, 2 mm micro cord about 400)")
    print(f"  hinge pin sees about the same; an M3 in double shear takes over 1000 N")
    print(f"device top {PLATE_H:.0f} mm below the ceiling: spider bottom at rest = spider height + {115 + PLATE_H:.0f} mm below the ceiling; the beam's bottom edge is at 254")


if __name__ == "__main__":
    P, C = hinge_plate(), hinge_clip()
    print(f"hinge_plate watertight={P.is_watertight} size={np.round(P.extents, 1).tolist()} vol={P.volume / 1000:.1f}cm3")
    print(f"hinge_clip  watertight={C.is_watertight} size={np.round(C.extents, 1).tolist()} vol={C.volume / 1000:.1f}cm3  (print 2)")
    for name, fn in (("plate", hinge_plate_print), ("clip", hinge_clip_print)):
        p = fn(); down = (p.face_normals[:, 2] < -0.7) & (p.triangles_center[:, 2] > 0.01)
        print(f"{name} print: footprint {np.round(p.extents[:2], 1).tolist()}, height {p.extents[2]:.1f}, overhang off the bed {p.area_faces[down].sum():.0f} mm2")
    A = assembly_hinge()
    print("--- clash check, overlap volume in mm3 (none listed = clear) ---")
    new = [k for k in A if k.startswith(("hinge", "pin", "cord"))]
    bad = False
    for k in new:
        for j, part in A.items():
            if j == k or {k[:4], j[:4]} in ({"pin_", "hing"}, {"cord", "hing"}): continue   # pins sit in their holes, cords end inside their eyes
            v = G.I(A[k], part).volume
            if v > 0.5: print(f"CLASH {k} x {j}: {v:.1f}"); bad = True
    if not bad: print("plate, clips, pins and cords clear every device part")
    pin_ok = all(G.I(A[f"pin_{i}"], A["hinge_plate"]).volume < 0.05 and G.I(A[f"pin_{i}"], A[f"hinge_clip_{i}"]).volume < 0.05 for i in range(2))
    print(f"pin holes line up through both forks and the knuckle: {pin_ok}")
    print(f"pad edge x -88 to the plate: {-88 - X_IN:.0f} mm; line falls {LINE_X - X_OUT:.0f} mm from the beam's face")
    dev = [k for k in A if k not in new and not k.startswith("ld2450")]
    for deg in (0, 30, 60, 90):
        hits = [k for k in dev for j in ("hinge_plate",) if G.I(swing(A[k], deg), A[j]).volume > 0.5]
        print(f"swing {deg:2.0f} degrees down on the hinge: {'clear of the plate' if not hits else 'HITS ' + str(hits)}")
    cord_report()
