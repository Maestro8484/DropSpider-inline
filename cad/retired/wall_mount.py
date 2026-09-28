"""
DropSpider Rev C.1 - wall mount: hangs the device from a VERTICAL face (the porch beam's inside
face) with the device in its normal orientation: bracket ceiling face level and on top, rod
level and parallel to the beam, spider dropping straight down.

The form is a shelf bracket (the trade calls the fixed kind a gusseted L-bracket or knee brace):
  shelf        a flat plate that takes the place of the ceiling. The device bolts up into it
               through its own ceiling holes, M3 bolts from below into nuts captured in hex
               pockets on the shelf's top.
  wall plate   hangs down from the shelf's wall edge; 4 wood screws into the beam.
  braces       two triangles under the shelf at its ends, outside the device, propping the shelf
               against the wall plate. They carry the load; the shelf and plate only join things.
One printed part. The pad end of the device (-x) goes at the wall, 6 mm off the plate, so the
line falls 69 mm from the beam's face. The radar cannot stay on the device here (it would look
away from the approach), so it moves under the beam on a screw-on version of its fork.

Coordinates: the assembly frame from generate.py, device in its normal place. The wall plate's
inner face is at x = X_IN; the beam's face is at X_OUT. The shelf's top is at y = -SHELF_T and
that is where the ceiling would be. +y is down.

Print: shelf top face on the bed, wall plate and braces rising (85 mm tall, 169 x 154 footprint,
no supports). The nut pockets open on the bed side, so their ceilings use the stepped bridging
from the finger. The prior-art rule to print an L on its side so the corner is drawn in one
line does not apply: the second brace would then hang over air. With the braces, the corner's
layer bonds see under 1 MPa (numbers printed by the report below).

Run on its own for the fit, clash, print and strength report: python wall_mount.py
"""
import math, os
import numpy as np, trimesh
from trimesh.creation import extrude_polygon, cylinder
from shapely.geometry import Polygon

import generate as G
import sensor_mount as S

# ---------------- wall mount dimensions (mm) ----------------
WALL_GAP = 6.0                 # pad edge (x -88) to the wall plate's inner face: room for a board edge, and the corner fillet
X_IN = -88.0 - WALL_GAP        # -94, inner face of the wall plate
PLATE_T = 5.0
X_OUT = X_IN - PLATE_T         # -99, the face against the beam
SHELF_T = 5.0                  # 2.6 nut pocket + 0.8 bridging + 1.6 solid
SHELF_X1 = 70.0                # past the (65, z) holes by 5; the bracket's servo end (x 75) overhangs 5 mm, unloaded
Z0, Z1 = -22.0, 132.0          # along the beam: 154 long. Device is z 0..110, motor to z -32 (near x 0 only)
PLATE_Y1 = 80.0                # wall plate reaches 80 below the shelf's underside
BRACE_T = 5.0
BRACE_Z = ((Z0, Z0 + BRACE_T), (Z1 - BRACE_T, Z1))
BRACE_X1 = -22.0               # brace tip under the shelf: 72 out from the wall, 8 short of the motor (x -14)
BRACE_Y1 = 78.0                # brace foot on the wall plate
FILLET_R = 4.0                 # quarter round in the shelf-to-plate corner, 2 mm clear of the pad edge
SCREWS = [(z, y) for z in (-6.0, 116.0) for y in (14.0, 70.0)]   # (z, y) of the 4 wood screws; all four have a straight screwdriver path along x
SCREW_D = 3.6                  # #4 wood screw (2.8 shank) through a hole that prints about 3.3
DEVICE_HOLES = [(-80, 28), (-80, 83), (-56, 28), (-56, 83), (65, 20), (65, 90)]   # (x, z) of the bracket's ceiling holes, minus the fairlead pair
BOLT_D = 3.4                   # M3 clearance
NUT_AF = 5.8                   # M3 nut 5.5 across flats + 0.3: prints about 5.6, a snug tap-in
NUT_T = 2.6                    # M3 nut 2.4 thick
WINDOW = (-12.0, 12.0, 30.0, 90.0)   # x0, x1, z0, z1: same window as the bracket base

# radar under the beam: the fork with a longer plate and two wood-screw holes
FORK_PLATE_T = 3.0
FORK_Z_HALF = 22.0             # plate z 40..84 about Z_CENTER 62; ears are z 53.3..70.7
FORK_SCREW_DZ = 17.0           # screws at z 45 and 79, outside the cradle's swing (z 53..71)
RADAR_TILT = 30.0              # under the beam nothing blocks the view; start here
RADAR_X_IN = 25.0              # fork pivot this far outside the beam's inside face

