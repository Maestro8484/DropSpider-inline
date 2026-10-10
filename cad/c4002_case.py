"""
DropSpider - C4002 radar case on the radar fork. Drawn from scratch 2026-10-10 after the layout of
"DFRobot C4002 mmWave enclosure" by user_643277529 on MakerWorld (makerworld.com/en/models/2826754,
released 2026-05-20, CC BY-NC-SA): a box with a 1 mm floor the radar looks through, a snap lid, the
board on four supports. This remix carries the same license: credit the original, no commercial
use, share changes alike. The original download, unchanged: cad/ref/c4002_enclosure/.

The owner's calls, 2026-10-08 and 2026-10-10:
  - No ESP32 half: the box holds the radar only.
  - No screws: the board rests on two flat buttons (pin end) and a 1 mm ledge (far end); four posts
    on the lid hold it down.
  - Nothing in front of the antenna (2026-10-10): a 20.8 x 20.8 mm opening in the floor under both
    gold antenna squares. PLA in front of a 24 GHz antenna costs range by reflection (a 1 mm floor
    about 6 to 10 percent, by a flat-sheet calculation); the case is outdoors a day or two, out of
    the rain, so the opening is left open.
  - Prints flat, no supports: nothing hangs over air steeper than 45 degrees except the tops of the
    snap slots, which are bridges; the bolt hole is a teardrop; the lid prints plate down.
  - Knuckle and wire opening on the same end (the board's pin end), opening 15 mm wide.
  - Inside 22.75 mm wide (was 22.2), body 2 mm taller (10, was 8). The lid is unchanged in thickness.

Board: the C4002, 22 x 26 mm (DFRobot wiki), two holes at the corners beside its 5 pins. It lies
antenna side toward the 1 mm floor, pins at the knuckle end, far edge against the far wall.

Frame: x across (0 to W), y along (0 = the knuckle end's outer face, the knuckle at y < 0), z up
from the bed. Run on its own for the report: python c4002_case.py   (writes nothing)
Export the two STLs: python c4002_case.py --export (only if changed); picture: --picture
"""
import math, os, sys
import numpy as np
import trimesh

import generate as G
import sensor_mount as S

HERE = os.path.dirname(os.path.abspath(__file__))

# box
IW = 22.75            # inside width (owner 2026-10-10)
IL = 31.5             # inside length: the 26 mm board plus 5.5 mm at the pin end for the wires
WALL, FLOOR = 1.5, 1.0
W, L = IW + 2 * WALL, IL + 2 * WALL     # 25.75 x 34.5 outside
H = 10.0              # body height (owner 2026-10-10: 2 mm taller than the 8 of the original)
CR = 1.5              # corner radius, as the original
CX = W / 2
# board
BOARD_L, BOARD_W, BOARD_T = 26.0, 22.0, 1.6
BOARD_Z = 3.0         # board's underside: the buttons are 2 mm tall on the 1 mm floor
BOARD_Y1 = WALL + IL  # far edge against the far wall
BOARD_Y0 = BOARD_Y1 - BOARD_L
BUTTON_D, POST_D, CORNER = 4.0, 3.0, 2.0     # buttons and posts centred 2 mm in from the board's corner edges
BX0 = CX - BOARD_W / 2 + CORNER
# The board rests on two buttons under its pin-end corners (where its holes are, no antenna) and on a
# 1 mm ledge along the far wall under its far edge (the far corners carry the antenna's gold).
BUTTONS = [(x, BOARD_Y0 + CORNER) for x in (BX0, W - BX0)]
LEDGE = 1.0
POSTS = BUTTONS + [(x, BOARD_Y1 - 1.5) for x in (BX0, W - BX0)]
POST_GAP = 0.0        # gap between a post's tip and the board, mm; raise it if the lid will not snap shut
# Antenna opening (owner 2026-10-10: "1 yes - proceed"; outdoors a day or two, no rain, little dust).
# The C4002's two gold antenna squares, read off DFRobot's photo with rulers (about 0.3 mm), in the
# photo's frame: x from the board's left seen from the antenna side, y down from the far edge.
GOLD = [(12.9, 20.9, 1.4, 10.0), (1.1, 8.6, 12.5, 20.9)]
RIM = 1.0             # floor left along each side wall, so the walls are not free-standing
WIN_X = (WALL + RIM, W - WALL - RIM)
WIN_Y = (BOARD_Y0 + CORNER + BUTTON_D / 2 + 0.2, BOARD_Y1 - LEDGE)


def gold_in_case():
    """The gold squares in case coordinates: antenna side down and pins at the knuckle end, so seen
    from above the photo is mirrored: x = CX + 11 - x_photo, y = far edge - y_photo."""
    return [(CX + BOARD_W / 2 - x1, CX + BOARD_W / 2 - x0, BOARD_Y1 - y1, BOARD_Y1 - y0) for x0, x1, y0, y1 in GOLD]
