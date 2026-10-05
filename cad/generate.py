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

# Rev C.3 one-piece spool (handoff_spool_onepiece.md, 2026-10-02): ratchet, separator, barrel as one part, no
# screws. Prints ratchet face down with no supports: everything above the teeth is smaller than them. Part z 0 =
# motor face, installed at OP_Z0, print orientation = installed orientation. The separator is r 28, inside the
# finger's reach (closest r 29.4), so the finger can overlap it along the rod and never touch it; the teeth are the
# finger plate's 7 mm and sit across it. The HF0612 (owner measured 9.99 across, 11.89 long) is held both ways: a
# printed shoulder on the motor side, and a small snap lip at the far face that it is pressed past. Line anchor
# printed in: the hole doc 05 step 5 drilled by hand.
# Rev C.4 (handoff_spool_rev_c4.md, 2026-10-04): the line came off the far side over the C.3 flange, a 2 mm wall
# that was a 45 degree ramp, and the line's feed point (z 45) landed on that ramp, 0.5 past the barrel. Now the
# separator is 3.75 thick so the barrel is centred on z 45, the body ends flat at the barrel's far edge, and the
# far wall is a separate flat cap (spool_cap): a 2 mm disc, r 32, 7 mm above the barrel, screwed to the body's spokes
# with 3x M3x8 (owner 2026-10-05: a cap held only by the rod stack can lift up to the stack's end play, and a 0.29 mm
# thread walks into that crack at the barrel's corner; the stack must stay snug, not tight, so the spool spins free).
OP_Z0 = 32.5           # installed z of the motor face = FINGER_Z0, so the teeth sit across the finger plate
OP_TEETH_T = 7.0       # teeth z 0..7, the finger plate's thickness
OP_SEP_R, OP_SEP_T = 28.0, 3.75       # separator z 7..10.75 (C.3: 1.5), so the barrel is centred on the line at z 45
OP_BARREL_W = 3.5      # flat barrel z 10.75..14.25, r 25 (same width as the Rev C.2 barrel); the body ends here, flat
HF0612_LEN = 11.89     # owner measured 2026-10-02 (9.99 across)
OP_SEAT_L = 12.0       # shoulder to the far face: 0.1 longer than the bearing, which the cap then covers
# No snap lip (owner 2026-10-05: the C.3 lip printed too tight, he carved it out with a deburring tool; "the entire
# bushing should just be the narrower smaller diameter"). The hole is one plain diameter, OP_BORE, from the shoulder
# right through the far face, with a 0.4 lead-in chamfer. The cap's centre hole clears spacer B, which passes through it
# and bears on the bearing's far end (owner 2026-10-05: the rod spacers touch the spool only at the bearing, never the
# cap's plastic; he opened his printed cap's hole to 10 mm). The press fit and spacer B keep the bearing in.
OP_BARREL_Z0 = OP_TEETH_T + OP_SEP_T
OP_L = OP_BARREL_Z0 + OP_BARREL_W     # 14.25: the body ends at the barrel's far edge (C.3 was 14.5 with the ramp and rim)
CAP_R, CAP_T = 32.0, 2.0              # far wall: flat disc, 7 above the barrel (the Rev C.2 flange's r 32), on the body's far face
CAP_HOLE_D = 11.0                     # clears spacer B's 9.6 end by 0.7 a side (prints about 0.55): spacer B passes through and bears on the bearing, not the cap
CAP_LUG_H = 1.5                       # three lugs, 1.5 tall (owner 2026-10-05: no higher than needed), on the cap's line-side face drop into the spoke windows (owner 2026-10-05: keep them, they
CAP_LUG_R0, CAP_LUG_R1 = 11.0, 19.0   # align the cap and hold the anchored string in its window); clear of the hub (r 9) and the stub at the skin
CAP_LUG_CLR = 0.4                     # drawn gap, lug side to spoke side (windows print 0.1 to 0.2 small a side, so about 0.2 real)
CAP_SCREW_D = 3.4                     # the cap's three screw holes, on the bolt circle (r 21, one per spoke): M3 clearance
CAP_BOSS_R = 3.5                      # boss round each pilot in the body (the windows are cut leaving it), as the Rev C.2 spool body
CAP_PILOT_D, CAP_PILOT_L = 2.5, 8.0   # M3x8 pilots into the spokes from the far face: 6 mm of thread under the 2 mm cap; 2.25 wall round each
OP_BORE = 10.2         # plain press hole for the HF0612 (owner 2026-10-01: 10.3 slips under more than the spider's weight)
OP_SHOULDER_R = 3.5    # hole under the bearing: 7.0 clears the 6 rod, so spacer A's 8 mm nose bears on the face round it (owner 2026-10-02)
OP_ANCHOR_D = 1.2      # line hole, teardrop point up so its roof prints
OP_ANCHOR_DEG = 60.0   # midway between the spokes at 0 and 120: a window lies behind the skin
OP_ANCHOR_LEAN = 45.0  # leans counterclockwise (seen from behind the motor), the way the line wraps off the hole while winding

