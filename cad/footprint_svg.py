"""
Bracket footprint for a laser cutter or a paper drilling template: the base's outer face (y = 0) outline
with every hole through it, 1:1 in millimeters. Writes cad/bracket_footprint.svg (ceiling install), and
cad/bracket_footprint_inverted.svg for the inverted install (docs/06): the same face with the five holes to
drill (line, 2 fairlead block screws, 2 radar fork screws), labelled, with the block's and the fork's outlines.

Ceiling drawing: seen from the room, looking up at the ceiling (the way a template held against the ceiling
reads): x (servo side) to the right, z (along the rod, motor end first) top to bottom.
Inverted drawing: seen from OUTSIDE the base face, which is how a paper template laid on that face reads (from
below when hung). Looking at the face from outside, the servo side (+x) is on the LEFT, so this drawing is
the ceiling one mirrored left to right. Checked 2026-09-28: camera looking along +y with z down the page has
+x pointing left (right = forward x up = (0,1,0) x (0,0,-1) = (-1,0,0)).
Cut lines: red hairline. Labels and part outlines: blue (set to engrave or ignore).

Run: python footprint_svg.py
"""
import os
import numpy as np
import generate as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bracket_footprint.svg")
OUT_INV = os.path.join(HERE, "bracket_footprint_inverted.svg")
MARGIN = 5.0


def footprint(mesh, y=0.2):
    """Shapely polygons of a mesh cut by the plane at height y (default 0.2 mm above the base's outer face)."""
    sec = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    to_2d = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], float)   # (x, z) in plane
    path, _ = sec.to_planar(to_2D=to_2d, check=False)
    return path.polygons_full


def as_circle(ring):
    """Center and radius if the ring is a circle (within 0.05 mm), else None."""
    p = np.asarray(ring.coords)[:-1]
    c = p.mean(axis=0); r = np.hypot(*(p - c).T)
    return (c, r.mean()) if len(p) >= 16 and r.max() - r.min() < 0.05 else None


def main(mesh=None, out_path=OUT, caption="DropSpider bracket, ceiling face, seen from below. 1:1 mm. Red = cut.",
         drilled=(), mirror=False, outlines=(), labels=(), legend=(), legend_at=(0, 0), scale_bar=False):
    """drilled: (x, z, d) holes drawn in blue as drilled by hand. mirror: draw +x to the left.
    outlines: shapely polygons drawn dashed blue. labels: (x, z, text) in model mm, text starting there.
    legend: lines of text starting at legend_at (drawing mm). scale_bar: a 100 mm bar to check the print scale."""
    polys = footprint(G.bracket() if mesh is None else mesh)
    allp = np.vstack([np.asarray(pg.exterior.coords) for pg in polys])
    x0, z0 = allp.min(axis=0) - MARGIN
    x1, z1 = allp.max(axis=0) + MARGIN
    W, H = x1 - x0, z1 - z0
    if scale_bar: H += 10
    X = (lambda x: x1 - x) if mirror else (lambda x: x - x0)
    Z = lambda z: z - z0
    f = lambda v: f"{v:.3f}"
    cut = 'fill="none" stroke="#ff0000" stroke-width="0.1"'
    blue = 'fill="none" stroke="#0000ff" stroke-width="0.15"'
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(W)}mm" height="{f(H)}mm" viewBox="0 0 {f(W)} {f(H)}">',
           f'<title>{"DropSpider bracket, inverted install drilling template" if mirror else "DropSpider bracket ceiling footprint"}, 1:1 mm</title>']
    ring_d = lambda coords: "M " + " L ".join(f"{f(X(x))} {f(Z(z))}" for x, z in coords) + " Z"
    holes = []
    for pg in polys:
        out.append(f'<path {cut} d="{ring_d(pg.exterior.coords[:-1])}"/>')
        for ring in pg.interiors:
            c = as_circle(ring)
            if c is not None:
                (cx, cz), r = c
                out.append(f'<circle {cut} cx="{f(X(cx))}" cy="{f(Z(cz))}" r="{f(r)}"/>')
                holes.append(f"circle d {2 * r:.2f} at x {cx:.1f}, z {cz:.1f}")
            else:
                out.append(f'<path {cut} d="{ring_d(ring.coords[:-1])}"/>')
                b = ring.bounds
                holes.append(f"cutout {b[2] - b[0]:.1f} x {b[3] - b[1]:.1f} at x {b[0]:.1f}..{b[2]:.1f}, z {b[1]:.1f}..{b[3]:.1f}")
    for pg in outlines:
        out.append(f'<path {blue} stroke-dasharray="1.2 0.8" d="{ring_d(pg.exterior.coords[:-1])}"/>')
    lab = 'fill="#0000ff" font-family="Arial" font-size="{}"'
    for x, z, d in drilled:   # a small cross at every hole to drill, so the centre punch has a mark
        cx, cz = X(x), Z(z)
        out.append(f'<path {blue} d="M {f(cx - d / 2 - 1)} {f(cz)} L {f(cx + d / 2 + 1)} {f(cz)} M {f(cx)} {f(cz - d / 2 - 1)} L {f(cx)} {f(cz + d / 2 + 1)}"/>')
        if not labels:
            out.append(f'<text {lab.format(3)} x="{f(cx + d / 2 + 1)}" y="{f(cz - d / 2 - 0.5)}">drill {d:g}</text>')
    for x, z, text in labels:
        out.append(f'<text {lab.format(2.4)} x="{f(X(x))}" y="{f(Z(z))}">{text}</text>')
    for i, line in enumerate(legend):
        out.append(f'<text {lab.format(2.2)} x="{f(legend_at[0])}" y="{f(legend_at[1] + 3 * i)}">{line}</text>')
    if scale_bar:
        yb = H - 7
        out.append(f'<path {blue} d="M {f(MARGIN)} {f(yb)} L {f(MARGIN + 100)} {f(yb)} M {f(MARGIN)} {f(yb - 1.5)} L {f(MARGIN)} {f(yb + 1.5)} M {f(MARGIN + 100)} {f(yb - 1.5)} L {f(MARGIN + 100)} {f(yb + 1.5)}"/>')
        out.append(f'<text {lab.format(2.4)} x="{f(MARGIN + 103)}" y="{f(yb + 0.8)}">100 mm: measure it after printing</text>')
    out.append(f'<text {lab.format(3 if not mirror else 2.4)} x="{f(MARGIN if mirror else MARGIN + 2)}" y="{f(H - 1.5)}">{caption}</text>')
    out.append("</svg>")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print(f"wrote {out_path}: {W:.1f} x {H:.1f} mm, {len(polys)} outline(s), {len(holes)} holes")
    for h in holes: print("  " + h)


