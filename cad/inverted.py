"""
DropSpider Rev C.1 - INVERTED layout (owner, 2026-09-27): the device turned over so its flat base
is at the bottom, the line leaving through the base, the base sitting on two steel corner braces
screwed to the porch beam's inside face. Every load presses the printed parts into the base.

What is the same: the whole mechanism. Same spool, clutch, ratchet, finger, servo, winding sense.
The line simply peels off the OTHER side of the barrel (the servo side, x +25) and heads for the
base, which is now the floor side.

What is new:
  bracket_inverted   the printed bracket with 5 holes drilled: 7 mm for the line at (x 25, z 45),
                     wider than the 6 mm barrel channel so the line never rubs a drilled edge;
                     2x 3.4 at (x 32, z 28) and (x 32, z 83) for the fairlead block; 2x 3.4 at
                     (x 62, z 45) and (x 62, z 79) for the radar fork. Brace holes are the owner's.
  fairlead_base      the fairlead + flap hard stop + KW12-3 switch plate, as a block on the base's
                     OUTER face at the line. Built from doc 09's geometry moved by one rigid
                     transform T (180 degrees about z, then +69 in y): the same flared bore, the
                     same flap (fairlead_flap.stl unchanged), the same switch slots and stops.
                     Two M3 screws from inside the base thread into 2.5 pilots.
  corner braces      2x steel L brackets, 6 in legs, 1 in wide (stand-ins for pictures and clash
                     checks, no holes: the owner drills the base to the braces' own holes, 2026-09-27),
                     at the base's ends. The owner's orientation (2026-09-27): the flat leg under the
                     base, the other leg standing UP the beam's face beside the device, screwed to it.
  radar              part of the device (owner 2026-09-27): ld2450_fork_screw (cad/sensor_mount.py,
                     same ears as ld2450_fork, no glue), cradle and radar, turned over and bolted
                     under the base at the servo end with 2x M3, looking back toward the beam (the
                     approach) and down, under the fairlead block.
  electronics        the controller board stays where it is in the ceiling design: on the pad, the
                     base's device side at the beam end, now facing up. A 52 x 75 x 30 stand-in box
                     is clash-checked.

Coordinates: the device's own frame from generate.py (y = 0 the base's outer face, +y INTO the
device). In the porch, +y is UP. The ceiling is at y = CEILING_Y above the device's top; the beam's
inside face is at x = X_BEAM. Pictures use view_inv() so the floor is down.

Run on its own for the report: python inverted.py
"""
import math
import numpy as np, trimesh

import generate as G
import fairlead as F
import sensor_mount as S

# ---------------- dimensions (mm) ----------------
LINE_X, LINE_Z = 25.0, 45.0          # line exit: the barrel's +x tangent, straight to the base
LINE_HOLE_D = 7.0                    # barrel channel is z 42 to 48; 7 mm (z 41.5 to 48.5) keeps the line off the drilled edge
BLOCK_SCREWS = [(32.0, 28.0), (32.0, 83.0)]   # (x, z): M3 from inside the base into the block's 2.5 pilots
BRACE_Z = (8.0, 106.0)              # brace centre lines: the base's ends, clear of the block (z 24 to 93); the owner's call
BRACE_LEG, BRACE_W, BRACE_T = 152.0, 25.0, 1.5  # 6 in x 1 in steel corner brace stand-in
BEAM_GAP = 4.0                       # pad edge (x -88) to the beam's face
X_BEAM = -88.0 - BEAM_GAP            # -92
DEVICE_TOP = 62.0                    # bearing plate top; the tallest thing above the base
CEILING_Y = BRACE_LEG + 8.0          # the braces' upright legs stand under the ceiling: base 160 below it
BEAM_DEPTH = 254.0
BEAM_BOTTOM_Y = CEILING_Y - BEAM_DEPTH   # -94
RADAR_TILT = 50.0                    # doc 03's tilt, below level; the cradle adjusts
RADAR_SHIFT = (130.0, 4.0)
RADAR_SCREWS = [(130.0 - 68.0, 62.0 - S.FORK_SCREW_DZ), (130.0 - 68.0, 62.0 + S.FORK_SCREW_DZ)]   # (x, z): the fork's 2 holes, turned over: x 62, z 45 and 79
PCB_BOX = (-88.0, -36.0, 4.0, 34.0, 18.0, 93.0)   # electronics stand-in on the pad (x, y, z ranges)