def anchor_hole():
    """Teardrop line hole through the barrel skin, mid-width, leaning counterclockwise (seen from behind the motor),
    with a 0.4 chamfer at the outside so the edge cannot nick the line. Returns (cutters, inner end point, axis)."""
    a, lean = math.radians(OP_ANCHOR_DEG), math.radians(OP_ANCHOR_LEAN)
    zc = OP_BARREL_Z0 + OP_BARREL_W / 2
    rad = np.array([math.cos(a), math.sin(a), 0.0]); tan_ccw = np.array([math.sin(a), -math.cos(a), 0.0])   # -angle about +z = counterclockwise from behind the motor
    ax = rad * math.cos(lean) + tan_ccw * math.sin(lean)                                                    # outward along the hole
    p_out = rad * (BARREL_D / 2) + np.array([0, 0, zc])                                                    # where the hole meets the barrel
    r = OP_ANCHOR_D / 2
    tear = Polygon([(r * math.cos(t), r * math.sin(t)) for t in np.linspace(math.pi * 0.25, math.pi * 1.75, 40)] + [(r * math.sqrt(2), 0)])
    # local frame of the hole: X = +z (so the point at +X is up in print), Y = across, Z = along the axis
    Y = np.cross(ax, [0, 0, 1.0]); Y /= np.linalg.norm(Y); X = np.cross(Y, ax)
    M = np.eye(4); M[:3, 0], M[:3, 1], M[:3, 2] = X, Y, ax
    L = 8.0
    h = extrude_polygon(tear, L); h.apply_translation([0, 0, -L + 1.0]); M2 = M.copy(); M2[:3, 3] = p_out; h.apply_transform(M2)
    c = trimesh.creation.cone(radius=r + CHAMFER + 0.6, height=r + CHAMFER + 0.6, sections=48)
    c.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))                  # apex inward
    M3 = M.copy(); M3[:3, 3] = p_out + ax * 0.6; c.apply_transform(M3)                              # r + 0.4 where it meets the barrel
    p_in = p_out - ax * ((BARREL_D / 2 - SHELL_R) / (rad @ ax))                                     # about where it leaves the skin's inside
    return [h, c], p_in, ax

def spool_onepiece():
    """Installed orientation = print orientation: motor face (z 0) on the bed."""
    body = U(extrude_polygon(ratchet_poly(), OP_TEETH_T),
             cyl(OP_SEP_R, OP_SEP_T, OP_TEETH_T),
             cyl(BARREL_D / 2, OP_BARREL_W, OP_BARREL_Z0, sections=192))
    seat_z0 = OP_L - OP_SEAT_L                              # shoulder; the bearing ends 0.11 below the far face, under the cap
    cuts = [cyl(OP_BORE / 2, OP_SEAT_L + 1, seat_z0), cyl(OP_SHOULDER_R, seat_z0 + 1.01, -1),
            hole_chamfer(OP_BORE / 2, OP_L, True),          # 0.4 lead-in at the far face: the bearing presses in from here
            hole_chamfer(OP_SHOULDER_R, 0, False, c=0.2),   # bed side: no first-layer lip under spacer A's nose (0.2, so the nose keeps r 3.7 to 4.0)
            *spoke_windows(CAP_BOSS_R, -1, OP_L + 2),       # windows leave a 3.5 boss round each cap screw pilot
            *[cyl(CAP_PILOT_D / 2, CAP_PILOT_L + 1, OP_L - CAP_PILOT_L, x, y) for x, y in BOLTS],   # cap screw pilots, 8 deep from the far face
            *anchor_hole()[0]]
    return D(body, *cuts)

