"""
DropSpider - Mechanism A - In-Line Single-Axle Clutch Spool (ISCS) - Rev C
Parametric source for every printed part, plus an installed-assembly model used for
clash checks and renders.

Run:     python generate.py
Needs:   pip install trimesh manifold3d shapely numpy matplotlib

ASSEMBLY FRAME (every coordinate in the docs uses this):
  y = 0   mounting face (ceiling). +y points away from the mount (toward the floor).
  z = 0   outer face of the motor plate. +z runs along the rod toward the 606ZZ plate.
  Rod axis at x = 0, y = 40. Servo tower on +x. Electronics pad on -x.
"""
import math, os, numpy as np, trimesh
from trimesh.creation import box, cylinder, extrude_polygon
from shapely.geometry import Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stl")
os.makedirs(OUT, exist_ok=True)

# ---------------- primitives ----------------
def cyl(r, h, z0, x=0, y=0, sections=96):
    c = cylinder(radius=r, height=h, sections=sections); c.apply_translation([x, y, z0 + h / 2]); return c

def vcyl(r, h, y0, x, z, sections=64):  # cylinder along y
    c = cylinder(radius=r, height=h, sections=sections)
    c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    c.apply_translation([x, y0 + h / 2, z]); return c

def bx(x0, x1, y0, y1, z0, z1):
    b = box(extents=[x1 - x0, y1 - y0, z1 - z0]); b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]); return b

def U(*m): return trimesh.boolean.union(list(m), engine="manifold")
def D(a, *m): return trimesh.boolean.difference([a] + list(m), engine="manifold")
def I(a, b): return trimesh.boolean.intersection([a, b], engine="manifold")

# ---------------- key dimensions (mm) ----------------
AXIS_Y = 40.0
BARREL_D = 50.0                 # line winds on this diameter
TOOTH_TIP_R, TOOTH_ROOT_R, TEETH = 33.0, 29.0, 12
HF0612_BORE = 9.9               # 10.0 OD one-way bearing, 0.1 press
BEARING_606 = 16.8              # 17.0 OD 606ZZ, 0.2 press (PLA)
Z_RATCHET = 36.0                # ratchet disk motor-side face; finger plane is z 36..39
SERVO_SHAFT_X = 49.7            # SG90 output spline, spline end of servo toward the spool
BOLT_R = 21.0
BOLTS = [(BOLT_R * math.cos(a), BOLT_R * math.sin(a)) for a in (0, 2 * math.pi / 3, 4 * math.pi / 3)]

# ---------------- ratchet ----------------
def ratchet_poly():
    pts = []
    for i in range(TEETH):
        a0 = math.radians(i * 360 / TEETH); a1 = math.radians(i * 360 / TEETH + 27); a2 = math.radians((i + 1) * 360 / TEETH)
        for k in range(10):
            t = k / 10; a = a0 + (a1 - a0) * t; r = TOOTH_TIP_R + (TOOTH_ROOT_R - TOOTH_TIP_R) * t
            pts.append((r * math.cos(a), r * math.sin(a)))
        pts.append((TOOTH_ROOT_R * math.cos(a2), TOOTH_ROOT_R * math.sin(a2)))
    return Polygon(pts)
# Viewed from +z (the 606ZZ end): ramps rise counterclockwise, steep faces block CLOCKWISE.

def spool_ratchet():
    """Part coords = installed orientation. z0 face = screw heads, faces the motor."""
    d = extrude_polygon(ratchet_poly(), 6.0)
    return D(d, cyl(5.1, 8, -1), cyl(15.1, 2, 4.5),
             *[cyl(1.65, 8, -1, x, y) for x, y in BOLTS],
             *[cyl(3.1, 3.5, -0.5, x, y) for x, y in BOLTS])

def spool_body():
    """Installed orientation: boss z 4.5..6 (in disk recess), barrel 6..12, flange 12..14."""
    b = U(cyl(BARREL_D / 2, 6, 6), cyl(32, 2, 12), cyl(9, 8, 6), cyl(15, 1.5, 4.5))
    return D(b, cyl(HF0612_BORE / 2, 12, 3), *[cyl(1.25, 6.5, 4.4, x, y) for x, y in BOLTS])

def spool_body_print():
    b = spool_body().copy()
    b.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0])); b.apply_translation([0, 0, 14])
    return b

# ---------------- bracket ----------------
def bracket():
    base = U(bx(-24, 75, 0, 4, 0, 110), bx(-88, -24, 0, 3, 18, 93))
    motor = bx(-20, 20, 0, 62, 0, 4)
    brg = bx(-20, 20, 0, 62, 100, 106)

    def gusset(x, z0, z1, flip=False):
        tri = Polygon([(z0, 4), (z1, 4), ((z1 if flip else z0), 40)])
        g = extrude_polygon(tri, 4.0)
        g.apply_transform(np.array([[0, 0, 1, x], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]], float)); return g

    gs = [gusset(16, 4, 24), gusset(-20, 4, 24), gusset(16, 80, 100, True), gusset(-20, 80, 100, True)]
    tower = bx(40, 72, 4, 48, 22, 29)
    ledge = bx(36, 44, 4, 36, 35, 42)  # finger rests on this under load
    b = U(base, motor, brg, tower, ledge, *gs)
    cuts = [cyl(11.2, 10, -3, 0, AXIS_Y),                                                   # NEMA 11 pilot
            *[cyl(1.4, 10, -3, sx * 11.5, AXIS_Y + sy * 11.5) for sx in (-1, 1) for sy in (-1, 1)],
            cyl(BEARING_606 / 2, 20, 96, 0, AXIS_Y),                                         # 606ZZ
            bx(43.8, 67.2, 33.6, 46.4, 18, 33),                                              # SG90 pocket
            cyl(0.9, 20, 18, 41.5, AXIS_Y), cyl(0.9, 20, 18, 69.5, AXIS_Y),                  # SG90 tab screws
            vcyl(1.7, 10, -1, 65, 20), vcyl(1.7, 10, -1, 65, 90),                           # mount holes
            *[vcyl(1.6, 10, -1, x, z) for x in (-80, -56, -32) for z in (28, 83)],           # pad: 6 holes
            bx(-12, 12, -1, 5, 30, 90)]                                                      # window
    return D(b, *cuts)

