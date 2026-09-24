"""Tiny z-buffer renderer (orthographic, flat shaded, outlined). No OpenGL needed."""
import numpy as np, matplotlib.colors as mc

def look(elev, azim):
    e, a = np.radians(elev), np.radians(azim)
    d = np.array([np.cos(e)*np.cos(a), np.cos(e)*np.sin(a), np.sin(e)])      # toward viewer
    up = np.array([0, 0, 1.0]); r = np.cross(up, d); r /= np.linalg.norm(r); u = np.cross(d, r)
    return r, u, d

def render(meshes, elev=25, azim=-60, W=1400, H=1000, pad=40, light=(0.3, 0.5, 0.8)):
    """meshes: list of (trimesh, color). Returns RGB image and projection info."""
    r, u, d = look(elev, azim); L = np.array(light, float); L /= np.linalg.norm(L)
    allv = np.vstack([m.vertices for m, _ in meshes])
    P = np.column_stack([allv @ r, allv @ u])
    lo, hi = P.min(0), P.max(0); s = min((W - 2*pad) / (hi[0]-lo[0]), (H - 2*pad) / (hi[1]-lo[1]))
    def proj(v):
        x = (v @ r - lo[0]) * s + pad; y = H - ((v @ u - lo[1]) * s + pad); z = v @ d; return x, y, z
    zbuf = np.full((H, W), -np.inf); img = np.ones((H, W, 3)); ids = np.full((H, W), -1)
    for pid, (m, col) in enumerate(meshes):
        c = np.array(mc.to_rgb(col)); x, y, z = proj(m.vertices)
        n = m.face_normals; shade = 0.35 + 0.65 * np.abs(n @ L) * 0.9 + 0.1 * (n @ d > 0)
        for fi, f in enumerate(m.faces):
            xs, ys, zs = x[f], y[f], z[f]
            x0, x1 = int(max(0, np.floor(xs.min()))), int(min(W-1, np.ceil(xs.max())))
            y0, y1 = int(max(0, np.floor(ys.min()))), int(min(H-1, np.ceil(ys.max())))
            if x1 < x0 or y1 < y0: continue
            den = (ys[1]-ys[2])*(xs[0]-xs[2]) + (xs[2]-xs[1])*(ys[0]-ys[2])
            if abs(den) < 1e-9: continue
            gx, gy = np.meshgrid(np.arange(x0, x1+1) + 0.5, np.arange(y0, y1+1) + 0.5)
            w0 = ((ys[1]-ys[2])*(gx-xs[2]) + (xs[2]-xs[1])*(gy-ys[2])) / den
            w1 = ((ys[2]-ys[0])*(gx-xs[2]) + (xs[0]-xs[2])*(gy-ys[2])) / den
            w2 = 1 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not inside.any(): continue
            zz = w0*zs[0] + w1*zs[1] + w2*zs[2]
            sub = zbuf[y0:y1+1, x0:x1+1]; upd = inside & (zz > sub)
            sub[upd] = zz[upd]
            img[y0:y1+1, x0:x1+1][upd] = np.clip(c * shade[fi], 0, 1)
            ids[y0:y1+1, x0:x1+1][upd] = pid
    # outlines: part boundaries and depth jumps
    edge = np.zeros((H, W), bool)
    edge[:, 1:] |= ids[:, 1:] != ids[:, :-1]; edge[1:, :] |= ids[1:, :] != ids[:-1, :]
    zf = np.where(np.isfinite(zbuf), zbuf, -1e6)
    edge[:, 1:] |= np.abs(zf[:, 1:] - zf[:, :-1]) > 2.0; edge[1:, :] |= np.abs(zf[1:, :] - zf[:-1, :]) > 2.0
    img[edge] = img[edge] * 0.25
    return img, proj