def cap_lug_polys():
    """The three lugs as flat outlines: each spoke window shrunk by CAP_LUG_CLR all round, kept to the band r 11 to 19,
    so every lug side runs parallel to its spoke 0.4 away and the lug drops in by hand. Same angular places as the
    windows (midway between the spokes at 0, 120 and 240 degrees)."""
    from shapely.geometry import Point
    band = Point(0, 0).buffer(CAP_LUG_R1, 256).difference(Point(0, 0).buffer(CAP_LUG_R0, 256))
    out = []
    for w in spoke_window_polys(CAP_BOSS_R):
        p = w.buffer(-CAP_LUG_CLR, 64).intersection(band)
        out += list(getattr(p, "geoms", [p]))
    return out

def spool_cap():
    """Rev C.4 far wall, in the body's frame: a flat disc r 32, CAP_T thick, its line-side face at z OP_L (on the body's
    far face), three lugs reaching down into the spoke windows to z OP_L - CAP_LUG_H (they align the cap and hold the
    anchored string in its window), centre hole 11.0 (spacer B passes through to the bearing) and three 3.4 screw holes on the bolt circle, all chamfered
    both faces. 3x M3x8 through it into the body's spokes clamp the seam shut; spacer B passes through its centre hole."""
    disc = cyl(CAP_R, CAP_T, OP_L, sections=192)
    lugs = [extrude_polygon(p, CAP_LUG_H + 0.01).apply_translation([0, 0, OP_L - CAP_LUG_H]) for p in cap_lug_polys()]
    m = U(disc, *lugs)
    holes = [cyl(CAP_HOLE_D / 2, CAP_T + CAP_LUG_H + 2, OP_L - CAP_LUG_H - 1)] + [cyl(CAP_SCREW_D / 2, CAP_T + 2, OP_L - 1, x, y) for x, y in BOLTS]
    ch = [hole_chamfer(CAP_HOLE_D / 2, OP_L + CAP_T, True), hole_chamfer(CAP_HOLE_D / 2, OP_L, False)]
    ch += [k for x, y in BOLTS for k in (hole_chamfer(CAP_SCREW_D / 2, OP_L + CAP_T, True).apply_translation([x, y, 0]),
                                         hole_chamfer(CAP_SCREW_D / 2, OP_L, False).apply_translation([x, y, 0]))]
    return D(m, *holes, *ch)

def spool_cap_print():
    """Outer face (spacer B side) on the bed, lugs up: nothing hangs over air. Flipped about x; the windows are symmetric
    about the x axis (spokes at 0, 120, 240), so the lugs and screw holes still land in place."""
    m = spool_cap(); m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0])); m.apply_translation([0, 0, OP_L + CAP_T]); return m

