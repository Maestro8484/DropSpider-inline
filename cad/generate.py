"""
DropSpider - Mechanism A - In-Line Single-Axle Clutch Spool (ISCS) - Rev C
Parametric source for every printed part, plus an installed-assembly model used for
clash checks and renders.

Run:     python generate.py
Needs:   pip install -r tools/requirements.txt

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
HF0612_BORE = 10.0              # 10.0 OD one-way bearing; printed holes come out 0.1 to 0.2 small, which is the press (9.9 risked squeezing the rollers, fit check 2026-09-26)
BEARING_606 = 16.8              # 17.0 OD 606ZZ, 0.2 press (PLA)
Z_RATCHET = 36.0                # ratchet disk motor-side face (disk z 36..42); finger plate z 35..42
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
    return D(d, cyl(5.3, 8, -1), cyl(15.25, 2, 4.5),        # 10.6 hole over the HF0612 stub, 30.5 recess over the 30 boss (fit check 2026-09-26)
             *[cyl(1.65, 8, -1, x, y) for x, y in BOLTS],
             *[cyl(3.1, 3.5, -0.5, x, y) for x, y in BOLTS])

def spool_body():
    """Installed orientation: boss z 4.5..6 (in disk recess), barrel 6..12, flange 12..14."""
    b = U(cyl(BARREL_D / 2, 6, 6), cyl(32, 2, 12), cyl(9, 8, 6), cyl(15, 1.5, 4.5))
    return D(b, cyl(HF0612_BORE / 2, 12, 3), *[cyl(1.25, 8.0, 4.4, x, y) for x, y in BOLTS])   # M3x8 tip reaches z 11; pilot to 12.4

def spool_body_print():
    b = spool_body().copy()
    b.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0])); b.apply_translation([0, 0, 14])
    return b

# ---------------- bracket ----------------
def csk(x, z, head_d=6.4):
    """90 degree countersink for an M3 flat-head screw put in from the ceiling face (y = 0): widest at y 0."""
    c = trimesh.creation.cone(radius=head_d / 2 + 0.1, height=head_d / 2 + 0.1, sections=48)   # base at z 0, apex at +z
    c.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))      # +z -> +y (into the pad)
    c.apply_translation([x, -0.1, z])
    assert c.bounds[0][1] < 0 < c.bounds[1][1], c.bounds                                      # widest end at the ceiling face
    return c

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
            *[csk(-32, z) for z in (28, 83)],                                                 # fairlead screws: flat heads flush with the ceiling face
            bx(-12, 12, -1, 5, 30, 90)]                                                      # window
    return D(b, *cuts)

def bracket_print():
    """Base (ceiling face) down, the way the owner printed it."""
    b = bracket(); b.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    b.apply_translation(-b.bounds[0]); return b

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
SPLINE_D = 4.8        # SG90 output spline across the teeth (owner, 2026-09-26)
SOCKET_D = 5.0        # drawn socket: the owner's 4.8 printed as 4.5, so 5.0 prints about 4.7, a light press on the spline
HEAD_D = 7.4          # drawn screw-head recess: owner needs at least 7 mm printed
SPLINE_LEN = 3.4      # spline height above the servo case top (owner, 2026-09-26)
SPLINE_TIP_Z = 33.0   # installed z of the spline tip: owner saw it about 2 mm short of the ledge (z 35) with the servo in the tower
FINGER_Z0 = 35.0      # finger plate z 35..42, level with the ledge it rests on; the ratchet disk is z 36..42
def finger():
    """Rev C.1 finger, 7 mm wide, plate 7 mm thick (z 35..42, the ledge's full height, so a spline
    height off by 1 mm either way still leaves 5 mm of finger on the 6 mm disk). Tip face beveled
    20 degrees so the ramp-side corner sits 2.5 mm back (checked: seats in a tooth gap).
    No horn: a hub reaches down from the plate onto the SG90 spline. The spline tip bottoms on a
    1.5 mm floor, which sets the height; the horn screw goes in from the top through a 4.6 mm recess.
    Local coords: plate bottom z 0 (installed FINGER_Z0), top z 7; the hub hangs below z 0."""
    L, W, T = 20.5, 7.0, 7.0
    tip = SPLINE_TIP_Z - FINGER_Z0                      # -2.0: spline tip, local
    hub_bot = tip - SPLINE_LEN + 0.8                    # 0.8 mm clear of the servo case top
    f = U(bx(-3, L, -W / 2, W / 2, 0, T), cyl(5.5, T, 0), cyl(5.5, -hub_bot, hub_bot))   # hub 11 mm: 1.8 mm wall round the head recess
    dx = W * math.tan(math.radians(20))
    bevel = extrude_polygon(Polygon([(L - dx, W / 2 + 0.01), (L + 0.1, W / 2 + 0.01), (L + 0.1, -W / 2)]), T + 2)
    bevel.apply_translation([0, 0, -1])
    return D(f, cyl(SOCKET_D / 2, tip - hub_bot + 0.1, hub_bot - 0.1),   # spline socket, floor at the spline tip
             cyl(1.25, 3, tip - 1),                                         # 2.5 mm screw hole through the 1.5 mm floor
             cyl(HEAD_D / 2, T - (tip + 1.4) + 1, tip + 1.4),               # screw-head recess from the top, 7.6 deep
             # Stepped bridging: printed top-down, the floor is a roof over the recess. Its first 0.4 mm
             # bridges the recess as two strips beside a 2.5 slot, the next 0.4 bridges the slot leaving a
             # 2.5 square, then the round hole: every layer rests on the one below, nothing floats.
             bx(-HEAD_D / 2, HEAD_D / 2, -1.25, 1.25, tip + 1.0, tip + 1.4 + 0.01),
             bx(-1.25, 1.25, -1.25, 1.25, tip + 0.6, tip + 1.0 + 0.01),
             bevel)

def finger_print():
    m = finger(); m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
    m.apply_translation(-m.bounds[0]); return m        # flat top face down: recesses face up, no floating regions

SPACER_A_R = 6.0   # 12 OD: stops on the ratchet disk's face at z 36 (a 9.6 spacer fell into the 10.6 hole and left 2 mm of end play)
SPACER_B_R = 4.8   # 9.6 OD on the spool body face
SPACER_B_NOSE = 4.0   # 8.0 OD, last 1 mm at the 606ZZ end: bears on the inner ring only, not the shield
def tube(L, r=SPACER_A_R): return D(cyl(r, L, 0), cyl(3.25, L + 2, -1))
def spacer_b(): return D(U(cyl(SPACER_B_R, 49, 0), cyl(SPACER_B_NOSE, 1, 49)), cyl(3.25, 52, -1))   # nose up in print, no overhang

def fairlead_body_print():
    import fairlead as F
    m = F.fairlead_body(); m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [0, 1, 0]))
    m.apply_translation(-m.bounds[0]); return m

def fairlead_flap_print():
    import fairlead as F
    m = F.fairlead_flap(); m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))
    m.apply_translation(-m.bounds[0]); return m

def ld2450_fork_print():
    import sensor_mount as S
    return S.ld2450_fork_print()

def ld2450_cradle_print():
    import sensor_mount as S
    return S.ld2450_cradle_print()

PARTS = {
    "fairlead_body": fairlead_body_print,
    "fairlead_flap": fairlead_flap_print,
    "spool_body": spool_body_print,
    "spool_ratchet": spool_ratchet,
    "bracket": bracket_print,
    "finger": finger_print,
    "spacer_A_6mm": lambda: tube(6),
    "spacer_B_50mm": spacer_b,
    "shim_1mm": lambda: tube(1),
    "shim_2mm": lambda: tube(2),
    "ld2450_fork": ld2450_fork_print,
    "ld2450_cradle": ld2450_cradle_print,
}

# ---------------- installed assembly ----------------
def assembly():
    A = {}
    A["bracket"] = bracket()
    r = spool_ratchet(); r.apply_translation([0, AXIS_Y, Z_RATCHET]); A["spool_ratchet"] = r
    b = spool_body(); b.apply_translation([0, AXIS_Y, Z_RATCHET]); A["spool_body"] = b
    import fairlead as F
    A["fairlead_body"] = F.fairlead_body(); A["fairlead_flap"] = F.fairlead_flap(); A["switch_kw12"] = F.switch_model()
    import sensor_mount as S
    A["ld2450_fork"] = S.ld2450_fork(); A["ld2450_cradle"] = S.ld2450_cradle(); A["ld2450_radar"] = S.ld2450_board()
    f = finger(); f.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [0, 0, 1]))
    f.apply_translation([SERVO_SHAFT_X, AXIS_Y, FINGER_Z0]); A["finger"] = f
    A["rod_6mm"] = cyl(3, 100, 20, 0, AXIS_Y)
    A["coupler"] = cyl(6, 20, 10, 0, AXIS_Y)
    A["spacer_A"] = D(cyl(SPACER_A_R, 6, 30, 0, AXIS_Y), cyl(3.25, 8, 29, 0, AXIS_Y))
    sb = spacer_b(); sb.apply_translation([0, AXIS_Y, 50]); A["spacer_B"] = sb
    A["bearing_606"] = D(cyl(8.5, 6, 100, 0, AXIS_Y), cyl(3, 8, 99, 0, AXIS_Y))
    A["motor_nema11"] = U(bx(-14, 14, AXIS_Y - 14, AXIS_Y + 14, -32, 0), cyl(2.5, 20, 0, 0, AXIS_Y))
    # stand-in, not measured: the tabs sit on the tower (they fit, owner), the case top and spline
    # follow the owner's observation (spline 3.4 mm, tip about 2 mm short of the ledge)
    case_top = SPLINE_TIP_Z - SPLINE_LEN
    A["servo_sg90"] = U(bx(43.8, 67.2, 34, 46, 13, case_top), bx(39.2, 43.8, 34, 46, 29, 31.5), bx(67.2, 71.8, 34, 46, 29, 31.5),
                        cyl(2.4, SPLINE_LEN, case_top, SERVO_SHAFT_X, AXIS_Y))
    return A

if __name__ == "__main__":
    for name, fn in PARTS.items():
        m = fn(); m.export(os.path.join(OUT, name + ".stl"))
        print(f"{name:15s} watertight={m.is_watertight} size={np.round(m.extents, 1).tolist()} vol={m.volume / 1000:.1f}cm3")
    A = assembly()
    print("--- clash check, overlap volume in mm3 (none listed = clear) ---")
    pairs = [(m, f) for m in ("spool_ratchet", "spool_body", "finger")
             for f in ("bracket", "fairlead_body", "fairlead_flap", "switch_kw12", "servo_sg90", "motor_nema11", "coupler", "ld2450_fork", "ld2450_cradle")]
    for m, f in pairs:
        v = I(A[m], A[f]).volume
        if v > 0.5: print(f"CLASH {m} x {f}: {v:.1f}")
    tip = A["finger"].vertices[:, 0].min()
    print(f"finger tip x = {tip:.1f}  (engaged if between root {TOOTH_ROOT_R} and tip {TOOTH_TIP_R}):",
          TOOTH_ROOT_R - 0.5 < tip < TOOTH_TIP_R)
    seat = []
    for deg in np.arange(0, 360 / TEETH, 0.25):     # one tooth pitch is enough: the teeth repeat
        rr = A["spool_ratchet"].copy()
        rr.apply_transform(trimesh.transformations.rotation_matrix(math.radians(deg), [0, 0, 1], point=[0, AXIS_Y, 0]))
        if I(A["finger"], rr).volume < 0.05: seat.append(deg)
    print("finger seats in a tooth gap:", bool(seat),
          f"(window {seat[0]:.2f} to {seat[-1]:.2f} deg)" if seat else "(NO seating angle: finger or teeth changed badly)")
    ring = trimesh.creation.annulus(r_min=TOOTH_TIP_R + 0.01, r_max=TOOTH_TIP_R + 2, height=16)
    ring.apply_translation([0, AXIS_Y, 43])   # spool spans z 36..50
    for k in ("bracket", "fairlead_body", "servo_sg90", "ld2450_fork", "ld2450_cradle"):
        print(f"2 mm swept clearance, spool vs {k}: {I(ring, A[k]).volume:.1f} mm3 overlap")
