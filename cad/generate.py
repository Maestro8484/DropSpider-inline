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
HF0612_OD = 10.0                # the one-way bearing itself, 6 x 10 x 12
HF0612_BORE = 10.3              # its press hole in spool_body. 10.0 would not take the bearing, 10.2 was tight, 10.7 printed at 10.7 and was loose (owner 2026-09-28)
HF0612_STUB_HOLE = HF0612_BORE  # the disk's center hole over the bearing's 2 mm stub: same as the spool body's hole (owner 2026-09-28; was 11.0)
BEARING_606 = 17.0              # 17.0 OD 606ZZ drawn at size: holes print 0.1 to 0.2 small, which is the press (16.8 would not go in even with the bearing heated, owner 2026-09-27)
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
# Seen from behind the motor (from -z): ramps rise clockwise, steep faces block COUNTERCLOCKWISE (the way the spider's weight turns the spool).

# Light duty, so both spool parts are spoked to print fast (owner 2026-09-28): three spokes, one through each
# screw, and three through-windows between them. Solid only where something bears: the hub around the HF0612,
# a 1.6 skin under the line, the flange and the tooth ring. Through-windows need no bridging in either print
# orientation, and every face the other part, the line, the finger or spacer A touches is unchanged.
HUB_R = 9.0            # hub around the HF0612 (spool body) and the stub hole (disk); spacer A bears on the disk's hub
SHELL_R = 23.4         # inside of the barrel skin; the line sits at r 25, so the disk stays solid from here out too
SPOKE_W = 5.0
WINDOW_FILLET = 1.5    # rounded corners where spokes meet hub and rim

def spoke_window_polys(boss_r):
    """The three windows between hub and skin as flat outlines (part x, y), leaving spokes and a boss_r ring round each screw. Also drawn by render.py."""
    from shapely.geometry import Point, box as sbox
    from shapely.affinity import rotate
    from shapely.ops import unary_union
    ring = Point(0, 0).buffer(SHELL_R, 256).difference(Point(0, 0).buffer(HUB_R, 256))
    keep = unary_union([rotate(sbox(0, -SPOKE_W / 2, SHELL_R + 1, SPOKE_W / 2), math.degrees(math.atan2(y, x)), origin=(0, 0)) for x, y in BOLTS]
                       + [Point(x, y).buffer(boss_r, 64) for x, y in BOLTS])
    win = ring.difference(keep).buffer(-WINDOW_FILLET, 64).buffer(WINDOW_FILLET, 64)
    return list(getattr(win, "geoms", [win]))

def spoke_windows(boss_r, z0, h):
    """The three windows, as solids to cut."""
    out = []
    for p in spoke_window_polys(boss_r):
        s = extrude_polygon(p, h); s.apply_translation([0, 0, z0]); out.append(s)
    return out

# Rev C.2 spool stack (owner 2026-09-29): ratchet disk, shield disc, spool body, three plain plates sandwiched on
# flat faces only. No boss, recess or lip: the boss once left a 1 mm gap at the rim where the line could wedge. The
# ratchet is 7 thick with the teeth full height, so its spool-side face is one flat plane 1 mm above the finger's
# top (z 42); the shield, spool-flange size, lies on it and keeps the line off the teeth. Assembly: screw the three
# together first (flat faces clamp with nothing in the way), then press the HF0612 through all three 10.3 holes
# from the flange side. Every hole edge that prints on the bed gets a 0.4 chamfer so no first-layer lip can hold a
# face off its neighbour or catch the bearing.
RATCHET_T = 7.0        # teeth z 0..7; the finger (z 35..42 installed) engages the lower 6
SHIELD_R = 32.0        # same as the spool flange
SHIELD_T = 1.5
SHIELD_Z = RATCHET_T                  # local z of the shield's motor-side face (ratchet local frame, z 0 = motor face)
BODY_Z = SHIELD_Z + SHIELD_T          # local z of the spool body's flat face; barrel from here to 12, flange 12..14
CHAMFER = 0.4

