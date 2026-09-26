"""
DropSpider Rev C.1 - LD2450 radar mount: a fork glued under the bracket's servo end,
and a cradle that tilts between the fork's ears on one M3 bolt.

The radar looks out from under the porch ceiling toward people walking in (+x),
standing upright as Hi-Link's manual figure 6 shows (44 mm edge vertical, antennas
out). The tilt is set on site: loosen the nut, swing the cradle, tighten. Any angle
from TILT_MIN to TILT_MAX clears the bracket and every other part (checked below).
The board goes in antenna side against the cradle's face plate (two big windows,
so it looks out mostly through air) with its circuit side and pin headers facing
back toward the device, open. It slides up into the edge grooves from the open
bottom end, header end last so the headers sit at the bottom: there the headers
and their dupont plugs (24 mm deep checked) clear everything at 30 to 60 degrees.
Header end at the top would hit the bracket above 40 degrees. A dab of hot glue
keeps the board in.

Hardware: one M3 bolt 20 to 25 mm long and a nut (a nylon-insert nut holds the
angle best).

Installed coordinates use the assembly frame in generate.py:
  y = 0 ceiling face (+y down), z along the rod, servo tower on +x.
Everything sits in the slab z 52.3..71.7, which below the bracket holds nothing
else: the spool ends at z 50, the servo at z 35, the 606ZZ plate starts at z 100.

Run on its own for the fit report: python sensor_mount.py
"""
import math
import numpy as np
import trimesh

import generate as G

# LD2450 board, Hi-Link manual figure 3
BOARD_L, BOARD_W, BOARD_T = 44.0, 15.0, 1.6
TILT_DEG = 50.0                # this porch: beam 10 in deep, device 12 in behind; model and pictures use it
TILT_MIN, TILT_MAX = 0.0, 60.0 # checked range
Z_CENTER = 62.0
PIVOT = (68.0, 13.0)           # (x, y) of the M3 pivot axis, installed; the axis runs along z
M3_CLEAR = 1.7                 # 3.4 mm hole

# cradle section, local coordinates: u down the board (0 = board top), v across (= z), w out of the antennas
LIP = 1.0
EDGE = BOARD_W / 2
RAIL_OUT = EDGE + 1.5          # 9.0: cradle half width (lightened 2026-09-26, was 9.7)
BACK_T = 1.2                   # was 2.0
BACK_W = -(1.5 + BACK_T)       # face plate 1.5 mm in front of the antenna side (flipped 2026-09-26)
FRONT_W = BOARD_T + 1.2
LEN = BOARD_L + 2.0
PIVOT_U, PIVOT_W = -10.5, 0.0  # pivot position in the cradle's local frame

# fork
KNUCKLE_HALF = 6.4             # cradle knuckle half width; the ears sit 0.3 mm outside it
EAR_T = 2.0                    # lightweight fork (owner's pick 2026-09-26): 2 mm ears
EAR_R = 4.5
PLATE_T = 2.0                  # 2 mm glue plate
FORK_HALF = KNUCKLE_HALF + 0.3 + EAR_T   # 8.7


def _along_v(m):
    """Turn a z-axis cylinder so it runs along local v (the local y axis)."""
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0])); return m


def _cradle_local():
    bx = G.bx
    rails = []
    for s in (1, -1):
        lo, hi = sorted((s * (EDGE - LIP), s * RAIL_OUT))
        rail = bx(0, LEN, lo, hi, BACK_W, FRONT_W)                       # u, v, w as x, y, z
        slot_lo, slot_hi = sorted((s * (EDGE - LIP - 0.1), s * (EDGE + 0.3)))
        rails.append(G.D(rail, bx(-1, LEN + 1, slot_lo, slot_hi, -0.2, BOARD_T + 0.2)))   # 1 mm lip front and back
    back = bx(0, LEN, -RAIL_OUT, RAIL_OUT, BACK_W, BACK_W + BACK_T)
    # face plate over the antenna side: two big windows, so the radar looks out mostly through air;
    # what plastic is left is 1.2 mm PLA ribs (top, middle, bottom)
    back = G.D(back, bx(1.0, LEN / 2 - 1.5, -5.5, 5.5, BACK_W - 1, BACK_W + BACK_T + 1),
               bx(LEN / 2 + 1.5, LEN - 1.5, -5.5, 5.5, BACK_W - 1, BACK_W + BACK_T + 1))
    top = bx(-1.5, 0, -RAIL_OUT, RAIL_OUT, BACK_W, FRONT_W)
    # knuckle: a round boss on the pivot, joined to the top block, narrow enough to sit between the ears
    boss = _along_v(G.cyl(4.0, 2 * KNUCKLE_HALF, -KNUCKLE_HALF))
    boss.apply_translation([PIVOT_U, 0, PIVOT_W])
    neck = bx(PIVOT_U, -1.0, -KNUCKLE_HALF, KNUCKLE_HALF, PIVOT_W - 3.0, PIVOT_W + 3.0)
    body = G.U(*rails, back, top, boss, neck)
    hole = _along_v(G.cyl(M3_CLEAR, 40, -20)); hole.apply_translation([PIVOT_U, 0, PIVOT_W])
    clear = bx(0, LEN + 1, -(EDGE - LIP - 0.1), EDGE - LIP - 0.1, BACK_W + BACK_T, 40)   # circuit side open for the pin headers
    edges = bx(0, LEN + 1, -(EDGE + 0.3), EDGE + 0.3, -0.2, BOARD_T + 0.2)
    # flat print: trim the knuckle flush with the face plate's outer face, which goes on the bed
    bed = bx(-20, LEN + 5, -20, 20, BACK_W - 10, BACK_W)
    return G.D(body, hole, clear, edges, bed)


