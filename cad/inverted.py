"""
DropSpider Rev C.1 - INVERTED layout (owner, 2026-09-27): the device turned over so its flat base
is at the bottom, the line leaving through the base, the base sitting on two steel corner braces
screwed to the porch beam's inside face. Every load presses the printed parts into the base.

What is the same: the whole mechanism. Same spool, clutch, ratchet, finger, servo, winding sense.
The line simply peels off the OTHER side of the barrel (the servo side, x +25) and heads for the
base, which is now the floor side.

What is new:
  bracket_inverted   the printed bracket with 5 holes the owner drills: 5 mm for the line at
                     (x 25, z 45); 2x 3.4 at (x 32, z 28) and (x 32, z 83) for the fairlead block;
                     nothing else. (The radar goes under the beam, so no holes for it.)
  fairlead_base      the fairlead + flap hard stop + KW12-3 switch plate, as a block on the base's
                     OUTER face at the line. Built from doc 09's geometry moved by one rigid
                     transform T (180 degrees about z, then +69 in y): the same flared bore, the
                     same flap (fairlead_flap.stl unchanged), the same switch slots and stops.
                     Two M3 screws from inside the base thread into 2.5 pilots.
  corner braces      2x steel L brackets, 1.5 in legs (stand-ins for pictures and clash checks),
                     bolted through the pad's x -80 and x -56 holes, vertical legs screwed to the beam.
  radar              ld2450_fork_screw (cad/wall_mount.py) under the beam, looking out and down.

Coordinates: the device's own frame from generate.py (y = 0 the base's outer face, +y INTO the
device). In the porch, +y is UP. The ceiling is at y = CEILING_Y above the device's top; the beam's
inside face is at x = X_BEAM. Pictures use view_inv() so the floor is down.

Run on its own for the report: python inverted.py
"""
import math
import numpy as np, trimesh

import generate as G
import fairlead as F
import wall_mount as WM

# ---------------- dimensions (mm) ----------------
LINE_X, LINE_Z = 25.0, 45.0          # line exit: the barrel's +x tangent, straight to the base
LINE_HOLE_D = 5.0
BLOCK_SCREWS = [(32.0, 28.0), (32.0, 83.0)]   # (x, z): M3 from inside the base into the block's 2.5 pilots
PAD_BRACE_X = (-80.0, -56.0)        # the pad holes the braces use
BRACE_Z = (28.0, 83.0)
BRACE_LEG, BRACE_W, BRACE_T = 38.0, 16.0, 1.5   # 1.5 in steel corner brace stand-in
BEAM_GAP = 4.0                       # pad edge (x -88) to the beam's face
X_BEAM = -88.0 - BEAM_GAP            # -92
DEVICE_TOP = 62.0                    # bearing plate top; the tallest thing above the base
CEILING_Y = DEVICE_TOP + 8.0         # base sits 70 below the ceiling
BEAM_DEPTH = 254.0
BEAM_BOTTOM_Y = CEILING_Y - BEAM_DEPTH   # -184
RADAR_X_IN = 25.0
RADAR_TILT = 30.0

# T: doc 09's fairlead geometry (line at x -25, bore y 69..78.5, flap at y 84 below it) moved to
# the base's outer face at x +25: 180 degrees about z (x -> -x, y -> -y), then y + 69 so the bore's
# spool-side flare lands on the base's outer face (y 0). The flap stays a right-handed part.
T_ROT = trimesh.transformations.rotation_matrix(math.pi, [0, 0, 1])
T_SHIFT = 69.0
def T(m):
    m = m.copy(); m.apply_transform(T_ROT); m.apply_translation([0, T_SHIFT, 0]); return m
def t_y(y): return -y + T_SHIFT
PIN_Y, HINGE_Z = t_y(F.PY), F.HZ    # the flap's pin: y -13.2, z 58, axis along x


def bracket_inverted():
    """The printed bracket plus the holes the owner drills (the STL is unchanged; this is the model for checks)."""
    cuts = [G.vcyl(LINE_HOLE_D / 2, 10, -3, LINE_X, LINE_Z)] + [G.vcyl(1.7, 10, -3, x, z) for x, z in BLOCK_SCREWS]
    return G.D(G.bracket(), *cuts)