def hole_chamfer(r, z_face, material_below, c=CHAMFER, e=0.05):
    """45 degree cone that breaks the edge of a round hole of radius r where it meets the face at z_face."""
    R = r + c + e
    k = trimesh.creation.cone(radius=R, height=R, sections=96)       # base at z 0, apex up
    if material_below:
        k.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0])); k.apply_translation([0, 0, z_face + e])
    else:
        k.apply_translation([0, 0, z_face - e])
    return k

def spool_ratchet():
    """Part coords = installed orientation. z0 face = screw heads, faces the motor; z 7 face = flat, on the shield."""
    d = extrude_polygon(ratchet_poly(), RATCHET_T)
    return D(d, cyl(HF0612_BORE / 2, RATCHET_T + 2, -1),                   # the HF0612 passes through, same hole as the spool body
             hole_chamfer(HF0612_BORE / 2, RATCHET_T, True),
             *[cyl(1.65, RATCHET_T + 2, -1, x, y) for x, y in BOLTS],
             *[cyl(3.1, 5.5, -0.5, x, y) for x, y in BOLTS],               # heads sit 5 deep so an M3x8 reaches 4.5 into the spool body
             *spoke_windows(4.6, -1, RATCHET_T + 2))                        # 1.5 wall round each screw-head counterbore

def spool_ratchet_print():
    """Flat shield face on the bed (the flattest face there is); counterbores open upward, so nothing to bridge."""
    m = spool_ratchet(); m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0])); m.apply_translation([0, 0, RATCHET_T]); return m

def spool_shield():
    """Flat 1.5 disc, spool-flange size, between the ratchet and the spool body; keeps the line off the teeth.
    Symmetric, so either face and any of the three screw positions fits."""
    d = cyl(SHIELD_R, SHIELD_T, 0)
    return D(d, cyl(HF0612_BORE / 2, 3, -1), hole_chamfer(HF0612_BORE / 2, 0, False), hole_chamfer(HF0612_BORE / 2, SHIELD_T, True),
             *[cyl(1.65, 3, -1, x, y) for x, y in BOLTS], *spoke_windows(4.6, -1, 3))

def spool_body():
    """Installed orientation: flat face at BODY_Z (on the shield), barrel BODY_Z..12, flange 12..14 (on the bed)."""
    b = U(cyl(BARREL_D / 2, 12 - BODY_Z, BODY_Z), cyl(32, 2, 12), cyl(9, 14 - BODY_Z, BODY_Z))
    return D(b, cyl(HF0612_BORE / 2, 12, 3), hole_chamfer(HF0612_BORE / 2, 14, True),   # lead-in where the bearing is pressed in
             *[cyl(1.25, 8.0, BODY_Z - 0.5, x, y) for x, y in BOLTS],   # pilots right through; M3x8 tip reaches z 13
             *spoke_windows(3.5, 3, 12))                                    # 2.25 wall round each screw pilot

def spool_shield_print():
    return spool_shield()

def spool_body_print():
    b = spool_body().copy()
    b.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0])); b.apply_translation([0, 0, 14])   # flange on the bed
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
            bx(-12, 12, -1, 5, 30, 90),                                                      # window
            # inverted install (inverted.py, doc 06), printed in rather than drilled (owner 2026-09-28):
            vcyl(3.5, 10, -1, 25, 45),                                                       # line pass-through, 7 mm, under the barrel's servo edge
            *[vcyl(1.8, 10, -1, 32, z) for z in (28, 83)],                                   # fairlead block, 2x M3 (3.6 prints about 3.4)
            *[vcyl(1.8, 10, -1, 62, z) for z in (45, 79)]]                                   # radar fork, 2x M3
    return D(b, *cuts)