# the porch, for pictures and the radar placement (doc 06: beam 10 in deep)
BEAM_DEPTH = 254.0
BEAM_THICK = 90.0              # stand-in, not measured
CEILING_Y = -SHELF_T           # the shelf top sits against the ceiling
BEAM_BOTTOM_Y = CEILING_Y + BEAM_DEPTH   # 249


def hex_prism_y(af, y0, y1, x, z):
    """Hex prism along y, across-flats af, flats facing +-z (a vertex points along x)."""
    h = cylinder(radius=af / 2 / math.cos(math.radians(30)), height=y1 - y0, sections=6)
    h.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    h.apply_translation([x, (y0 + y1) / 2, z]); return h


def wall_mount():
    bx = G.bx
    shelf = bx(X_OUT, SHELF_X1, -SHELF_T, 0, Z0, Z1)
    plate = bx(X_OUT, X_IN, -SHELF_T, PLATE_Y1, Z0, Z1)
    fillet = bx(X_IN, X_IN + FILLET_R, 0, FILLET_R, Z0, Z1)
    fillet = G.D(fillet, G.cyl(FILLET_R, Z1 - Z0 + 2, Z0 - 1, X_IN + FILLET_R, FILLET_R))
    braces = []
    for z0, z1 in BRACE_Z:
        tri = extrude_polygon(Polygon([(X_IN, 0), (BRACE_X1, 0), (X_IN, BRACE_Y1)]), z1 - z0)
        tri.apply_translation([0, 0, z0]); braces.append(tri)
    body = G.U(shelf, plate, fillet, *braces)
    cuts = [bx(WINDOW[0], WINDOW[1], -SHELF_T - 1, 1, WINDOW[2], WINDOW[3])]
    for x, z in DEVICE_HOLES:
        cuts.append(G.vcyl(BOLT_D / 2, SHELF_T + 2, -SHELF_T - 1, x, z))
        yc = -SHELF_T + NUT_T                                   # pocket ceiling
        cuts.append(hex_prism_y(NUT_AF, -SHELF_T - 1, yc, x, z))
        # stepped bridging (printed top face down): first 0.4 mm over the pocket is two strips
        # beside a slot as wide as the bolt hole, the next 0.4 bridges the slot leaving a square,
        # then the round hole. Every layer rests on the one below.
        r = NUT_AF / 2 / math.cos(math.radians(30)) + 0.5
        cuts.append(bx(x - r, x + r, yc - 0.01, yc + 0.4, z - BOLT_D / 2, z + BOLT_D / 2))
        cuts.append(bx(x - BOLT_D / 2, x + BOLT_D / 2, yc + 0.4 - 0.01, yc + 0.8, z - BOLT_D / 2, z + BOLT_D / 2))
    for z, y in SCREWS:
        c = cylinder(radius=SCREW_D / 2, height=PLATE_T + 2, sections=48)
        c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        c.apply_translation([(X_OUT + X_IN) / 2, y, z]); cuts.append(c)
    return G.D(body, *cuts)


def wall_mount_print():
    """Shelf top face on the bed; the wall plate and both braces rise from it. 85 mm tall."""
    m = wall_mount()
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))   # +y (down) -> +z (up in print)
    m.apply_translation(-m.bounds[0]); return m


def ld2450_fork_screw():
    """The radar fork with a 3 mm plate, 44 long along z, and two 3.6 holes for #4 wood screws.
    Same ears and pivot as ld2450_fork, so the cradle is unchanged. Drawn in the fork's own
    place under the bracket (y 4 = the face against the wood); the wall layout moves it."""
    z0, z1 = S.Z_CENTER - FORK_Z_HALF, S.Z_CENTER + FORK_Z_HALF
    plate = G.bx(62, 74, 4, 4 + FORK_PLATE_T, z0, z1)
    m = G.U(S.ld2450_fork(), plate)
    return G.D(m, *[G.vcyl(SCREW_D / 2, 10, 0, 68, S.Z_CENTER + s * FORK_SCREW_DZ) for s in (-1, 1)])


def ld2450_fork_screw_print():
    m = ld2450_fork_screw()
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))
    m.apply_translation(-m.bounds[0]); return m