def main_inverted():
    import inverted as INV
    import sensor_mount as S
    (lx, lz), bs, rs = (INV.LINE_X, INV.LINE_Z), INV.BLOCK_SCREWS, INV.RADAR_SCREWS
    drilled = [(lx, lz, INV.LINE_HOLE_D)] + [(x, z, 3.4) for x, z in bs + rs]
    # where the parts sit: cut just under the base's outer face
    block = footprint(INV.fairlead_base(), -0.3)
    fork = footprint(INV.radar_on_base()["ld2450_fork_screw"], -0.3)
    edge_x = G.bracket().bounds[1][0]          # servo-side edge of the base, x 75
    fz = [z for _, z in rs]
    labels = [
        (bs[0][0] + 12, bs[0][1] - 6.5, f"FAIRLEAD BLOCK: 2x drill 3.4"),
        (lx - 7, lz + 1, f"LINE: drill {INV.LINE_HOLE_D:g}"),
        (rs[0][0] + 7, min(fz) - 7.5, f"RADAR FORK: 2x drill 3.4"),
    ]
    legend = [
        "Distances to each hole's centre, in mm,",
        "from the servo-side edge (left) and",
        "from the motor end (top):",
        f"line: {edge_x - lx:g} in, {lz:g} down",
        f"fairlead block: {edge_x - bs[0][0]:g} in, {bs[0][1]:g} and {bs[1][1]:g} down",
        f"radar fork: {edge_x - rs[0][0]:g} in, {fz[0]:g} and {fz[1]:g} down",
        "Dashed blue: where the block and the",
        "fork sit. Red circles with no cross:",
        "the bracket's own holes, not used.",
    ]
    main(INV.bracket_inverted(), OUT_INV,
         "DropSpider bracket, base outer face seen from outside (from below when hung). Lay the 1:1 print on that face, printed side up, and drill through the crosses. Brace holes are the owner's.",
         drilled, mirror=True, outlines=list(block) + list(fork), labels=labels, legend=legend,
         legend_at=(edge_x - 5 + MARGIN + 42, 58), scale_bar=True)


if __name__ == "__main__":
    main(); main_inverted()