# wire opening in the knuckle end's wall, open at the top (the lid closes it)
NOTCH_W, NOTCH_Z0 = 15.0, BOARD_Z
# knuckle, the LD2450 cradle's: 8 mm round, 3.4 hole, 12.8 wide, between the fork's ears
KH = S.KNUCKLE_HALF   # 6.4
BOSS_R = 4.0
PIVOT_Y = -12.0       # 12 mm out from the end wall: 8 mm between wall and boss for the wires to turn
PIVOT_Z = H / 2
# lid and snaps
LID_T = 1.5
TAB_T, TAB_L, TAB_GAP = 1.0, 5.0, 0.3        # tab thickness, length down from the lid, gap to the wall
HOOK = 0.6            # hook stands out of the tab: 0.3 to reach the wall, 0.3 into the slot
HOOK_S0 = 3.4         # hook's catch starts this far down from the lid (45 degrees to full height at 4.0)
SLOT_Z0, SLOT_Z1 = 5.4, 6.4                  # through-slots in the walls the hooks click into
SIDE_TAB_Y = (BOARD_Y0 + 4.0, BOARD_Y1 - 6.0)  # side tabs between the buttons
FAR_TAB_HALF = 8.0


def _rrect(x0, y0, x1, y1, r):
    from shapely.geometry import box as sbox
    return sbox(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, 32)


def _prism(poly, z0, z1):
    m = trimesh.creation.extrude_polygon(poly, z1 - z0); m.apply_translation([0, 0, z0]); return m


def _along_x(m):
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 1, 0])); return m


def knuckle():
    """Round on top for the swing, square below so it stands on the bed. The neck's top is the
    wire opening's floor, so the wires come out onto it."""
    boss = _along_x(G.cyl(BOSS_R, 2 * KH, -KH)); boss.apply_translation([CX, PIVOT_Y, PIVOT_Z])
    neck = G.bx(CX - KH, CX + KH, PIVOT_Y, 0.5, 0, NOTCH_Z0)               # overlaps the end wall 0.5
    foot = G.bx(CX - KH, CX + KH, PIVOT_Y - BOSS_R, PIVOT_Y + BOSS_R, 0, PIVOT_Z)
    return G.U(boss, neck, foot)


def bolt_hole():
    """3.4 mm teardrop along x: the round hole plus a 45 degree point on top, no support."""
    r = S.M3_CLEAR
    h = _along_x(G.cyl(r, 40, -20)); h.apply_translation([CX, PIVOT_Y, PIVOT_Z])
    d = G.bx(-20, 20, -r, r, -r, r)
    d.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 4, [1, 0, 0]))
    d.apply_translation([CX, PIVOT_Y, PIVOT_Z])
    top = G.I(d, G.bx(-30, 30, PIVOT_Y - 5, PIVOT_Y + 5, PIVOT_Z + r * 0.7071, PIVOT_Z + 5))
    return G.U(h, top)


def c4002_case_base():
    outer = _prism(_rrect(0, 0, W, L, CR), 0, H)
    inner = G.bx(WALL, W - WALL, WALL, L - WALL, FLOOR, H + 1)
    buttons = [G.cyl(BUTTON_D / 2, BOARD_Z - FLOOR + 0.01, FLOOR - 0.01, x, y) for x, y in BUTTONS]
    ledge = G.bx(WALL - 0.01, W - WALL + 0.01, BOARD_Y1 - LEDGE, L - WALL + 0.01, FLOOR - 0.01, BOARD_Z)
    window = G.bx(WIN_X[0], WIN_X[1], WIN_Y[0], WIN_Y[1], -1, FLOOR + 0.01)
    notch = G.bx(CX - NOTCH_W / 2, CX + NOTCH_W / 2, -1, WALL + 0.01, NOTCH_Z0, H + 1)
    y0, y1 = SIDE_TAB_Y
    slots = [G.bx(-1, WALL + 0.01, y0 - 0.5, y1 + 0.5, SLOT_Z0, SLOT_Z1),
             G.bx(W - WALL - 0.01, W + 1, y0 - 0.5, y1 + 0.5, SLOT_Z0, SLOT_Z1),
             G.bx(CX - FAR_TAB_HALF - 0.5, CX + FAR_TAB_HALF + 0.5, L - WALL - 0.01, L + 1, SLOT_Z0, SLOT_Z1)]
    return G.D(G.U(G.D(outer, inner), *buttons, ledge, knuckle()), notch, bolt_hole(), window, *slots)