def _place(m, tilt_deg):
    """Local (u, v, w) to installed (x, y, z), rotated about the pivot by the tilt."""
    t = math.radians(tilt_deg)
    a = np.array([-math.sin(t), math.cos(t), 0.0])     # down the board
    n = np.array([math.cos(t), math.sin(t), 0.0])      # beam: out toward the approach, and down
    # Flipped: the antenna side (local w = 0) faces the face plate (local -w), and the face plate
    # faces out along n. The circuit side with its pin headers faces back toward the device, open.
    v = np.array([0.0, 0.0, -1.0])
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2] = a, v, -n
    p = np.array([PIVOT[0], PIVOT[1], Z_CENTER])
    M[:3, 3] = p - (PIVOT_U * a - PIVOT_W * n)          # local pivot point lands on the installed pivot
    m = m.copy(); m.apply_transform(M); return m


def ld2450_cradle(tilt_deg=TILT_DEG):
    return _place(_cradle_local(), tilt_deg)


def ld2450_board(tilt_deg=TILT_DEG):
    """The radar itself, for clash checks and pictures."""
    return _place(G.bx(0, BOARD_L, -EDGE, EDGE, 0, BOARD_T), tilt_deg)


def ld2450_fork():
    """Glued flat to the bracket underside (y = 4). Two round ears carry the M3 pivot."""
    px, py = PIVOT
    plate = G.bx(62, 74, 4, 4 + PLATE_T, Z_CENTER - FORK_HALF, Z_CENTER + FORK_HALF)
    ears = []
    for z0 in (Z_CENTER - FORK_HALF, Z_CENTER + FORK_HALF - EAR_T):
        ears.append(G.U(G.cyl(EAR_R, EAR_T, z0, px, py), G.bx(px - EAR_R, px + EAR_R, 4 + PLATE_T - 0.5, py, z0, z0 + EAR_T)))
    return G.D(G.U(plate, *ears), G.cyl(M3_CLEAR, 40, Z_CENTER - 20, px, py))


def ld2450_fork_print():
    """Glue face down: the ears stand up as walls, the bolt hole runs sideways."""
    m = ld2450_fork()
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [1, 0, 0]))   # y = 4 face to the bed
    m.apply_translation(-m.bounds[0]); return m


def ld2450_cradle_print():
    """Lies flat, face plate on the bed (local w is up). The windows are plain holes, the rails
    and knuckle stand up from the plate, the pivot hole runs level; only the 1 mm groove lips
    overhang, by 1.3 mm. No supports."""
    m = _cradle_local()
    m.apply_translation(-m.bounds[0]); return m


if __name__ == "__main__":
    f = ld2450_fork()
    print(f"fork   watertight={f.is_watertight} size={np.round(f.extents, 1).tolist()} vol={f.volume / 1000:.1f}cm3")
    c0 = ld2450_cradle(0.0)
    print(f"cradle watertight={c0.is_watertight} size={np.round(c0.extents, 1).tolist()} vol={c0.volume / 1000:.1f}cm3")
    fp = ld2450_fork_print()
    print("fork print: lowest face is the glue face:", round(fp.bounds[0][2], 2), "height", round(fp.extents[2], 1))
    cp = ld2450_cradle_print()
    down = (cp.face_normals[:, 2] < -0.999) & (cp.vertices[cp.faces][:, :, 2].max(axis=1) < 1e-6)
    fl = cp.area_faces[down].sum()
    print(f"cradle print: size {np.round(cp.extents, 1).tolist()} (x, y, height), area on the bed {fl:.0f} mm2")
    A = G.assembly()
    for t in np.arange(TILT_MIN, TILT_MAX + 0.1, 5.0):
        c, b = ld2450_cradle(t), ld2450_board(t)
        hits = {"fork": G.I(c, f).volume, "board in cradle": G.I(c, b).volume, "board vs fork": G.I(b, f).volume}
        for k in ("bracket", "servo_sg90", "spool_body", "spool_ratchet", "finger", "fairlead_body", "switch_kw12", "motor_nema11"):
            hits[k] = G.I(c, A[k]).volume + G.I(b, A[k]).volume
        top = min(c.bounds[0][1], b.bounds[0][1])
        bad = {k: round(v, 2) for k, v in hits.items() if v > 0.05}
        print(f"tilt {t:4.0f} deg: highest point y {top:5.2f} (>= 4 ok)  {'clear' if not bad else 'CLASH ' + str(bad)}")