# T: doc 09's fairlead geometry (line at x -25, bore y 69..78.5, flap at y 84 below it) moved to
# the base's outer face at x +25: 180 degrees about z (x -> -x, y -> -y), then y + 69 so the bore's
# spool-side flare lands on the base's outer face (y 0). The flap stays a right-handed part.
T_ROT = trimesh.transformations.rotation_matrix(math.pi, [0, 0, 1])
T_SHIFT = 69.0
def T(m):
    m = m.copy(); m.apply_transform(T_ROT); m.apply_translation([0, T_SHIFT, 0]); return m
def t_y(y): return -y + T_SHIFT



def bracket_inverted():
    """The printed bracket plus the holes the owner drills (the STL is unchanged; this is the model for checks)."""
    cuts = [G.vcyl(LINE_HOLE_D / 2, 10, -3, LINE_X, LINE_Z)] + [G.vcyl(1.7, 10, -3, x, z) for x, z in BLOCK_SCREWS + RADAR_SCREWS]
    return G.D(G.bracket(), *cuts)


# ---------------- fairlead block, v2 (owner 2026-09-28) ----------------
# Owner: switch facing outward, its legs and wires toward the spool (up, toward the base), not jutting out
# under the flap; the flap the lowest point of the unit. So the switch now sits ABOVE the flap: the flap's
# free-end side (the side the bead lifts) gets a tab reaching out past the block, under the switch's roller.
# The bead lifts the free end, the tab lifts the roller. A switch stacked above the flap with its legs up
# needs about 30 mm between the flap and the base (lever and roller 9.8, body 10.2, legs 6.4, room to
# solder), so the flap hangs 32 mm under the base (the old unit hung 39, with the switch lowest).
FL_Y = -32.0                          # flap mid-plane at rest
DY = FL_Y - t_y(F.HY)                 # the doc 09 flap moved by T, then down this far
PIN_Y, HINGE_Z = t_y(F.PY) + DY, F.HZ # hinge pin: y -30.2, z 58, axis along x
FLAP_TOP = FL_Y + F.FT / 2            # -30.8
STOP_GAP = 4.8                        # flap top to the block's underside (hard stop), as doc 09
STOP_Y_INV = FLAP_TOP + STOP_GAP      # -26: underside of the bore column
COL = (19.0, 31.0, 39.0, 68.0)        # bore column x0, x1, z0, z1. Stop face starts at z 39, as doc 09 (sets the stop angle)
GAP_X = (31.0, 34.0)                  # nut gap between the column and the switch plate, open underneath
PLATE_X = (34.0, 37.0)                # switch plate, 3 thick; the switch bolts to its outer (x 37) face
PLATE_Z = (37.0, 58.0)
PLATE_Y0 = -20.0                      # plate bottom, just above the switch's lever face
TAB = (30.5, 45.0, 34.0, 48.0)        # flap tab x0, x1, z0, z1, free-end side, under the roller
SWV_X0 = 37.0                         # switch body x 37 to 43.4 (6.4 thick), on the plate's outer face
SWV_Z0 = 37.0                         # body z 37 to 57; roller end at z 37
SWV_ROLLER_Z = SWV_Z0 + (F.TAIL_Z - F.SW_Z0)   # roller 4 mm in from that end: z 41, 17 mm from the hinge
SWV_ROLL_Y = FLAP_TOP + 0.3 + 2.4     # roller centre: 0.3 above the tab at rest
SWV_BODY_BOT = FLAP_TOP + 0.3 + 9.8   # lever face of the body: -20.7 (lever and roller stack 9.8, as doc 09's model)
SWV_BODY_TOP = SWV_BODY_BOT + (F.SW_BODY_BOT - F.SW_BODY_TOP)   # -10.5; legs up to -4.1
SWV_HOLE_Y = SWV_BODY_TOP - 2.9       # mounting holes 2.9 in from the leg side, as doc 09
SWV_HOLES_Z = (SWV_Z0 + 5.25, SWV_Z0 + 5.25 + 9.5)
BORE_R = 2.0                          # bore throat radius (4.0 mm)
SW_PILOT_D, SW_PILOT_DEPTH = 1.8, 6.5 # owner 2026-09-28: switch on 2x M2 x 12 self-tapping into the plastic, holes 6.5 deep; 1.8 drawn prints about 1.6
REST_SHAVE = 1.25                     # owner 2026-09-28: rest pad shortened 1.25 mm