def _radar_to_beam(m):
    """Take a radar part drawn in its device place (fork under the bracket, looking along +x) and
    put it under the beam looking outward (-x): turn 180 degrees about y, then move so the
    plate's face sits on the beam's underside RADAR_X_IN outside the beam's inside face."""
    m = m.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [0, 1, 0]))
    m.apply_translation([X_OUT - RADAR_X_IN + S.PIVOT[0], BEAM_BOTTOM_Y - 4.0, 0]); return m   # the turned pivot sits at -PIVOT x; land it at X_OUT - RADAR_X_IN


def assembly_wall(tilt=RADAR_TILT):
    """The device in its normal place, the wall mount over it, the radar under the beam."""
    A = {k: v for k, v in G.assembly().items() if not k.startswith("ld2450")}
    A["wall_mount"] = wall_mount()
    A["ld2450_fork_screw"] = _radar_to_beam(ld2450_fork_screw())
    A["ld2450_cradle"] = _radar_to_beam(S.ld2450_cradle(tilt))
    A["ld2450_radar"] = _radar_to_beam(S.ld2450_board(tilt))
    return A


def porch():
    """Stand-ins for pictures: the beam and a slab of ceiling."""
    beam = G.bx(X_OUT - BEAM_THICK, X_OUT, CEILING_Y, BEAM_BOTTOM_Y, -120, 250)
    ceiling = G.bx(X_OUT - BEAM_THICK, 200, CEILING_Y - 12, CEILING_Y, -120, 250)
    return {"beam": beam, "ceiling": ceiling}


def hardware():
    """M3 bolts and nuts at the device holes, #4 screws at the wall, for the exploded picture."""
    H = {}
    for i, (x, z) in enumerate(DEVICE_HOLES):
        yh = 4.0 if x > 0 else 3.0                                  # under the base (4) or the pad (3)
        bolt = G.U(G.vcyl(1.5, 12, yh - 12 + 0.0, x, z), G.vcyl(2.75, 2.0, yh, x, z))
        H[f"bolt_{i}"] = bolt
        H[f"nut_{i}"] = hex_prism_y(5.5, -SHELF_T, -SHELF_T + 2.4, x, z)
    for i, (z, y) in enumerate(SCREWS):
        c = cylinder(radius=1.4, height=25, sections=24)
        c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        c.apply_translation([X_IN - 12.5 + 2, y, z])
        head = cylinder(radius=2.75, height=2, sections=24)
        head.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        head.apply_translation([X_IN + 1, y, z])
        H[f"screw_{i}"] = G.U(c, head)
    return H


# ---------------- strength, plain numbers ----------------
DEVICE_MASS_G = 480.0          # printed parts about 150, NEMA 11 about 140, rod, bearings, coupler, servo, boards, spider 60
LINE_SNAP_N = 27.0             # 6 lb mono parts here (doc 01); the mount must survive that on top of the weight
LINE_X, LINE_Z = -25.0, 45.0
DEVICE_CG_X = -5.0             # motor and spool near x 0, pad and fairlead at -x, servo at +x
SAFETY = 3.0
PLA_LAYER_BOND_MPA = 20.0      # conservative across-layer strength for PLA


def strength_report():
    W = DEVICE_MASS_G / 1000 * 9.81
    arm_w = DEVICE_CG_X - X_IN; arm_l = LINE_X - X_IN
    M = (W * arm_w + LINE_SNAP_N * arm_l) / 1000 * SAFETY          # N m about the wall, with the safety factor
    z_brace = 2 * BRACE_T * BRACE_Y1 ** 2 / 6                          # mm3, both braces at their root
    z_shelf = (Z1 - Z0) * SHELF_T ** 2 / 6                             # mm3, the shelf alone (if the braces were not there)
    top_row = M / ((PLATE_Y1 - SCREWS[0][1]) / 1000)                   # N pulling the top screw row off the beam
    print(f"load: weight {W:.1f} N at {arm_w:.0f} mm out, line snap {LINE_SNAP_N:.0f} N at {arm_l:.0f} mm out, safety x{SAFETY:.0f}: {M:.2f} N m at the wall")
    print(f"  braces at the wall: {M * 1000 / z_brace:.2f} MPa (PLA layer bond taken as {PLA_LAYER_BOND_MPA:.0f}): margin x{PLA_LAYER_BOND_MPA / (M * 1000 / z_brace):.0f}")
    print(f"  shelf alone, no braces: {M * 1000 / z_shelf:.1f} MPa: margin x{PLA_LAYER_BOND_MPA / (M * 1000 / z_shelf):.1f} (this is why the braces are there)")
    print(f"  top screw row pull-out: {top_row:.0f} N over 2 screws = {top_row / 2:.0f} N each (a #4 in softwood holds a few hundred)")
    print(f"  each device bolt: {(W + LINE_SNAP_N) * SAFETY / len(DEVICE_HOLES):.0f} N with all {len(DEVICE_HOLES)} in, {(W + LINE_SNAP_N) * SAFETY / 4:.0f} N with 4")