def fairlead_base():
    """Doc 09's block, slab, plates, ribs and rest stop moved by T and clipped to the outside of the
    base, plus a 4 mm mounting plate on the base's outer face. Same cuts as doc 09, moved by T."""
    bx = G.bx
    plate = bx(19, 36, -4, 0, 20, 99)
    slab  = bx(-36, F.SW_X0, 62, F.BOT_Y, 54, F.RIB2_Z0)
    web   = bx(-36, -32, 3, F.BOT_Y, 54, F.RIB2_Z1)
    lower = bx(-36, -32, 70, F.BOT_Y, 39, 54)
    rib1b = bx(-36, F.RIB_X1, F.RIB1B_Y0, F.BOT_Y, 52.5, 58.5)
    rib2  = bx(-36, F.RIB_X1, 3, F.BOT_Y, F.RIB2_Z0, F.RIB2_Z1)
    block = bx(-36, -19, 70, F.STOP_Y, 39, 62)
    rest  = bx(-36, -26, F.STOP_Y, F.HY - F.FT / 2 - 0.2, 63.5, 67.5)
    moved = [T(m) for m in (slab, web, lower, rib1b, rib2, block, rest)]
    outside = bx(0, 40, -60, 0, 0, 120)                      # keep only what lies outside the base (y <= 0)
    body = G.U(plate, *[G.I(m, outside) for m in moved])
    cuts = [T(F.trumpet()),
            T(F.xcyl(0.95, -37, -28, F.PY, F.HZ)),                                  # M2 hinge bolt threads in from the flap side
            T(bx(F.SW_X0 + 0.01, -16, F.HY - 3.6, F.HY + 3.6, F.HZ - 3.6, F.HZ + 3.6))]   # knuckle clearance guard
    for z in F.SW_HOLES_Z:
        cuts += [T(F.xcyl(1.2, -37, -27, F.SW_HOLE_Y - F.SW_SLIDE, z)), T(F.xcyl(1.2, -37, -27, F.SW_HOLE_Y + F.SW_SLIDE, z)),
                 T(bx(-37, -27, F.SW_HOLE_Y - F.SW_SLIDE, F.SW_HOLE_Y + F.SW_SLIDE, z - 1.2, z + 1.2))]
    cuts += [G.vcyl(1.25, 12, -11, x, z) for x, z in BLOCK_SCREWS]          # 2.5 pilots, 11 deep from the mounting face
    return G.D(body, *cuts)


def fairlead_base_print():
    """x = 36 face (the back, where the switch nuts sit) on the bed, like doc 09's body."""
    m = fairlead_base()
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))   # +x -> -z
    m.apply_translation(-m.bounds[0]); return m


def flap_installed(): return T(F.fairlead_flap())
def switch_installed(): return T(F.switch_model())


def rotate_flap(m, deg):
    """About the moved pin. Positive = the free end (z 33 side) toward the base (world up)."""
    r = trimesh.transformations.rotation_matrix(math.radians(deg), [1, 0, 0], point=[0, PIN_Y, HINGE_Z])
    mm = m.copy(); mm.apply_transform(r); return mm


def corner_braces():
    """Steel L stand-ins: horizontal leg under the pad, vertical leg down the beam."""
    out = {}
    for i, zc in enumerate(BRACE_Z):
        z0, z1 = zc - BRACE_W / 2, zc + BRACE_W / 2
        horiz = G.bx(X_BEAM, X_BEAM + BRACE_LEG, -BRACE_T, 0, z0, z1)
        vert = G.bx(X_BEAM, X_BEAM + BRACE_T, -BRACE_LEG, 0, z0, z1)
        b = G.U(horiz, vert)
        b = G.D(b, *[G.vcyl(2.5, 6, -3, x, zc) for x in PAD_BRACE_X], *[G.cyl(2.2, 6, zc - 3, X_BEAM + 0, y) for y in (-10.0, -30.0)])
        out[f"brace_{i}"] = b
    return out


def radar_under_beam(tilt=RADAR_TILT):
    """Fork with screw holes on the beam's underside, looking toward the approach (-x) and down (-y here)."""
    R = trimesh.transformations.rotation_matrix(math.pi, [0, 0, 1])
    out = {}
    for k, m in (("ld2450_fork_screw", WM.ld2450_fork_screw()), ("ld2450_cradle", __import__("sensor_mount").ld2450_cradle(tilt)),
                 ("ld2450_radar", __import__("sensor_mount").ld2450_board(tilt))):
        mm = m.copy(); mm.apply_transform(R)
        mm.apply_translation([X_BEAM - RADAR_X_IN + 68.0, BEAM_BOTTOM_Y + 4.0, 0]); out[k] = mm   # rotated pivot at x -68, plate face y -4
    return out


def line_and_bead(drop=120.0):
    line = G.vcyl(0.3, 40 + drop, -drop, LINE_X, LINE_Z)
    bead = trimesh.creation.icosphere(radius=4, subdivisions=3); bead.apply_translation([LINE_X, t_y(F.HY) - F.FT / 2 - 4 - 3.3, LINE_Z])
    return {"line": line, "bead": bead}


def assembly_inverted():
    A = {k: v for k, v in G.assembly().items() if k not in ("bracket", "fairlead_body", "fairlead_flap", "switch_kw12") and not k.startswith("ld2450")}
    A["bracket"] = bracket_inverted()
    A["fairlead_base"] = fairlead_base(); A["fairlead_flap"] = flap_installed(); A["switch_kw12"] = switch_installed()
    A.update(corner_braces()); A.update(radar_under_beam())
    return A