def bore_inv():
    """Line bore through the column, y 0 down to the stop face, rounded flares at both ends. Owner 2026-09-28:
    wider and more forgiving (less fraying): 4.0 mm throat (was 3.2), top mouth 7 mm to meet the base's
    7 mm hole, bottom mouth 9 mm, each flare 6 mm long. Walls to the column's sides stay 1.5 mm or more."""
    h = -STOP_Y_INV + 0.5
    r0, rt, rb, L = BORE_R, 3.5, 4.5, 6.0
    prof = [(0, 0.0)]
    for k in range(9):
        t = k / 8; prof.append((r0 + (rt - r0) * (1 - t) ** 2, L * t))
    prof.append((r0, h - L))
    for k in range(1, 9):
        t = k / 8; prof.append((r0 + (rb - r0) * t ** 2, h - L + L * t))
    prof.append((0, h))
    v = trimesh.creation.revolve(np.array(prof), sections=64)                     # axis z, 0 to h
    v.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))   # z -> -y
    if v.volume < 0: v.invert()
    assert v.bounds[1][1] < 0.1 and v.bounds[0][1] < STOP_Y_INV, v.bounds    # must span the column
    v.apply_translation([LINE_X, 0.05, LINE_Z]); return v


def fairlead_base():
    """v2: mounting plate on the base, a bore column whose underside is the flap's hard stop, the hinge
    boss, the rest stop, and a switch plate on the outer side with a nut gap behind it."""
    bx = G.bx
    x0, x1, z0, z1 = COL
    plate = bx(19, 37, -4, 0, 24, 93)                                   # mounting plate, same footprint as v1 plus the switch plate
    bosses = [bx(28.5, 36, -11, 0, z - 4, z + 4) for _, z in BLOCK_SCREWS]   # 11 mm of thread for each M3
    column = bx(x0, x1, STOP_Y_INV, 0, z0, z1)
    hinge = bx(29.0, 36.0, PIN_Y - 2.5, 0, HINGE_Z - 3.0, HINGE_Z + 3.0)     # M2 hinge bolt threads 7 mm; 1.1 clear of the knuckle (x 27.9)
    rest = bx(24.0, x1, FLAP_TOP + 0.2 + REST_SHAVE, STOP_Y_INV, 63.5, 67.5)   # rest stop over the flap tail, shortened 1.25 (owner)
    splate = bx(GAP_X[0], PLATE_X[1], PLATE_Y0, 0, PLATE_Z[0], PLATE_Z[1])   # solid from the column to the switch face (x 31 to 37), no nut gap
    body = G.U(plate, *bosses, column, hinge, rest, splate)
    cuts = [bore_inv(), F.xcyl(0.95, 28.5, 37, PIN_Y, HINGE_Z)]
    for z in SWV_HOLES_Z:                                               # M2 x 12 self-tapping, 6.5 deep from the switch face
        cuts += [F.xcyl(SW_PILOT_D / 2, PLATE_X[1] - SW_PILOT_DEPTH, PLATE_X[1] + 1, SWV_HOLE_Y, z)]
    cuts += [G.vcyl(1.25, 12, -11, x, z) for x, z in BLOCK_SCREWS]      # 2.5 pilots, 11 deep from the mounting face
    return G.D(body, *cuts)


def fairlead_base_print():
    """Mounting face (y 0) on the bed; everything grows from it, so no supports and a dead-flat face."""
    m = fairlead_base()
    m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))   # -y -> +z
    m.apply_translation(-m.bounds[0]); return m


def flap_inv_local():
    """Doc 09's flap (same knuckle, slot, prong) plus the tab, in doc 09's frame so it prints like the old one."""
    tx0, tx1, tz0, tz1 = TAB
    tab = G.bx(-tx1, -tx0, F.HY - F.FT / 2, F.HY + F.FT / 2, tz0, tz1)
    return G.U(F.fairlead_flap(), tab)


def fairlead_flap_inv_print():
    m = flap_inv_local(); m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))
    m.apply_translation(-m.bounds[0]); return m