def cap_screws():
    """3x M3x8 pan heads in the body's frame: shank r 1.5 from the head's underside down into the pilot, head 5.5 across, 2.5 tall."""
    out = []
    for x, y in BOLTS:
        out.append(U(cyl(1.5, 8.0, OP_L + CAP_T - 8.0, x, y), cyl(2.75, 2.5, OP_L + CAP_T, x, y)))
    return out

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
# on the end plate's outer face (z 106) stops the 606ZZ walking out. The 12 mm hole (owner) clears the turning inner ring and
# the rod (which runs on about 14 mm past the plate); the rim overlaps the outer ring by 2.5 mm. One M3 each side at
# x +-14, y 40, into 2.5 mm pilots drilled through the 6 mm end plate using the retainer as the template.
RET_T = 2.0
RET_X = 14.0
def bearing_retainer():
    """Installed position: z 106..108 on the end plate's outer face, centred on the rod."""
    from shapely.geometry import LineString
    outline = LineString([(-RET_X, AXIS_Y), (RET_X, AXIS_Y)]).buffer(9.0, 64)      # 46 x 18 rounded bar, inside the 40 wide end plate at the screws
    outline = outline.intersection(Polygon([(-19.5, 0), (19.5, 0), (19.5, 62), (-19.5, 62)]))
    plate = extrude_polygon(outline, RET_T); plate.apply_translation([0, 0, 106])
    return D(plate, cyl(6.0, RET_T + 2, 105, 0, AXIS_Y),                            # 12 mm (owner confirmed): clears the rod and the turning inner ring
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
FLOOR_T = 3.5         # screw-head seat to spline tip (owner 2026-10-02: 1.5 was too thin for the horn screw, +2)
FINGER_Z0 = 32.5      # finger plate z 32.5..39.5 (owner 2026-10-02: hub 2.5 shorter, finger 2.5 nearer the servo, plate still 7); was 35..42, level with the ledge (z 35..42)
def finger():
    """Rev C.1 finger, 7 mm wide, plate 7 mm thick (z 35..42, the ledge's full height, so a spline
    height off by 1 mm either way still leaves 5 mm of finger on the 6 mm disk). Tip face beveled
    20 degrees so the ramp-side corner sits 2.5 mm back (checked: seats in a tooth gap).
    No horn: a hub reaches down from the plate onto the SG90 spline. The spline tip bottoms on a
    3.5 mm floor (was 1.5, too thin for the horn screw), which sets the height; the horn screw goes in from the top through the recess.
    Local coords: plate bottom z 0 (installed FINGER_Z0), top z 7; the hub hangs below z 0."""
    L, W, T = 20.5, 7.0, 7.0
    tip = SPLINE_TIP_Z - FINGER_Z0                      # +0.5: spline tip, local (was -2.0 before the hub was shortened 2.5)
    hub_bot = tip - SPLINE_LEN + 0.8                    # 0.8 mm clear of the servo case top
    f = U(bx(-3, L, -W / 2, W / 2, 0, T), cyl(5.5, T, 0), cyl(5.5, -hub_bot, hub_bot))   # hub 11 mm: 1.8 mm wall round the head recess
    dx = W * math.tan(math.radians(20))
    bevel = extrude_polygon(Polygon([(L - dx, W / 2 + 0.01), (L + 0.1, W / 2 + 0.01), (L + 0.1, -W / 2)]), T + 2)
    bevel.apply_translation([0, 0, -1])
    return D(f, cyl(SOCKET_D / 2, tip - hub_bot + 0.1, hub_bot - 0.1),   # spline socket, floor at the spline tip
             cyl(1.25, FLOOR_T + 2, tip - 1),                               # 2.5 mm screw hole through the floor
             cyl(HEAD_D / 2, T - (tip + FLOOR_T) + 1, tip + FLOOR_T),       # screw-head recess from the top
             # Stepped bridging: printed top-down, the floor is a roof over the recess. Its first 0.4 mm
             # bridges the recess as two strips beside a 2.5 slot, the next 0.4 bridges the slot leaving a
             # 2.5 square, then the round hole: every layer rests on the one below, nothing floats.
             bx(-HEAD_D / 2, HEAD_D / 2, -1.25, 1.25, tip + FLOOR_T - 0.4, tip + FLOOR_T + 0.01),
             bx(-1.25, 1.25, -1.25, 1.25, tip + FLOOR_T - 0.8, tip + FLOOR_T - 0.4 + 0.01),
             bevel)

def finger_print():
    m = finger(); m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
    m.apply_translation(-m.bounds[0]); return m        # flat top face down: recesses face up, no floating regions

SPACER_A_R = 6.0   # 12 OD: stops on the ratchet disk's face at z 36 (a 9.6 spacer fell into the disk's center hole, then 10.6, and left 2 mm of end play)
SPACER_B_R = 4.8   # 9.6 OD on the spool body face
SPACER_B_NOSE = 4.0   # 8.0 OD, last 1 mm at the 606ZZ end: bears on the inner ring only, not the shield
def tube(L, r=SPACER_A_R): return D(cyl(r, L, 0), cyl(3.25, L + 2, -1))
SPACER_A_NOSE_L = 7.5   # owner's build: spacer A 6 + 4 mm shim (doc 05 step 9) less 2.5 for the shorter finger hub (2026-10-02)
def spacer_a_nose(L=SPACER_A_NOSE_L):
    """Motor-side spacer like spacer B: 12 OD on the coupler, last 1 mm 8 OD so it bears on the one-piece spool's face
    close to the rod (small rubbing radius while the spool freewheels). Nose up in print, no overhang."""
    return D(U(cyl(SPACER_A_R, L - 1, 0), cyl(SPACER_B_NOSE, 1, L - 1)), cyl(3.25, L + 2, -1))
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
    "spool_onepiece": spool_onepiece,                                  # Rev C.3, replaces the three above once the owner has it in hand
    "spool_cap": spool_cap_print,                                      # Rev C.4 far wall on the one-piece: flat disc, three lugs into the windows, 3x M3x8 into the spokes
    "bearing_retainer": bearing_retainer_print,
    "bracket": bracket_print,
    "finger": finger_print,
    "spacer_A_6mm": lambda: tube(6),
    "spacer_B_50mm": spacer_b,
    "spacer_A_nose_7_5mm": spacer_a_nose,                              # motor side, with spool_onepiece
    "shim_1mm": lambda: tube(1),
    "shim_2mm": lambda: tube(2),
    "ld2450_cradle": ld2450_cradle_print,
    "ld2450_fork_screw": lambda: __import__("sensor_mount").ld2450_fork_screw_print(),   # the radar fork, both installs: 2x M3, no glue (owner 2026-09-27; the glued ld2450_fork is retired)
    "fairlead_base": lambda: __import__("inverted").fairlead_base_print(),
    "fairlead_base_ptfe": lambda: __import__("inverted").fairlead_base_print(ptfe=True, windows=False),   # same block, straight 4.3 bore for the 4 mm PTFE guide tube (2026-10-04); no lightening windows (owner 2026-10-05: print time beats material)
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

def onepiece_checks(A):
    """Rev C.4 one-piece spool and its cap in place of the three-part stack, with spacer A 2.5 and spacer B from the bearing's far end to z 100."""
    print("--- one-piece spool (spool_onepiece) and cap (spool_cap), Rev C.4 ---")
    P = spool_onepiece(); C = spool_cap()
    sp = P.copy(); sp.apply_translation([0, AXIS_Y, OP_Z0])
    cp = C.copy(); cp.apply_translation([0, AXIS_Y, OP_Z0])
    both = U(sp, cp)
    L = OP_L + CAP_T
    near = dict(A)
    hz = OP_Z0 + OP_L - OP_SEAT_L
    near["hf0612"] = D(cyl(HF0612_OD / 2 - 0.01, HF0612_LEN, hz + 0.05, 0, AXIS_Y), cyl(3, 14, hz - 1, 0, AXIS_Y))
    near["spacer_A"] = spacer_a_nose(OP_Z0 - 30); near["spacer_A"].apply_translation([0, AXIS_Y, 30])
    face = I(near["spacer_A"].copy().apply_translation([0, 0, 0.05]), sp).volume / 0.05
    print(f"spacer A's 8 mm nose on the spool's motor face: {face:.1f} mm2 of contact (nose r {SPACER_B_NOSE}, hole r {OP_SHOULDER_R} + 0.2 chamfer)")
    bz_end = hz + HF0612_LEN                                  # the bearing's far end: spacer B bears here, through the cap's hole
    near["spacer_B"] = D(cyl(SPACER_B_R, 100 - bz_end, bz_end, 0, AXIS_Y), cyl(3.25, 60, bz_end - 1, 0, AXIS_Y))
    sbB = near["spacer_B"].copy().apply_translation([0, 0, -0.05])
    faceB = I(sbB, near["hf0612"]).volume / 0.05
    plastic = I(sbB, both).volume
    wob = 0.25                                                # spacer B's 6.5 bore on the 6 rod: it can sit 0.25 off centre
    print(f"spacer B's 9.6 end through the cap's {CAP_HOLE_D} hole onto the bearing's far end: {faceB:.1f} mm2 on the bearing, {plastic:.2f} mm3 on the spool's plastic "
          f"(pass 0); radial gap to the cap hole {CAP_HOLE_D / 2 - SPACER_B_R:.2f} drawn, {CAP_HOLE_D / 2 - SPACER_B_R - wob:.2f} with the spacer pushed {wob} off centre; "
          f"to the body's bore {OP_BORE / 2 - SPACER_B_R:.2f}")
    print(f"body z {OP_Z0:.2f} to {OP_Z0 + OP_L:.2f} ({OP_L:.2f}), cap to {OP_Z0 + L:.2f} ({L:.2f} in all); spacer A {OP_Z0 - 30:.2f}, spacer B {100 - bz_end:.2f} "
          f"from the bearing's end at z {bz_end:.2f} (the C.3 stack fills 53.0: {100 - bz_end - 53.0:.2f} of play with it unchanged, pass under 0.5)")
    bz0, bz1 = OP_Z0 + OP_BARREL_Z0, OP_Z0 + OP_L
    import inverted as V
    print(f"barrel flat z {bz0:.2f} to {bz1:.2f}, line feed point z {V.LINE_Z:.1f}: {V.LINE_Z - bz0:.2f} from the separator, {bz1 - V.LINE_Z:.2f} from the cap; "
          f"centred with 1 mm to spare each side: {V.LINE_Z - bz0 >= 1.0 and bz1 - V.LINE_Z >= 1.0}")
    print(f"cap wall {CAP_R - BARREL_D / 2:.1f} above the barrel, separator wall {OP_SEP_R - BARREL_D / 2:.1f} (C.3 far wall was 2.0, a ramp)")
    for f in ("bracket", "fairlead_body", "fairlead_flap", "switch_kw12", "servo_sg90", "motor_nema11", "coupler", "ld2450_fork", "ld2450_cradle",
              "hf0612", "spacer_A", "spacer_B", "rod_6mm", "bearing_606"):
        v = I(sp, near[f]).volume
        if v > 0.05: print(f"CLASH spool_onepiece x {f}: {v:.2f}")
        v = I(cp, near[f]).volume
        if v > 0.05: print(f"CLASH spool_cap x {f}: {v:.2f}")
    fit = I(sp, cp).volume
    print(f"cap lugs drop into the spoke windows, cap flat on the body's far face (overlap {fit:.2f} mm3): {fit < 0.01}")
    bind = None
    for deg in np.arange(0.25, 6.0, 0.25):
        rr = cp.copy(); rr.apply_transform(trimesh.transformations.rotation_matrix(math.radians(deg), [0, 0, 1], point=[0, AXIS_Y, 0]))
        if I(sp, rr).volume > 0.5: bind = deg; break
    lugs = cap_lug_polys()
    print(f"three lugs ({len(lugs)}), {min(p.area for p in lugs):.0f} mm2 each, r {CAP_LUG_R0} to {CAP_LUG_R1}, {CAP_LUG_H} deep: they meet the spokes at {bind} deg of play (drawn {CAP_LUG_CLR} a side), so the lugs align the cap and the screws clamp it")
    screws = [m.copy().apply_translation([0, AXIS_Y, OP_Z0]) for m in cap_screws()]
    thru = max(I(cp, m).volume for m in screws)
    wall = []
    for x, y in BOLTS:
        ring = D(cyl(CAP_PILOT_D / 2 + 2.0, CAP_PILOT_L, OP_L - CAP_PILOT_L, x, y), cyl(CAP_PILOT_D / 2 + 0.01, CAP_PILOT_L + 1, OP_L - CAP_PILOT_L - 0.5, x, y))
        wall.append(I(P, ring).volume / ring.volume)
    print(f"cap screws: 3x M3x8 pass the cap's 3.4 holes ({thru:.2f} mm3 overlap), pilots {CAP_PILOT_D} x {CAP_PILOT_L} deep into the spokes, "
          f"material within 2 mm round each pilot {100 * min(wall):.0f}% full (boss r {CAP_BOSS_R}, so a {CAP_BOSS_R - CAP_PILOT_D / 2:.2f} wall)")
    heads = U(*[cyl(2.75, 2.5, OP_Z0 + OP_L + CAP_T, x, AXIS_Y + y) for x, y in BOLTS])
    hits = [f for f in ("spacer_B", "rod_6mm", "bearing_606", "bracket", "servo_sg90", "finger") if I(heads, near[f]).volume > 0.05]
    print(f"screw heads (5.5 across, 2.5 tall) on the cap's outer face at r {BOLT_R}: {'clear of everything' if not hits else 'HIT ' + str(hits)}")
    fv = A["finger"].vertices
    rmin = np.min(np.hypot(fv[:, 0], fv[:, 1] - AXIS_Y))
    print(f"finger tip closest r {rmin:.2f}, separator r {OP_SEP_R}: {rmin - OP_SEP_R:.2f} mm apart, so no contact at any slide along the rod; cap r {CAP_R} starts {OP_Z0 + OP_L - (FINGER_Z0 + 7):.2f} past the finger plate")
    print(f"teeth z {OP_Z0:.1f} to {OP_Z0 + OP_TEETH_T:.1f} cover the finger plate z {FINGER_Z0:.1f} to {FINGER_Z0 + 7:.1f}:",
          OP_Z0 <= FINGER_Z0 and OP_Z0 + OP_TEETH_T >= FINGER_Z0 + 7)
    rest = D(both, cyl(40, OP_TEETH_T, OP_Z0, 0, AXIS_Y))
    slid = [I(A["finger"], rest.copy().apply_translation([0, 0, dz])).volume for dz in (-5, -2.5, 0, 2.5, 5)]
    print("finger vs separator, barrel, cap with the part slid -5 to +5 mm:", "clear" if max(slid) < 0.01 else f"TOUCHES {np.round(slid, 2)}")
    seat = []
    for deg in np.arange(0, 360 / TEETH, 0.25):
        rr = sp.copy(); rr.apply_transform(trimesh.transformations.rotation_matrix(math.radians(deg), [0, 0, 1], point=[0, AXIS_Y, 0]))
        if I(A["finger"], rr).volume < 0.05: seat.append(deg)
    print("finger seats in a tooth gap:", bool(seat), f"(window {seat[0]:.2f} to {seat[-1]:.2f} deg)" if seat else "(NO seating angle)")
    ring = trimesh.creation.annulus(r_min=TOOTH_TIP_R + 0.01, r_max=TOOTH_TIP_R + 2, height=L); ring.apply_translation([0, AXIS_Y, OP_Z0 + L / 2])
    print("2 mm swept clearance (teeth and cap):", ", ".join(f"{k} {I(ring, A[k]).volume:.1f}" for k in ("bracket", "fairlead_body", "servo_sg90", "ld2450_fork", "ld2450_cradle")), "mm3")
    n, c, ar = P.face_normals, P.triangles_center, P.area_faces
    steep = (n[:, 2] < -0.71) & (c[:, 2] > 0.05)
    print(f"body print orientation (ratchet face down): {ar[steep].sum():.2f} mm2 steeper than 45 degrees off the bed (pass under 0.5)")
    print(f"bearing hole: one plain {OP_BORE} diameter from the shoulder (z {OP_Z0 + hz - OP_Z0:.2f}) through the far face, no lip; the bearing's far end sits {OP_SEAT_L - HF0612_LEN:.2f} below the face; the press fit and spacer B keep it in")
    Cp = spool_cap_print(); n, c, ar = Cp.face_normals, Cp.triangles_center, Cp.area_faces
    steep = (n[:, 2] < -0.71) & (c[:, 2] > 0.05)
    print(f"cap print orientation (outer face down, lugs up): {ar[steep].sum():.2f} mm2 steeper than 45 degrees off the bed (pass under 0.5); "
          f"{Cp.extents[2]:.1f} tall, watertight {Cp.is_watertight}")
    cut, p_in, ax = anchor_hole()
    o = p_in + ax * 5; locs, _, _ = P.ray.intersects_location(np.array([o]), np.array([-ax]))
    first = locs[np.argmin(np.linalg.norm(locs - o, axis=1))] if len(locs) else None
    print("line hole open through the skin:", first is None or np.hypot(first[0], first[1]) < SHELL_R - 0.5,
          f"(installed z {OP_Z0 + p_in[2]:.2f}, {OP_ANCHOR_DEG:.0f} deg, between spokes)")
    rad = np.array([math.cos(math.radians(OP_ANCHOR_DEG)), math.sin(math.radians(OP_ANCHOR_DEG)), 0])
    ctr = rad * (math.sqrt((SHELL_R - 0.875) ** 2 - 25) - 0.05) + np.array([0, 0, p_in[2]])   # 10 mm stub resting on its ends against the skin
    hf = near["hf0612"].copy(); hf.apply_translation([0, -AXIS_Y, -OP_Z0])
    worst = {"body": 0.0, "cap": 0.0, "HF0612": 0.0}
    room = OP_L - p_in[2] - 0.1                                   # stub centre to the cap's face: the stub tips until its end's top edge meets the cap
    tilt = max(t for t in range(0, 90) if 5 * math.sin(math.radians(t)) + 0.875 * math.cos(math.radians(t)) <= room)
    for th in np.arange(-tilt, tilt + 0.1, 3):
        d = math.cos(math.radians(th)) * np.cross([0, 0, 1.0], rad) + math.sin(math.radians(th)) * np.array([0, 0, 1.0])
        st = trimesh.creation.cylinder(radius=0.875, height=10, sections=24); st.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], d)); st.apply_translation(ctr)
        for k, m in (("body", P), ("cap", C), ("HF0612", hf)): worst[k] = max(worst[k], I(m, st).volume)
    print(f"10 x 1.75 filament stub across the hole, flat along the barrel and tipped up to {tilt} deg either way (the cap's face is {room + 0.1:.2f} past the hole): "
          f"clear of the body, the cap and the HF0612: {max(worst.values()) < 0.01}" + ("" if max(worst.values()) < 0.01 else f" HITS {worst}"))
    touch = I(sp, cp.copy().apply_translation([0, 0, -0.05])).volume / 0.05
    print(f"cap's line-side face sits on the body's far face: {touch:.0f} mm2 of contact, the screws clamp it (the window ends are closed by the cap, so the stub cannot leave the window)")