def _tab(axis, sign, a0, a1, face):
    """A snap tab hanging from the lid (assembled position), its outer face at `face` on `axis`
    ('x' or 'y'), hook pointing `sign` (+1/-1) along that axis, running a0..a1 along the other.
    Profile, s = depth below the lid's inner face (z = H - s): tab from s 0 to TAB_L; hook rises at
    45 degrees from s HOOK_S0 to full HOOK at HOOK_S0 + HOOK, then tapers back to the tab at the tip."""
    prof = [(-0.1, HOOK_S0), (HOOK, HOOK_S0 + HOOK + 0.1), (-0.1, TAB_L)]   # (out from the tab face, s); 0.1 into the tab
    pts = []
    for a in (a0, a1):
        for o, s in prof:
            c = face + sign * o
            pts.append((c, a, H - s) if axis == "x" else (a, c, H - s))
    hook = trimesh.convex.convex_hull(np.array(pts))
    lo, hi = sorted((face, face - sign * TAB_T))
    body = G.bx(lo, hi, a0, a1, H - TAB_L, H + 0.01) if axis == "x" else G.bx(a0, a1, lo, hi, H - TAB_L, H + 0.01)
    return G.U(body, hook)


def lid_assembled():
    """The lid sitting on the base: plate z H to H + LID_T, tabs and posts hanging inside."""
    plate = _prism(_rrect(0, 0, W, L, CR), H, H + LID_T)
    y0, y1 = SIDE_TAB_Y
    tabs = [_tab("x", -1, y0, y1, WALL + TAB_GAP), _tab("x", +1, y0, y1, W - WALL - TAB_GAP),
            _tab("y", +1, CX - FAR_TAB_HALF, CX + FAR_TAB_HALF, L - WALL - TAB_GAP)]
    top = BOARD_Z + BOARD_T + POST_GAP
    posts = [G.cyl(POST_D / 2, H - top + 0.01, top, x, y) for x, y in POSTS]
    return G.U(plate, *tabs, *posts)


def c4002_case_lid():
    """Turned over for printing: plate on the bed, tabs and posts standing up."""
    l = lid_assembled()
    l.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [0, 1, 0]))
    l.apply_translation(-l.bounds[0]); return l


def overhangs(m, limit_deg=45.0, bed=0.05):
    """Faces pointing down more steeply than limit_deg from vertical that are not on the bed:
    (area mm2, list of (centre, area)), largest first."""
    n = m.face_normals; c = m.triangles_center
    k = (n[:, 2] < -math.sin(math.radians(limit_deg)) - 1e-3) & (c[:, 2] > bed)
    return m.area_faces[k].sum(), sorted(zip(np.round(c[k], 1).tolist(), np.round(m.area_faces[k], 2).tolist()), key=lambda t: -t[1])


def board():
    return G.bx(CX - BOARD_W / 2, CX + BOARD_W / 2, BOARD_Y0, BOARD_Y1, BOARD_Z, BOARD_Z + BOARD_T)


def _local(flip=False):
    """Base plus lid in the LD2450 cradle's frame (u along the case away from the pivot, v along the
    bolt, w out of the board with the antenna toward -w, pivot at u -10.5, w 0), so sensor_mount's
    _place puts it where the cradle was. flip=False: antenna toward the floor; True: toward the lid."""
    m = G.U(c4002_case_base(), lid_assembled())
    M = np.eye(4)
    if not flip:   # u = y - PIVOT_Y - 10.5, v = CX - x, w = z - PIVOT_Z
        M[:3, :3] = [[0, 1, 0], [-1, 0, 0], [0, 0, 1]]
        M[:3, 3] = [-PIVOT_Y - 10.5, CX, -PIVOT_Z]
    else:          # u = y - PIVOT_Y - 10.5, v = x - CX, w = PIVOT_Z - z
        M[:3, :3] = [[0, 1, 0], [1, 0, 0], [0, 0, -1]]
        M[:3, 3] = [-PIVOT_Y - 10.5, -CX, PIVOT_Z]
    m.apply_transform(M); return m


def case_on_porch(tilt, flip=False):
    """The case where inverted.py puts the cradle: placed like the cradle, then turned over under the base."""
    import inverted as V
    m = S._place(_local(flip), tilt)
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [0, 0, 1]))
    m.apply_translation([V.RADAR_SHIFT[0], V.RADAR_SHIFT[1], 0])
    m.apply_transform(V.RY_END)
    m.apply_translation([V.RADAR_FORK[0] + 62.0, 0, V.RADAR_FORK[1] + 62.0])
    return m


PARTS = {"c4002_case_base": c4002_case_base, "c4002_case_lid": c4002_case_lid}


