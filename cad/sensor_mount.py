"""
DropSpider Rev C.1 - LD2450 radar holder, glued under the bracket's servo end (+x).

The radar looks out from under the porch ceiling, toward people walking in (+x),
standing upright as Hi-Link's manual figure 6 shows (44 mm edge vertical,
antennas out) and tilted TILT_DEG down so the beam meets people 1 to 3 m away
from about 2.3 m up. The board slides up into two edge grooves from the open
bottom end and stops against the top block; a dab of hot glue keeps it there.
Windows in the back plate leave room for the 1.25 mm plug at either end.

Installed coordinates use the assembly frame in generate.py:
  y = 0 ceiling face (+y down), z along the rod, servo tower on +x.
The holder's plate glues to the bracket underside (y = 4) at x 58..75, z 52..72,
clear of the servo, the ceiling screws at x 65 z 20/90, and the spool.

Run on its own for the numbers: python sensor_mount.py
"""
import math
import numpy as np
import trimesh

import generate as G

# LD2450 board, Hi-Link manual figure 3
BOARD_L, BOARD_W, BOARD_T = 44.0, 15.0, 1.6
TILT_DEG = 20.0               # beam tilted down from horizontal
Z_CENTER = 62.0               # holder centre along the rod
TOP_POINT = (70.0, 9.2)       # (x, y) of the board's top back corner line, installed

# holder section, local coordinates: u down the board (0 = top), v across, w out of the antennas
LIP = 1.0                     # how far the grooves overlap the board edge, front and back
EDGE = BOARD_W / 2
RAIL_OUT = EDGE + 2.2
BACK_W = -8.0                 # back plate outer face
BACK_T = 2.0
FRONT_W = BOARD_T + 1.2
LEN = BOARD_L + 2.0


def _local():
    bx = G.bx
    rails = []
    for s in (1, -1):
        lo, hi = sorted((s * (EDGE - LIP), s * RAIL_OUT))
        rail = bx(0, LEN, lo, hi, BACK_W, FRONT_W)                      # u, v, w as x, y, z
        slot_lo, slot_hi = sorted((s * (EDGE - LIP - 0.1), s * (EDGE + 0.3)))
        rail = G.D(rail, bx(-1, LEN + 1, slot_lo, slot_hi, -0.2, BOARD_T + 0.2))   # board edge groove: 1 mm lip front and back
        rails.append(rail)
    back = bx(0, LEN, -RAIL_OUT, RAIL_OUT, BACK_W, BACK_W + BACK_T)
    back = G.D(back, bx(1.5, 13, -5.5, 5.5, BACK_W - 1, BACK_W + BACK_T + 1),   # plug window, top end
               bx(LEN - 13, LEN + 1, -5.5, 5.5, BACK_W - 1, BACK_W + BACK_T + 1))  # plug window, bottom end
    top = bx(-2.5, 0, -RAIL_OUT, RAIL_OUT, BACK_W, FRONT_W)
    return G.U(*rails, back, top)


def _place(m):
    """Local (u, v, w) to installed (x, y, z): u runs down the tilted board, w is the beam direction."""
    t = math.radians(TILT_DEG)
    a = np.array([-math.sin(t), math.cos(t), 0.0])     # down the board
    n = np.array([math.cos(t), math.sin(t), 0.0])      # beam: out toward the approach and down
    v = np.array([0.0, 0.0, 1.0])
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2] = a, v, n
    M[:3, 3] = [TOP_POINT[0], TOP_POINT[1], Z_CENTER]
    m = m.copy(); m.apply_transform(M); return m


def ld2450_holder():
    frame = _place(_local())
    plate = G.bx(58, 75, 4, 7, Z_CENTER - RAIL_OUT, Z_CENTER + RAIL_OUT)
    top = _place(G.bx(-2.5, 0, -RAIL_OUT, RAIL_OUT, BACK_W, FRONT_W))
    web = trimesh.convex.convex_hull(np.vstack([plate.vertices, top.vertices]))
    # keep the space in front of the antennas and behind the board's parts clear of the web
    clear = _place(G.bx(0, LEN + 1, -(EDGE - LIP - 0.1), EDGE - LIP - 0.1, BACK_W + BACK_T, 40))
    edges = _place(G.bx(0, LEN + 1, -(EDGE + 0.3), EDGE + 0.3, -0.2, BOARD_T + 0.2))
    return G.D(G.U(frame, plate, web), clear, edges)


def ld2450_board():
    """The radar itself, for clash checks and pictures."""
    return _place(G.bx(0, BOARD_L, -EDGE, EDGE, 0, BOARD_T))


def ld2450_holder_print():
    """Lies on its side (the z face): rails, grooves and windows print with no supports."""
    m = ld2450_holder()
    m.apply_translation(-m.bounds[0]); return m


if __name__ == "__main__":
    h, b = ld2450_holder(), ld2450_board()
    print(f"holder watertight={h.is_watertight} size={np.round(h.extents, 1).tolist()} vol={h.volume / 1000:.1f}cm3")
    print("holder bounds x y z:", np.round(h.bounds, 1).tolist())
    print("board bounds  x y z:", np.round(b.bounds, 1).tolist())
    print("board overlaps holder (should be 0):", round(G.I(h, b).volume, 2))
    print("highest point y (must stay >= 4, nothing above the bracket underside):", round(h.bounds[0][1], 2))