def same_geometry(m, path, tol=1e-4):
    """True if the STL on disk already holds this part: same volume, area, extents and centre of mass (triangulation may differ)."""
    if not os.path.exists(path): return False
    try: o = trimesh.load(path, force="mesh")
    except Exception: return False
    close = lambda a, b: np.allclose(a, b, rtol=tol, atol=1e-3)
    return close(o.volume, m.volume) and close(o.area, m.area) and close(o.extents, m.extents) and close(o.center_mass, m.center_mass)

def export_part(name, m):
    """Write cad/stl/<name>.stl only if the part's geometry changed. Returns what happened, for the report."""
    path = os.path.join(OUT, name + ".stl")
    if same_geometry(m, path): return "same geometry as the STL on disk, not rewritten"
    m.export(path); return "WRITTEN"

if __name__ == "__main__":
    # Owner's rule (2026-09-27, hardened 2026-10-04): never rewrite every STL. Running this script builds every part in
    # memory and runs the checks; it writes an STL only for the parts named with --export, and only if the geometry
    # changed. --export-all is the full rebuild and belongs to tools\regen_cad.ps1, run by the owner.
    import argparse
    ap = argparse.ArgumentParser(description="Build every part, run the checks; write STLs only for the parts named.")
    ap.add_argument("--export", nargs="*", default=[], metavar="PART", help="names from the PARTS table to write to cad/stl (only if changed)")
    ap.add_argument("--export-all", action="store_true", help="the full rebuild (regen_cad.ps1); still skips unchanged parts")
    args = ap.parse_args()
    unknown = [n for n in args.export if n not in PARTS]
    if unknown: raise SystemExit(f"no such part: {unknown}. Parts: {', '.join(PARTS)}")
    for name, fn in PARTS.items():
        m = fn()
        status = export_part(name, m) if (args.export_all or name in args.export) else "not exported"
        print(f"{name:15s} watertight={m.is_watertight} size={np.round(m.extents, 1).tolist()} vol={m.volume / 1000:.1f}cm3  {status}")
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
    onepiece_checks(A)