def flap_installed():
    m = T(flap_inv_local()); m.apply_translation([0, DY, 0]); return m


def switch_legs_installed():
    x0, x1 = SWV_X0, SWV_X0 + (F.SW_X1 - F.SW_X0)
    return G.bx(x0 + 2, x1 - 2, SWV_BODY_TOP, SWV_BODY_TOP + 6.4, SWV_Z0 + 2, SWV_Z0 + 18)


def switch_installed():
    """KW12-3, legs UP toward the base, lever and roller down onto the flap's tab, body on the plate's outer face."""
    x0, x1 = SWV_X0, SWV_X0 + (F.SW_X1 - F.SW_X0)
    body = G.bx(x0, x1, SWV_BODY_BOT, SWV_BODY_TOP, SWV_Z0, SWV_Z0 + 20)
    xc = (x0 + x1) / 2
    roller = F.xcyl(2.4, xc - 1.5, xc + 1.5, SWV_ROLL_Y, SWV_ROLLER_Z)
    return G.U(body, switch_legs_installed(), roller)


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
        vert = G.bx(X_BEAM, X_BEAM + BRACE_T, -BRACE_T, BRACE_LEG - BRACE_T, z0, z1)   # stands UP the beam beside the device
        out[f"brace_{i}"] = G.U(horiz, vert)
    return out


def radar_on_base(tilt=RADAR_TILT):
    """The ceiling design's fork, cradle and radar turned over (180 degrees about z) and moved under the
    base's servo end: bolted to the base's outer face with 2x M3, looking toward the beam (-x) and down (-y)."""
    R = trimesh.transformations.rotation_matrix(math.pi, [0, 0, 1])
    out = {}
    for k, m in (("ld2450_fork_screw", S.ld2450_fork_screw()), ("ld2450_cradle", S.ld2450_cradle(tilt)), ("ld2450_radar", S.ld2450_board(tilt))):
        mm = m.copy(); mm.apply_transform(R); mm.apply_translation([RADAR_SHIFT[0], RADAR_SHIFT[1], 0]); out[k] = mm
    return out


def pcb_box():
    x0, x1, y0, y1, z0, z1 = PCB_BOX
    return G.bx(x0, x1, y0, y1, z0, z1)


def line_and_bead(drop=120.0):
    line = G.vcyl(0.3, 40 + drop, -drop, LINE_X, LINE_Z)
    bead = trimesh.creation.icosphere(radius=4, subdivisions=3); bead.apply_translation([LINE_X, FL_Y - F.FT / 2 - 4 - 3.3, LINE_Z])
    return {"line": line, "bead": bead}