def report():
    b, l, la, bd = c4002_case_base(), c4002_case_lid(), lid_assembled(), board()
    for name, m in (("c4002_case_base", b), ("c4002_case_lid", l)):
        area, faces = overhangs(m)
        print(f"{name:16s} watertight={m.is_watertight} size={np.round(m.extents, 2).tolist()} vol={m.volume / 1000:.2f}cm3; "
              f"over air steeper than 45 deg: {area:.1f} mm2" + (f", largest {faces[:4]}" if faces else ""))
    print(f"lid on base: overlap {G.I(la, b).volume:.3f} mm3 (0 = fits); board vs base {G.I(bd, b).volume:.3f}, vs lid {G.I(bd, la).volume:.3f}")
    touch = [bool(G.I(G.cyl(0.5, 0.3, BOARD_Z + BOARD_T + 0.01, x, y), la).volume > 0) for x, y in POSTS]
    rest = G.bx(CX - BOARD_W / 2, CX + BOARD_W / 2, BOARD_Y0, BOARD_Y1, BOARD_Z - 0.05, BOARD_Z)
    print(f"posts reach the board top: {touch}; board's underside touches base over {G.I(rest, b).volume / 0.05:.0f} mm2 "
          f"(two buttons and the far ledge); inside {IW} x {IL}, outside {W} x {L} x {H}")
    under = G.bx(CX - BOARD_W / 2, CX + BOARD_W / 2, BOARD_Y0, BOARD_Y1, -1, BOARD_Z)
    for i, (x0, x1, y0, y1) in enumerate(gold_in_case()):
        sq = G.bx(x0, x1, y0, y1, -1, BOARD_Z)
        m = min(x0 - WIN_X[0], WIN_X[1] - x1, y0 - WIN_Y[0], WIN_Y[1] - y1)
        print(f"gold square {i + 1}: x {x0:.1f}-{x1:.1f} y {y0:.1f}-{y1:.1f}; PLA under it {G.I(sq, b).volume:.2f} mm3; "
              f"opening edge {m:.1f} mm beyond it at the nearest side")
    print(f"opening x {WIN_X[0]:.2f}-{WIN_X[1]:.2f}, y {WIN_Y[0]:.2f}-{WIN_Y[1]:.2f} ({WIN_X[1] - WIN_X[0]:.1f} x {WIN_Y[1] - WIN_Y[0]:.1f} mm)")
    print(f"wire opening {NOTCH_W} wide, z {NOTCH_Z0} to {H} (lid closes the top); knuckle end: {-PIVOT_Y - BOSS_R:.1f} mm between the wall and the boss")
    import inverted as V
    A = V.assembly_inverted()
    skip = {"ld2450_cradle", "ld2450_radar"}
    for flip in (False, True):
        bad = []
        for t in range(0, 91, 5):
            c = case_on_porch(t, flip)
            hits = {k: round(G.I(c, A[k]).volume, 2) for k in A if k not in skip}
            hits = {k: v for k, v in hits.items() if v > 0.05}
            if hits: bad.append((t, hits))
        clear = [t for t in range(0, 91, 5) if t not in [x[0] for x in bad]]
        print(f"antenna toward the {'lid' if flip else 'floor'}: clear at tilt {clear} deg")
        for t, h in bad: print(f"   tilt {t}: {h}")


def picture(path):
    """One picture for the owner: base and lid as they print, and the case on the fork at 50 degrees."""
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    import raster, inverted as V
    b, l = c4002_case_base(), c4002_case_lid()
    lid_side = l.copy(); lid_side.apply_translation([W + 6, 0, 0])
    img1, _ = raster.render([(b, "#1d4f38"), (lid_side, "#4ade80")], elev=40, azim=-120, W=900, H=700)
    A = V.assembly_inverted()
    box = G.bx(-140, -40, -60, 20, 20, 100)
    parts = [(V.view_inv(G.I(A[k], box)), c) for k, c in (("bracket", "#9aa0a6"), ("ld2450_fork_screw", "#ea580c"), ("servo_sg90", "#0969da"))]
    parts.append((V.view_inv(case_on_porch(50)), "#1d4f38"))
    img2, _ = raster.render(parts, elev=-12, azim=210, W=900, H=700)
    fig, ax = plt.subplots(1, 2, figsize=(18, 7.6))
    ax[0].imshow(img1); ax[0].set_title("as printed: base (dark: knuckle and 15 mm wire opening on the same end) and lid (light)")
    ax[1].imshow(img2); ax[1].set_title("on the porch at 50 degrees, between the fork's ears (orange), under the base")
    for a in ax: a.axis("off")
    plt.tight_layout(); plt.savefig(path, dpi=80); plt.close(fig)


if __name__ == "__main__":
    if "--export" in sys.argv:
        for name, fn in PARTS.items(): print(f"{name}: {G.export_part(name, fn())}")
    report()
    if "--picture" in sys.argv:
        picture(os.path.join(HERE, "..", "docs", "img", "c4002_case.png")); print("picture: docs/img/c4002_case.png")