# ---------------- line guide (new in Rev C) ----------------
def line_guide():
    """Bolts to the two x=-32 pad holes. 3.2 mm eyelet on the line exit (x=-25, z=45)."""
    g = U(bx(-36, -26, 3, 7, 20, 91), bx(-36, -26, 3, 76, 52, 60), bx(-36, -19, 70, 76, 39, 60))
    return D(g, vcyl(1.7, 10, 0, -32, 28), vcyl(1.7, 10, 0, -32, 83),
             vcyl(1.6, 10, 68, -25, 45),
             vcyl(2.6, 1.2, 69.4, -25, 45, 32), vcyl(2.6, 1.2, 75.4, -25, 45, 32))

def line_guide_print():
    g = line_guide().copy()   # lay on its x face: rail, post, arm all flat
    g.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [0, 1, 0]))
    g.apply_translation(-g.bounds[0]); return g

# ---------------- small parts ----------------
def finger():
    L = 20.5
    f = U(bx(-3, L, -3, 3, 0, 3), cyl(5, 3, 0))
    # tip taper: the half that faces the ramp is cut back so the tip seats deeper against the steep face
    taper = extrude_polygon(Polygon([(13, 3.01), (L + 0.1, 3.01), (L + 0.1, 0)]), 5.0); taper.apply_translation([0, 0, -1])
    return D(f, cyl(1.3, 10, -1), cyl(3.7, 1.6, -0.1), bx(0, 8, -2.1, 2.1, -0.1, 1.5), taper)

def tube(L): return D(cyl(5, L, 0), cyl(3.25, L + 2, -1))

PARTS = {
    "spool_body": spool_body_print,
    "spool_ratchet": spool_ratchet,
    "bracket": bracket,
    "line_guide": line_guide_print,
    "finger": finger,
    "spacer_A_6mm": lambda: tube(6),
    "spacer_B_50mm": lambda: tube(50),
    "shim_1mm": lambda: tube(1),
    "shim_2mm": lambda: tube(2),
}

# ---------------- installed assembly ----------------
def assembly():
    A = {}
    A["bracket"] = bracket()
    r = spool_ratchet(); r.apply_translation([0, AXIS_Y, Z_RATCHET]); A["spool_ratchet"] = r
    b = spool_body(); b.apply_translation([0, AXIS_Y, Z_RATCHET]); A["spool_body"] = b
    A["line_guide"] = line_guide()
    f = finger(); f.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [0, 0, 1]))
    f.apply_translation([SERVO_SHAFT_X, AXIS_Y, Z_RATCHET]); A["finger"] = f
    A["rod_6mm"] = cyl(3, 100, 20, 0, AXIS_Y)
    A["coupler"] = cyl(6, 20, 10, 0, AXIS_Y)
    A["spacer_A"] = D(cyl(5, 6, 30, 0, AXIS_Y), cyl(3.25, 8, 29, 0, AXIS_Y))
    A["spacer_B"] = D(cyl(5, 50, 50, 0, AXIS_Y), cyl(3.25, 52, 49, 0, AXIS_Y))
    A["bearing_606"] = D(cyl(8.5, 6, 100, 0, AXIS_Y), cyl(3, 8, 99, 0, AXIS_Y))
    A["motor_nema11"] = U(bx(-14, 14, AXIS_Y - 14, AXIS_Y + 14, -32, 0), cyl(2.5, 20, 0, 0, AXIS_Y))
    A["servo_sg90"] = U(bx(43.8, 67.2, 34, 46, 13, 29), bx(39.2, 71.8, 34, 46, 29, 31.5),
                        bx(43.8, 67.2, 34, 46, 31.5, 35), cyl(2.4, 1.5, 34.5, SERVO_SHAFT_X, AXIS_Y))
    return A

if __name__ == "__main__":
    for name, fn in PARTS.items():
        m = fn(); m.export(os.path.join(OUT, name + ".stl"))
        print(f"{name:15s} watertight={m.is_watertight} size={np.round(m.extents, 1).tolist()} vol={m.volume / 1000:.1f}cm3")
    A = assembly()
    print("--- clash check, overlap volume in mm3 (none listed = clear) ---")
    pairs = [(m, f) for m in ("spool_ratchet", "spool_body", "finger")
             for f in ("bracket", "line_guide", "servo_sg90", "motor_nema11", "coupler")]
    for m, f in pairs:
        v = I(A[m], A[f]).volume
        if v > 0.5: print(f"CLASH {m} x {f}: {v:.1f}")
    tip = A["finger"].vertices[:, 0].min()
    print(f"finger tip x = {tip:.1f}  (engaged if between root {TOOTH_ROOT_R} and tip {TOOTH_TIP_R}):",
          TOOTH_ROOT_R - 0.5 < tip < TOOTH_TIP_R)
    ring = trimesh.creation.annulus(r_min=TOOTH_TIP_R + 0.01, r_max=TOOTH_TIP_R + 2, height=16)
    ring.apply_translation([0, AXIS_Y, 43])   # spool spans z 36..50
    for k in ("bracket", "line_guide", "servo_sg90"):
        print(f"2 mm swept clearance, spool vs {k}: {I(ring, A[k]).volume:.1f} mm3 overlap")