def assembly_inverted():
    A = {k: v for k, v in G.assembly().items() if k not in ("bracket", "fairlead_body", "fairlead_flap", "switch_kw12") and not k.startswith("ld2450")}
    A["bracket"] = bracket_inverted()
    A["fairlead_base"] = fairlead_base(); A["fairlead_flap"] = flap_installed(); A["switch_kw12"] = switch_installed()
    A.update(corner_braces()); A.update(radar_on_base()); A["electronics"] = pcb_box()
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
    top = body.face_normals[:, 1] > 0.99; at0 = top & (np.abs(body.triangles_center[:, 1]) < 0.01)
    print(f"mounting face is one plane at y 0: {abs(body.bounds[1][1]) < 0.01} (nothing above y 0; contact area {body.area_faces[at0].sum():.0f} mm2)")
    A = assembly_inverted()
    print("--- clash check, overlap volume in mm3 (none listed = clear) ---")
    new = ["fairlead_base", "fairlead_flap", "switch_kw12", "brace_0", "brace_1", "ld2450_fork_screw", "ld2450_cradle", "ld2450_radar", "electronics"]
    bad = False
    for k in new:
        for j, part in A.items():
            if j == k or {k, j} <= {"fairlead_flap", "switch_kw12"} or {k, j} <= {"ld2450_fork_screw", "ld2450_cradle", "ld2450_radar"}: continue   # roller on flap tail; radar sits in its cradle
            v = G.I(A[k], part).volume
            if v > 0.5: print(f"CLASH {k} x {j}: {v:.1f}"); bad = True
    if not bad: print("block, flap, switch, braces, radar and the 52 x 75 x 30 electronics box clear every part")
    # radar view: rays over +-60 across and +-35 along the board from its centre; what share hits the device or its braces
    Rb = A["ld2450_radar"]; t = math.radians(RADAR_TILT)
    nb = np.array([-math.cos(t), -math.sin(t), 0.0]); ab = np.array([math.sin(t), -math.cos(t), 0.0]); zb = np.array([0, 0, 1.0])
    c = Rb.bounds.mean(0) + nb * 2.0
    solid = G.U(*[m for k2, m in A.items() if not k2.startswith("ld2450") and k2 != "electronics"])
    dirs = [math.cos(math.radians(e)) * (math.cos(math.radians(a2)) * nb + math.sin(math.radians(a2)) * zb) + math.sin(math.radians(e)) * ab
            for a2 in range(-60, 61, 5) for e in range(-35, 36, 5)]
    dirs = np.array(dirs); hit = solid.ray.intersects_any(np.repeat([c], len(dirs), 0), dirs)
    core = [abs(a2) <= 20 and abs(e) <= 15 for a2 in range(-60, 61, 5) for e in range(-35, 36, 5)]
    print(f"radar view blocked by the device: {100 * hit.mean():.0f}% of the full cone, {100 * hit[core].mean():.0f}% of the middle (+-20 by +-15)")
    yb = c[1] + nb[1] * (X_BEAM - c[0]) / nb[0]
    print(f"radar centre line reaches the beam's face {CEILING_Y - yb:.0f} below the ceiling (beam bottom edge {BEAM_DEPTH:.0f}): {'passes under the beam' if CEILING_Y - yb > BEAM_DEPTH else 'HITS the beam'}")
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
            a = math.radians(deg); print(f"  bead lift at stop {13 * math.sin(a):.2f} mm; roller push {(HINGE_Z - SWV_ROLLER_Z) * math.sin(a) - 0.3:.2f} mm past touching (switch needs 3.4)")
    rest_flap = rotate_flap(flap, -deg if False else 0)
    lows = {"flap (at rest)": None, "block": body.bounds[0][1], "switch body and roller": switch_installed().bounds[0][1]}
    for dd in np.arange(0, 25.0, 0.25):
        if G.I(rotate_flap(flap, -dd), body).volume > 0.2: break
    lows["flap (at rest)"] = rotate_flap(flap, -dd).bounds[0][1]
    print("lowest points (y, mm below the base): " + ", ".join(f"{k} {v:.1f}" for k, v in lows.items()))
    print(f"flap is the lowest point: {lows['flap (at rest)'] < min(lows['block'], lows['switch body and roller']) - 0.5}")
    lg = switch_legs_installed()
    print(f"switch legs point up toward the base: legs y {lg.bounds[0][1]:.1f} to {lg.bounds[1][1]:.1f}, {-lg.bounds[1][1]:.1f} mm of room under the base to solder; switch body x {SWV_X0:.1f} to {SWV_X0 + 6.4:.1f}, on the outer face")
    # screw heads inside the base: the block's 2 screws and nothing else in the way
    for x, z in BLOCK_SCREWS + RADAR_SCREWS:
        head = G.vcyl(3.2, 3.0, 4.0, x, z)                                          # screw head or M3 nut inside the base
        hits = [k for k, part in A.items() if k != "bracket" and G.I(head, part).volume > 0.05]
        print(f"screw head inside the base at x {x:.0f}, z {z:.0f}: {'clear' if not hits else 'HITS ' + str(hits)}")
    W = 480 / 1000 * 9.81; M = W * (-5 - X_BEAM) + 27 * (LINE_X - X_BEAM)
    print(f"load: weight + a line snap turn {M / 1000:.1f} N m about the beam's face, carried by the two steel braces' corners; "
          f"the PLA base only sits on their flat legs (from x -24, where the base starts at the brace rows, to x 60), in compression; "
          f"the braces' top beam screws see about {M / (BRACE_LEG - 20) / 2:.0f} N each")
    print(f"line falls {LINE_X - X_BEAM:.0f} mm from the beam's face; base {CEILING_Y:.0f} below the ceiling; bead at rest {CEILING_Y - (FL_Y - 4):.0f} below the ceiling; spider bottom = that + 30 + spider height (beam edge 254)")