def porch():
    beam = G.bx(X_BEAM - 90, X_BEAM, BEAM_BOTTOM_Y, CEILING_Y, -110, 220)
    ceiling = G.bx(X_BEAM - 90, 200, CEILING_Y, CEILING_Y + 12, -110, 220)
    return {"beam": beam, "ceiling": ceiling}


def view_inv(m):
    """Render world for the inverted install: X = x, Y = -z, Z = y (up). A proper rotation, so parts keep their handedness."""
    mm = m.copy(); v = mm.vertices.copy(); mm.vertices = np.column_stack([v[:, 0], -v[:, 2], v[:, 1]]); return mm


if __name__ == "__main__":
    body, flap, sw = fairlead_base(), flap_installed(), switch_installed()
    print(f"fairlead_base watertight={body.is_watertight} size={np.round(body.extents, 1).tolist()} vol={body.volume / 1000:.1f}cm3")
    p = fairlead_base_print(); down = (p.face_normals[:, 2] < -0.7) & (p.triangles_center[:, 2] > 0.01)
    print(f"  print: footprint {np.round(p.extents[:2], 1).tolist()}, height {p.extents[2]:.1f}, overhang off the bed {p.area_faces[down].sum():.0f} mm2")
    ys = sorted(set(np.round(body.triangles_center[body.face_normals[:, 1] > 0.99, 1], 2).tolist()))
    print(f"mounting face is one plane at y 0: {ys == [0.0]} (faces looking into the base: {ys})")
    A = assembly_inverted()
    print("--- clash check, overlap volume in mm3 (none listed = clear) ---")
    new = ["fairlead_base", "fairlead_flap", "switch_kw12", "brace_0", "brace_1", "ld2450_fork_screw", "ld2450_cradle", "ld2450_radar"]
    bad = False
    for k in new:
        for j, part in A.items():
            if j == k or {k, j} <= {"fairlead_flap", "switch_kw12"}: continue      # the roller rests on the flap tail by design
            v = G.I(A[k], part).volume
            if v > 0.5: print(f"CLASH {k} x {j}: {v:.1f}"); bad = True
    if not bad: print("block, flap, switch, braces and radar clear every part")
    path = G.vcyl(1.0, 100, -60, LINE_X, LINE_Z)                                    # 2 mm rod from the barrel down past the flap
    lb, lf, lk = G.I(path, body).volume, G.I(path, flap).volume, G.I(path, A["bracket"]).volume
    print(f"line path clear through the base hole: {lk < 0.01} ({lk:.2f}), the block's bore: {lb < 0.01} ({lb:.2f}), the flap slot: {lf < 0.01} ({lf:.2f})")
    ring = trimesh.creation.annulus(r_min=33.01, r_max=35, height=16); ring.apply_translation([0, 40, 43])
    print(f"spool 2 mm clearance vs the block: {G.I(ring, body).volume:.1f} mm3")
    for sign, name in ((1, "hard stop (free end up toward the base)"), (-1, "rest stop (free end down)")):
        for deg in np.arange(0, 25, 0.25):
            if G.I(rotate_flap(flap, sign * deg), body).volume > 0.2:
                print(f"{name}: {deg:.2f} deg"); break
        if sign == 1:
            a = math.radians(deg); print(f"  bead lift at stop {13 * math.sin(a):.2f} mm; roller push {(F.TAIL_Z - F.HZ) * math.sin(a):.2f} mm (switch needs 3.4)")
    # screw heads inside the base: the block's 2 screws and nothing else in the way
    for x, z in BLOCK_SCREWS:
        head = G.vcyl(2.8, 2.5, 4.0, x, z)
        hits = [k for k, part in A.items() if k != "bracket" and G.I(head, part).volume > 0.05]
        print(f"screw head inside the base at x {x:.0f}, z {z:.0f}: {'clear' if not hits else 'HITS ' + str(hits)}")
    W = 480 / 1000 * 9.81; M = W * (-5 - X_BEAM) + 27 * (LINE_X - X_BEAM)
    Zb = 110 * 4 ** 2 / 6
    print(f"load: base plate bending at the brace leg tip, weight + line snap: {M / Zb:.1f} MPa in-plane (PLA about 50): margin x{50 / (M / Zb):.0f}; top brace screw about {M / BRACE_LEG / 2:.0f} N each")
    print(f"line falls {LINE_X - X_BEAM:.0f} mm from the beam's face; base {CEILING_Y:.0f} below the ceiling; bead at rest {CEILING_Y - (t_y(F.HY) - 4):.0f} below the ceiling; spider bottom = that + 30 + spider height (beam edge 254)")
