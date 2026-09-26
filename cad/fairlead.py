"""
Rev C.1 fairlead + limit switch unit. Replaces line_guide.stl. Bracket unchanged.
Assembly frame as in generate.py: y from the ceiling face (+y toward floor), z from the motor plate.
Line axis: x = -25, z = 45 (center of the 6 mm line channel), vertical (along y).

Parts:
  fairlead_body.stl  glues to the pad in the old line guide's spot (rail over the x=-32 holes)
  fairlead_flap.stl  hinged bumper. The stop bead lifts it; its tail presses the KW12-3 roller.
Hinge pin: an M2 bolt, 16 to 20 mm (owner 2026-09-26; filament was too tight). In from the flap side,
free in the flap's 2.5 mm hole, threads itself into the body's 1.9 mm hole.
Switch: KW12-3 roller lever, 2x M2 x 12 screws + nuts through slotted holes (adjust the click point).

Run on its own for the travel and clash report: python fairlead.py
"""
import math, numpy as np, trimesh
from generate import U, D, I, bx, cyl, vcyl
from trimesh.creation import revolve, cylinder

LX, LZ = -25.0, 45.0          # line axis
HY, HZ = 84.0, 58.0           # flap mid-plane y, hinge z
PY = HY - 1.8                 # hinge pin axis y: above the flap mid-plane so the flap prints flat
FT = 2.4                      # flap thickness (y)
STOP_Y = 78.0                 # underside of the fairlead block = hard stop for the flap
TAIL_Z = 75.0                 # roller contact point on the flap tail
SW_BODY_TOP, SW_BODY_BOT = 95.3, 105.5   # KW12-3 body (lever side up toward the ceiling)
SW_HOLE_Y = SW_BODY_BOT - 2.9            # mounting hole line
SW_Z0 = 71.0                  # body end nearest the roller
SW_HOLES_Z = (SW_Z0 + 5.25, SW_Z0 + 5.25 + 9.5)
SW_X0, SW_X1 = -28.2, -21.8   # body thickness 6.4, roller centered on x = -25

def xcyl(r, x0, x1, y, z, sections=48):
    c = cylinder(radius=r, height=x1 - x0, sections=sections)
    c.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0]))
    c.apply_translation([(x0 + x1) / 2, y, z]); return c

def trumpet():
    """Void for the fairlead bore: flared top (spool side) and bottom, 3.2 mm throat at y = 74."""
    top, throat, bot = 69.0, 74.0, STOP_Y + 0.5
    prof = [(0, top)]
    for k in range(9):                          # top flare, rounded: r 4.6 -> 1.6
        t = k / 8; prof.append((1.6 + 3.0 * (1 - t) ** 2, top + (throat - top) * t))
    for k in range(1, 9):                       # bottom flare: r 1.6 -> 3.0
        t = k / 8; prof.append((1.6 + 1.4 * t ** 2, throat + (bot - throat) * t))
    prof.append((0, bot))
    v = revolve(np.array(prof), sections=64)    # axis = z
    v.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0]))   # z -> +y
    if v.volume < 0: v.invert()
    # Guard: an extra y flip here once put the bore at y -78, so the cut missed the block and the
    # fairlead printed solid (found by the owner 2026-09-26). The bore must span the block.
    assert top - 0.1 < v.bounds[0][1] and v.bounds[1][1] < bot + 0.1, v.bounds
    v.apply_translation([LX, 0, LZ]); return v

def fairlead_body():
    rail  = bx(-36, -26, 3, 7, 20, 91)                     # glue footprint, same as the old guide
    spine = bx(-36, -29, 3, 92, 54, 70)                    # carries the hinge
    block = bx(-36, -19, 70, STOP_Y, 39, 62)               # fairlead + hard stop face
    rest  = bx(-36, -26, 80.0, HY - FT / 2 - 0.2, 63.5, 67.5)   # rest stop above the flap tail
    swpl  = bx(-36, -28.2, 86, 108, 64, 92)                # switch plate, switch on its +x face
    b = U(rail, spine, block, rest, swpl)
    cuts = [vcyl(1.7, 10, 0, -32, 28), vcyl(1.7, 10, 0, -32, 83),        # alignment pin holes
            trumpet(),
            xcyl(0.95, -37, -28, PY, HZ),                                   # 1.9: the M2 hinge bolt threads itself in
            bx(-29.01, -16, HY - 3.6, HY + 3.6, HZ - 3.6, HZ + 3.6)]        # knuckle clearance
    for z in SW_HOLES_Z:                                                    # 2.4 wide slots, +-2.5 mm in y
        cuts += [xcyl(1.2, -37, -27, SW_HOLE_Y - 2.5, z), xcyl(1.2, -37, -27, SW_HOLE_Y + 2.5, z),
                 bx(-37, -27, SW_HOLE_Y - 2.5, SW_HOLE_Y + 2.5, z - 1.2, z + 1.2)]
    return D(b, *cuts)