if __name__ == "__main__":
    m = wall_mount()
    print(f"wall_mount        watertight={m.is_watertight} size={np.round(m.extents, 1).tolist()} vol={m.volume / 1000:.1f}cm3")
    f = ld2450_fork_screw()
    print(f"ld2450_fork_screw watertight={f.is_watertight} size={np.round(f.extents, 1).tolist()} vol={f.volume / 1000:.1f}cm3")
    p = wall_mount_print()
    print(f"print: footprint {np.round(p.extents[:2], 1).tolist()}, height {p.extents[2]:.1f}; shelf top on the bed: {abs(p.bounds[0][2]) < 1e-6}")
    down = (p.face_normals[:, 2] < -0.7) & (p.triangles_center[:, 2] > 0.01)
    bed = (p.face_normals[:, 2] < -0.7) & ~down
    print(f"print overhang (down-facing area off the bed): {p.area_faces[down].sum():.0f} mm2 (the nut-pocket bridging: {len(DEVICE_HOLES)} pockets), bed contact {p.area_faces[bed].sum():.0f} mm2")
    # nut pockets landed: a probe the size of the pocket must be all void
    probe_ok = all(G.I(hex_prism_y(NUT_AF - 0.2, -SHELF_T + 0.1, -SHELF_T + NUT_T - 0.1, x, z), m).volume < 0.05 for x, z in DEVICE_HOLES)
    print(f"nut pockets are open on all {len(DEVICE_HOLES)} holes: {probe_ok}")
    A = assembly_wall()
    print("--- clash check, overlap volume in mm3 (none listed = clear) ---")
    bad = False
    for k, part in A.items():
        if k == "wall_mount": continue
        v = G.I(A["wall_mount"], part).volume
        if v > 0.5: print(f"CLASH wall_mount x {k}: {v:.1f}"); bad = True
    if not bad: print("wall_mount clears every device part")
    # the device's ceiling face lies flat on the shelf: highest device point at y 0, shelf underside at y 0
    dev_top = min(A[k].bounds[0][1] for k in A if k != "wall_mount" and not k.startswith("ld2450"))
    print(f"device ceiling face on the shelf underside: highest device point y {dev_top:.1f} (shelf underside y 0)")
    print(f"pad edge x -88 to the wall plate: {-88 - X_IN:.0f} mm; line falls {LINE_X - X_OUT:.0f} mm from the beam's face")
    # screwdriver paths: a 6 mm shaft along x from the screw head to open air past the device
    for i, (z, y) in enumerate(SCREWS):
        shaft = cylinder(radius=3.0, height=220, sections=32)
        shaft.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
        shaft.apply_translation([X_IN + 0.2 + 110, y, z])
        hits = [k for k, part in A.items() if k != "wall_mount" and G.I(shaft, part).volume > 0.5]
        print(f"screw {i + 1} at y {y:.0f} z {z:.0f}: straight screwdriver path along x is {'clear' if not hits else 'BLOCKED by ' + str(hits)}")
    # radar under the beam: clear of the beam, the wall plate and the device at every tilt
    P = porch()
    for t in np.arange(0, 61, 10.0):
        c, b = _radar_to_beam(S.ld2450_cradle(t)), _radar_to_beam(S.ld2450_board(t))
        hits = {k: round(G.I(c, part).volume + G.I(b, part).volume, 2) for k, part in list(A.items()) + list(P.items()) if k not in ("ld2450_cradle", "ld2450_radar")}
        hits = {k: v for k, v in hits.items() if v > 0.05}
        print(f"radar tilt {t:3.0f}: {'clear' if not hits else 'CLASH ' + str(hits)}")
    fs = A["ld2450_fork_screw"]
    print(f"fork plate against the beam's underside: plate face y {fs.bounds[0][1]:.1f}, beam bottom y {BEAM_BOTTOM_Y:.1f}")
    strength_report()
