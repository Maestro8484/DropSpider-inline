"""
Bracket footprint for a laser cutter: the ceiling face (y = 0) outline with every hole through it,
1:1 in millimeters. Writes cad/laser/bracket_footprint.svg.

View: from the room, looking up at the ceiling (the way a paper or plywood template held against
the ceiling reads). x runs left to right; z (along the rod, motor end first) runs top to bottom.
Cut lines: red hairline. Labels: blue (set to engrave or ignore).

Run: python footprint_svg.py
"""
import os
import numpy as np
import generate as G

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laser", "bracket_footprint.svg")
MARGIN = 5.0


def footprint():
    """Shapely polygons of the bracket cut 0.2 mm above its ceiling face."""
    sec = G.bracket().section(plane_origin=[0, 0.2, 0], plane_normal=[0, 1, 0])
    to_2d = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], float)   # (x, z) in plane
    path, _ = sec.to_planar(to_2D=to_2d, check=False)
    return path.polygons_full


def as_circle(ring):
    """Center and radius if the ring is a circle (within 0.05 mm), else None."""
    p = np.asarray(ring.coords)[:-1]
    c = p.mean(axis=0); r = np.hypot(*(p - c).T)
    return (c, r.mean()) if len(p) >= 16 and r.max() - r.min() < 0.05 else None


def main():
    polys = footprint()
    allp = np.vstack([np.asarray(pg.exterior.coords) for pg in polys])
    x0, z0 = allp.min(axis=0) - MARGIN
    x1, z1 = allp.max(axis=0) + MARGIN
    W, H = x1 - x0, z1 - z0
    f = lambda v: f"{v:.3f}"
    cut = 'fill="none" stroke="#ff0000" stroke-width="0.1"'
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(W)}mm" height="{f(H)}mm" viewBox="0 0 {f(W)} {f(H)}">',
           '<title>DropSpider bracket ceiling footprint, 1:1 mm</title>']
    holes = []
    for pg in polys:
        d = "M " + " L ".join(f"{f(x - x0)} {f(z - z0)}" for x, z in pg.exterior.coords[:-1]) + " Z"
        out.append(f'<path {cut} d="{d}"/>')
        for ring in pg.interiors:
            c = as_circle(ring)
            if c is not None:
                (cx, cz), r = c
                out.append(f'<circle {cut} cx="{f(cx - x0)}" cy="{f(cz - z0)}" r="{f(r)}"/>')
                holes.append(f"circle d {2 * r:.2f} at x {cx:.1f}, z {cz:.1f}")
            else:
                d = "M " + " L ".join(f"{f(x - x0)} {f(z - z0)}" for x, z in ring.coords[:-1]) + " Z"
                out.append(f'<path {cut} d="{d}"/>')
                b = ring.bounds
                holes.append(f"cutout {b[2] - b[0]:.1f} x {b[3] - b[1]:.1f} at x {b[0]:.1f}..{b[2]:.1f}, z {b[1]:.1f}..{b[3]:.1f}")
    lab = 'fill="#0000ff" font-family="Arial" font-size="3"'
    out.append(f'<text {lab} x="{f(MARGIN + 2)}" y="{f(H - 1.5)}">DropSpider bracket, ceiling face, seen from below. 1:1 mm. Red = cut.</text>')
    out.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
    print(f"wrote {OUT}: {W:.1f} x {H:.1f} mm, {len(polys)} outline(s), {len(holes)} holes")
    for h in holes: print("  " + h)


if __name__ == "__main__":
    main()