def fairlead_flap():
    plate = bx(-27.9, -17, HY - FT / 2, HY + FT / 2, 33, 78)              # free end z 33, tail to z 78
    knuckle = U(xcyl(3.0, -27.9, -17, PY, HZ), bx(-27.9, -17, PY, HY + FT / 2, HZ - 3, HZ + 3))   # flat bottom, prints flat
    f = U(plate, knuckle)
    slot = U(bx(LX - 1.7, LX + 1.7, HY - 4, HY + 4, 30, LZ),
             vcyl(1.7, 8, HY - 4, LX, LZ))                                  # open slot to the line hole
    return D(f, slot, xcyl(1.25, -30, -15, PY, HZ))                         # 2.5 pin hole, free (prints sideways, comes out small)

def switch_model():
    body = bx(SW_X0, SW_X1, SW_BODY_TOP, SW_BODY_BOT, SW_Z0, SW_Z0 + 20)
    pins = bx(SW_X0 + 2, SW_X1 - 2, SW_BODY_BOT, SW_BODY_BOT + 6.4, SW_Z0 + 2, SW_Z0 + 18)
    roller = xcyl(2.4, LX - 1.5, LX + 1.5, HY + FT / 2 + 0.3 + 2.4, TAIL_Z)
    return U(body, pins, roller)

def rotate_flap(m, deg):
    r = trimesh.transformations.rotation_matrix(math.radians(deg), [1, 0, 0], point=[0, PY, HZ])
    mm = m.copy(); mm.apply_transform(r); return mm

if __name__ == "__main__":
    import generate as G
    body, flap, sw = fairlead_body(), fairlead_flap(), switch_model()
    for n, m in [("fairlead_body", body), ("fairlead_flap", flap)]:
        print(n, "watertight", m.is_watertight, "vol cm3", round(m.volume / 1000, 1), "extents", np.round(m.extents, 1))
    A = G.assembly()
    for k in ("line_guide", "fairlead_body", "fairlead_flap", "switch_kw12"): A.pop(k, None)
    print("--- clashes (mm3) ---")
    for k in ("spool_ratchet", "spool_body", "bracket", "finger", "servo_sg90", "motor_nema11", "spacer_B", "rod_6mm"):
        for n, m in [("body", body), ("flap", flap), ("switch", sw)]:
            v = I(A[k], m).volume
            if v > 0.3: print(f"CLASH {n} x {k}: {v:.1f}")
    path = vcyl(1.0, 60, 60, LX, LZ)          # 2 mm rod down the line's path, y 60..120
    lb, lf = I(path, body).volume, I(path, flap).volume
    print(f"line path clear through the fairlead: {lb < 0.01} ({lb:.2f} mm3), through the flap slot: {lf < 0.01} ({lf:.2f} mm3)")
    print("body x flap at rest:", round(I(body, flap).volume, 2))
    print("switch x body:", round(I(body, sw).volume, 2), " switch x flap:", round(I(sw, flap).volume, 2))
    ring = trimesh.creation.annulus(r_min=33.01, r_max=35, height=16); ring.apply_translation([0, 40, 43])
    print("spool 2 mm clearance vs body:", round(I(ring, body).volume, 2))
    for deg in np.arange(0, 25, 0.25):
        f2 = rotate_flap(flap, -deg)          # negative = free end rises toward the ceiling
        if I(f2, body).volume > 0.2:
            print(f"hard stop at {deg:.2f} deg (free end up)"); break
    a = math.radians(deg)
    print(f"bead lift at stop {13 * math.sin(a):.2f} mm; roller push at stop {(TAIL_Z - HZ) * math.sin(a):.2f} mm (switch needs 2.6 + 0.8 = 3.4)")
    for deg2 in np.arange(0, 25, 0.25):
        f3 = rotate_flap(flap, deg2)
        if I(f3, body).volume > 0.2:
            print(f"rest stop at {deg2:.2f} deg below level (free end down)"); break