# 606ZZ retainer (owner 2026-09-29): on a bracket whose seat went loose after heating the bearing in, a thin plate
# on the end plate's outer face (z 106) stops the 606ZZ walking out. The 14.5 mm hole (owner) clears everything that turns and
# the rod (which runs on about 14 mm past the plate); the plate overlaps only the outer ring's rim, r 7.25 to 8.5. One M3 each side at
# x +-14, y 40, into 2.5 mm pilots drilled through the 6 mm end plate using the retainer as the template.
RET_T = 2.0
RET_X = 14.0
def bearing_retainer():
    """Installed position: z 106..108 on the end plate's outer face, centred on the rod."""
    from shapely.geometry import LineString
    outline = LineString([(-RET_X, AXIS_Y), (RET_X, AXIS_Y)]).buffer(9.0, 64)      # 46 x 18 rounded bar, inside the 40 wide end plate at the screws
    outline = outline.intersection(Polygon([(-19.5, 0), (19.5, 0), (19.5, 62), (-19.5, 62)]))
    plate = extrude_polygon(outline, RET_T); plate.apply_translation([0, 0, 106])
    return D(plate, cyl(7.25, RET_T + 2, 105, 0, AXIS_Y),                           # 14.5 mm: the plate holds only the outer ring's rim, 1.25 mm of it (owner)
             *[cyl(1.8, RET_T + 2, 105, sx * RET_X, AXIS_Y) for sx in (-1, 1)])        # M3 clearance, prints about 3.4

def bearing_retainer_print():
    m = bearing_retainer(); m.apply_translation([0, -AXIS_Y, -106]); return m

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

SPACER_A_R = 6.0   # 12 OD: stops on the ratchet disk's face at z 36 (a 9.6 spacer fell into the disk's center hole, then 10.6, and left 2 mm of end play)
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
    "spool_ratchet": spool_ratchet_print,
    "spool_shield": spool_shield_print,
    "bearing_retainer": bearing_retainer_print,
    "bracket": bracket_print,
    "finger": finger_print,
    "spacer_A_6mm": lambda: tube(6),
    "spacer_B_50mm": spacer_b,
    "shim_1mm": lambda: tube(1),
    "shim_2mm": lambda: tube(2),
    "ld2450_cradle": ld2450_cradle_print,
    "ld2450_fork_screw": lambda: __import__("sensor_mount").ld2450_fork_screw_print(),   # the radar fork, both installs: 2x M3, no glue (owner 2026-09-27; the glued ld2450_fork is retired)
    "fairlead_base": lambda: __import__("inverted").fairlead_base_print(),
    "fairlead_flap_inv": lambda: __import__("inverted").fairlead_flap_inv_print(),   # inverted install only: doc 09 flap plus the tab under the switch roller (2026-09-28)             # inverted install only (docs/06): fairlead block under the base
}

# ---------------- installed assembly ----------------
def assembly():
    A = {}
    A["bracket"] = bracket()
    r = spool_ratchet(); r.apply_translation([0, AXIS_Y, Z_RATCHET]); A["spool_ratchet"] = r
    b = spool_body(); b.apply_translation([0, AXIS_Y, Z_RATCHET]); A["spool_body"] = b
    s = spool_shield(); s.apply_translation([0, AXIS_Y, Z_RATCHET + SHIELD_Z]); A["spool_shield"] = s
    import fairlead as F
    A["fairlead_body"] = F.fairlead_body(); A["fairlead_flap"] = F.fairlead_flap(); A["switch_kw12"] = F.switch_model()
    import sensor_mount as S
    A["ld2450_fork"] = S.ld2450_fork_screw();   # bolted fork (key kept for the checks below)
    A["ld2450_cradle"] = S.ld2450_cradle(); A["ld2450_radar"] = S.ld2450_board()
    f = finger(); f.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [0, 0, 1]))
    f.apply_translation([SERVO_SHAFT_X, AXIS_Y, FINGER_Z0]); A["finger"] = f
    A["rod_6mm"] = cyl(3, 100, 20, 0, AXIS_Y)
    A["coupler"] = cyl(6, 20, 10, 0, AXIS_Y)
    A["spacer_A"] = D(cyl(SPACER_A_R, 6, 30, 0, AXIS_Y), cyl(3.25, 8, 29, 0, AXIS_Y))
    sb = spacer_b(); sb.apply_translation([0, AXIS_Y, 50]); A["spacer_B"] = sb
    A["bearing_606"] = D(cyl(8.5, 6, 100, 0, AXIS_Y), cyl(3, 8, 99, 0, AXIS_Y))
    A["bearing_retainer"] = bearing_retainer()
    A["hf0612"] = D(cyl(HF0612_OD / 2, 12, 38, 0, AXIS_Y), cyl(3, 14, 37, 0, AXIS_Y))   # one-way bearing 6 x 10 x 12, flush with the spool flange (z 50), 2 mm stub into the disk (doc 05 step 1)
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
