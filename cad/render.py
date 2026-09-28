"""Renders assembly images into ../docs/img. Run after generate.py: python render.py"""
import os, math, numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import generate as G
import raster

IMG = os.path.join(G.HERE, "..", "docs", "img"); os.makedirs(IMG, exist_ok=True)
COL = {"bracket": "#9aa0a6", "spool_ratchet": "#1f6feb", "spool_body": "#58a6ff",
       "fairlead_body": "#8b5cf6", "fairlead_flap": "#d946ef", "fairlead_flap_inv": "#d946ef", "switch_kw12": "#111111",
       "finger": "#e5534b", "rod_6mm": "#444", "coupler": "#d4a72c", "spacer_A": "#2da44e", "spacer_B": "#2da44e",
       "bearing_606": "#57606a", "hf0612": "#f59e0b", "motor_nema11": "#24292f", "servo_sg90": "#0969da",
       "ld2450_fork": "#ea580c", "ld2450_cradle": "#f97316", "ld2450_radar": "#1d4f38",
       "wall_mount": "#b45309", "ld2450_fork_screw": "#ea580c", "beam": "#c9a66b", "ceiling": "#e5e7eb",
       "bolt": "#57606a", "nut": "#374151", "screw": "#8a6d3b",
       "hinge_plate": "#b45309", "hinge_clip": "#d97706", "pin": "#57606a", "tie_bar": "#92400e", "strut": "#f59e0b",
       "fairlead_base": "#8b5cf6", "brace": "#6b7280", "line": "#111111", "bead": "#f59e0b", "electronics": "#16a34a"}
LABEL = {"bracket": "bracket.stl", "spool_ratchet": "spool_ratchet.stl", "spool_body": "spool_body.stl (the HF0612 presses into it)",
         "fairlead_body": "fairlead_body.stl", "fairlead_flap": "fairlead_flap.stl (hinged bumper)", "fairlead_flap_inv": "fairlead_flap_inv.stl (flap with the tab under the switch)",
         "switch_kw12": "KW12-3 limit switch", "finger": "finger.stl on the SG90 spline", "rod_6mm": "6 mm rod, 100 mm",
         "coupler": "5-to-6 mm coupler", "spacer_A": "spacer_A_6mm.stl", "spacer_B": "spacer_B_50mm.stl",
         "bearing_606": "606ZZ ball bearing", "hf0612": "HF0612 one-way bearing (clutch), pressed into spool_body", "motor_nema11": "NEMA 11 motor", "servo_sg90": "SG90 servo",
         "ld2450_fork": "ld2450_fork.stl (glued)", "ld2450_cradle": "ld2450_cradle.stl (tilts on one M3 bolt)", "ld2450_radar": "LD2450 radar",
         "wall_mount": "wall_mount.stl (shelf, wall plate, 2 braces)", "ld2450_fork_screw": "ld2450_fork_screw.stl (2x M3 through the base, no glue)",
         "beam": "porch beam (stand-in)", "ceiling": "porch ceiling (stand-in)",
         "bolt": "6x M3 x 10 to 12 bolt, from below", "nut": "6x M3 nut, tapped into the shelf's pockets", "screw": "4x #4 x 1 in wood screw",
         "hinge_plate": "hinge_plate.stl (4x #4 screws into the beam)", "hinge_clip": "hinge_clip.stl x2 (2x M3 each, on the pad)",
         "pin": "pins: 2x M3 x 25 (hinge), 4x M3 x 20 (struts), nuts", "tie_bar": "tie_bar.stl (2x M3 through the base's x 65 holes)",
         "strut": "strut.stl x2 (the 45 degree bar, pushed)",
         "fairlead_base": "fairlead_base.stl (under the base, 2x M3 from inside)", "brace": "2x steel corner brace, 6 in (owner drills the base)",
         "line": "6 lb line, out through a 7 mm hole in the base", "bead": "stop bead",
         "electronics": "room for the controller board on the pad, 52 x 75 x 30 (stand-in box)"}

def rview(m):
    # render world: X = x, Y = z (rod), Z = -y (floor is down, ceiling mount on top)
    mm = m.copy(); v = mm.vertices.copy(); mm.vertices = np.column_stack([v[:, 0], v[:, 2], -v[:, 1]]); return mm

def save(img, name, title, labels=(), keys=(), loc="upper right"):
    import matplotlib.patches as mp
    fig, ax = plt.subplots(figsize=(img.shape[1] / 100, img.shape[0] / 100 + 0.5))
    ax.imshow(img); ax.set_axis_off(); ax.set_title(title, fontsize=13)
    for lab in labels:
        x, y, t = lab[:3]
        if len(lab) == 5: ax.annotate(t, xy=lab[3:], xytext=(x, y), fontsize=10, bbox=dict(fc="white", ec="0.6", alpha=0.9), arrowprops=dict(arrowstyle="->", color="0.3"))   # label with a pointer to the part
        else: ax.text(x, y, t, fontsize=10, bbox=dict(fc="white", ec="0.6", alpha=0.9))
    if keys:
        ax.legend(handles=[mp.Patch(color=COL[k], label=LABEL[k]) for k in keys], loc=loc, fontsize=10, framealpha=0.95)
    fig.savefig(os.path.join(IMG, name), dpi=100, bbox_inches="tight"); plt.close(fig)

def lbl(proj, pt, dx, dy, text, arrow=False):
    x, y, _ = proj(np.array([pt])); return (x[0] + dx, y[0] + dy, text) + ((x[0], y[0]) if arrow else ())

def assembly_png():
    A = G.assembly()
    for view, (el, az) in {"assembly_iso.png": (-28, -55), "assembly_iso_top.png": (30, -125)}.items():
        img, proj = raster.render([(rview(m), COL[k]) for k, m in A.items()], elev=el, azim=az, W=1300, H=950)
        labels = [lbl(proj, (-25, 45, -76), 15, 25, "line exits down through the fairlead")] if view == "assembly_iso.png" else []
        save(img, view, "Mechanism A, Rev C.1 - installed, ceiling mount" + (" (view from below)" if view == "assembly_iso.png" else " (view from above, ceiling removed)"), labels, keys=list(A.keys()))

def exploded_png():
    A = G.assembly()
    # (dx, dy, dz) in assembly frame; +dy moves toward the floor
    off = {"bracket": (0, 0, 0), "servo_sg90": (0, 0, 0), "finger": (0, 0, 22),
           "motor_nema11": (0, 90, -95), "coupler": (0, 90, -45), "spacer_A": (0, 90, -8),
           "spool_ratchet": (0, 90, 20), "hf0612": (0, 90, 38), "spool_body": (0, 90, 55), "spacer_B": (0, 90, 95),
           "bearing_606": (0, 90, 150), "rod_6mm": (0, 150, 20),
           "fairlead_body": (-110, 40, -40), "fairlead_flap": (-110, 40, -40), "switch_kw12": (-110, 40, -40),
           "ld2450_fork": (40, 20, 20), "ld2450_cradle": (70, 60, 20), "ld2450_radar": (100, 75, 20)}
    items = []
    for k, m in A.items():
        mm = m.copy(); mm.apply_translation(off.get(k, (0, 0, 0))); items.append((rview(mm), COL[k]))
    img, proj = raster.render(items, elev=-12, azim=-30, W=1600, H=1050)
    labels = [lbl(proj, (0, 82, -(G.AXIS_Y + 90) - 5), 170, 120, "HF0612 one-way bearing (the clutch):\npresses into spool_body", True)]
    save(img, "exploded.png", "Exploded view. Rod order from motor: coupler, spacer A, ratchet disk, HF0612 one-way bearing in spool body, spacer B, 606ZZ", labels, keys=list(A.keys()))

def lock_png():
    fig, ax = plt.subplots(figsize=(10, 8))
    P = G.ratchet_poly(); xs, ys = P.exterior.xy
    ax.fill(np.array(xs), np.array(ys) + G.AXIS_Y, color="#1f6feb", alpha=0.25); ax.plot(np.array(xs), np.array(ys) + G.AXIS_Y, "#1f6feb")
    for w in G.spoke_window_polys(4.6):                                         # the disk's three through-windows (spoked, owner 2026-09-28)
        wx, wy = w.exterior.xy; ax.fill(np.array(wx), np.array(wy) + G.AXIS_Y, color="white", ec="#1f6feb", lw=1)
    ax.add_patch(plt.Circle((0, G.AXIS_Y), 25, fill=False, ls="--", color="#58a6ff"))
    ax.add_patch(plt.Circle((0, G.AXIS_Y), 3, color="#444"))
    ax.add_patch(plt.Rectangle((G.SERVO_SHAFT_X - 20.5, G.AXIS_Y - 3), 23.5, 6, color="#e5534b"))
    ax.add_patch(plt.Circle((G.SERVO_SHAFT_X, G.AXIS_Y), 5, color="#e5534b"))
    a = math.radians(60)
    tipx, tipy = G.SERVO_SHAFT_X - 20.5 * math.cos(a), G.AXIS_Y + 20.5 * math.sin(a)
    ax.plot([G.SERVO_SHAFT_X, tipx], [G.AXIS_Y, tipy], color="#e5534b", lw=6, alpha=0.3)
    ax.text(tipx - 4, tipy + 3, "RELEASED (servo 30)", color="#e5534b", fontsize=9)
    ax.text(45.5, G.AXIS_Y - 9, "LOCKED (servo 90)", color="#e5534b", fontsize=9)
    ax.add_patch(plt.Rectangle((36, 4), 8, 32, color="#9aa0a6"))
    ax.text(45, 10, "ledge: takes the\nlocking load", fontsize=9)
    ax.add_patch(plt.Rectangle((-90, 0), 170, 4, color="#9aa0a6")); ax.text(-88, -7, "base, y = 0 (ceiling)", fontsize=9)
    ax.add_patch(plt.Rectangle((43.8, 33.6), 23.4, 12.8, fill=False, ec="#0969da", lw=2)); ax.text(60, 48, "SG90", color="#0969da")
    ax.add_patch(plt.Rectangle((-36, 70), 17, 8, color="#8b5cf6")); ax.text(-70, 82, "fairlead (see doc 09)", color="#8b5cf6")
    ax.plot([-25, -25], [40, 115], color="k", lw=1.5); ax.text(-23, 105, "line to spider", fontsize=9)
    ax.annotate("", xy=(20, 65), xytext=(-20, 67), arrowprops=dict(arrowstyle="->", lw=2.5, color="green",
                connectionstyle="arc3,rad=-0.3"))
    ax.text(14, 78, "UNWIND (spider falling):\ncounterclockwise in this view", color="green", fontsize=10, ha="center", bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5))
    ax.annotate("tooth pushes finger\nUP onto the ledge", xy=(31, 37), xytext=(5, 12), fontsize=9,
                arrowprops=dict(arrowstyle="->"))
    ax.set_aspect("equal"); ax.invert_yaxis(); ax.set_xlim(-95, 85); ax.set_ylim(118, -12)
    ax.set_title("Lock detail: section through the ratchet disk, seen from behind the motor, ceiling install\n(every direction in the docs is seen from this side)")
    ax.grid(alpha=0.2)
    fig.savefig(os.path.join(IMG, "lock_detail.png"), dpi=120, bbox_inches="tight"); plt.close(fig)

def base_png():
    import fairlead as F
    b = G.bracket(); s = b.section(plane_origin=[0, 1.5, 0], plane_normal=[0, 1, 0])
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for d in s.discrete: ax.plot(d[:, 0], d[:, 2], "k")
    sg = F.fairlead_body().section(plane_origin=[0, 5, 0], plane_normal=[0, 1, 0])
    for d in sg.discrete: ax.fill(d[:, 0], d[:, 2], color="#8b5cf6", alpha=0.4)
    ax.add_patch(plt.Rectangle((-88, 18), 52, 75, fill=False, ls="--", ec="#2da44e"))
    ax.text(-86, 95, "electronics area 52 x 75 (board may overhang -x edge)", color="#2da44e", fontsize=9)
    for x, z in [(-80, 28), (-56, 28), (-80, 83), (-56, 83)]: ax.text(x + 2, z + 2, "PCB", fontsize=7, color="#2da44e")
    for z in (28, 83): ax.text(-31, z + 2, "fairlead", fontsize=7, color="#8b5cf6")
    for z in (20, 90): ax.text(67, z + 2, "mount", fontsize=7)
    ax.text(-10, 60, "window", fontsize=8)
    ax.set_aspect("equal"); ax.set_xlabel("x (mm)"); ax.set_ylabel("z (mm, along rod)")
    ax.set_title("Base, viewed from the room side (y=0 plane). Motor end at z=0, 606ZZ end at z=110")
    fig.savefig(os.path.join(IMG, "base_layout.png"), dpi=120, bbox_inches="tight"); plt.close(fig)

def steps_png():
    import matplotlib.colors as mc
    A = G.assembly()
    base = ["bracket"]
    fl = ("fairlead_body", "fairlead_flap", "switch_kw12")
    rd = ("ld2450_fork", "ld2450_cradle", "ld2450_radar")
    steps = [("Step 1: press 606ZZ into the end plate, motor onto the motor plate", base, ["bearing_606", "motor_nema11"]),
             ("Step 2: coupler onto the motor shaft (set screw on the 5 mm side)", base + ["bearing_606", "motor_nema11"], ["coupler"]),
             ("Step 3: hold spacer A, spool, spacer B in the gap, disk toward the motor", base + ["bearing_606", "motor_nema11", "coupler"], ["spacer_A", "spool_ratchet", "hf0612", "spool_body", "spacer_B"]),
             ("Step 4: push the rod in from the 606ZZ end, through everything, into the coupler", base + ["bearing_606", "motor_nema11", "coupler", "spacer_A", "spool_ratchet", "hf0612", "spool_body", "spacer_B"], ["rod_6mm"]),
             ("Step 5: SG90 into the tower, finger pressed onto its spline", [k for k in A if k not in ("servo_sg90", "finger") + fl + rd], ["servo_sg90", "finger"]),
             ("Step 6: fairlead with flap and limit switch, glued to the pad", [k for k in A if k not in fl + rd], list(fl)),
             ("Step 7: radar fork glued under the servo end, cradle on one M3 bolt, radar slid in", [k for k in A if k not in rd], list(rd))]
    for i, (title, old, new) in enumerate(steps, 1):
        items = [(rview(A[k]), tuple(0.55 + 0.45 * np.array(mc.to_rgb(COL[k])))) for k in old]
        items += [(rview(A[k]), COL[k]) for k in new]
        img, proj = raster.render(items, elev=-25, azim=-50, W=1000, H=720)
        save(img, f"step{i}.png", title + "   (new parts in full color)", (), keys=new)

def fairlead_png():
    import fairlead as F, matplotlib.colors as mc
    A = G.assembly()
    ghost = lambda k: tuple(0.6 + 0.4 * np.array(mc.to_rgb(COL[k])))
    bead = trimesh.creation.icosphere(radius=4, subdivisions=3)
    line = G.vcyl(0.3, 70, 40, F.LX, F.LZ)
    for name, deg, title in [("fairlead_rest.png", 0, "Fairlead + limit switch, spider away: flap resting, switch open"),
                             ("fairlead_home.png", -14.5, "Spider home: bead lifts the flap, tail presses the roller, flap hits the hard stop")]:
        flap = F.rotate_flap(A["fairlead_flap"], deg)
        b = bead.copy(); b.apply_translation([F.LX, F.HY + F.FT / 2 + 4 + (12 if deg == 0 else -3.3), F.LZ])
        items = [(rview(A[k]), ghost(k)) for k in ("bracket", "spool_ratchet", "spool_body")]
        items += [(rview(A["fairlead_body"]), COL["fairlead_body"]), (rview(flap), COL["fairlead_flap"]),
                  (rview(A["switch_kw12"]), COL["switch_kw12"]), (rview(b), "#f59e0b"), (rview(line), "#222222")]
        img, proj = raster.render(items, elev=-8, azim=-8, W=1200, H=900)
        save(img, name, title, (), keys=["fairlead_body", "fairlead_flap", "switch_kw12"])

def fairlead_exploded_png():
    """Fairlead sub-assembly: body, flap, M2 hinge bolt, KW12-3, 2x M2 screws, exploded along the pin axis (x)."""
    import fairlead as F
    import matplotlib.patches as mp
    body, flap, sw = F.fairlead_body(), F.fairlead_flap(), F.switch_model()
    pin = F.xcyl(0.875, -36, -6, F.PY, F.HZ); pin.apply_translation([-40, 0, 0])
    fl = flap.copy(); fl.apply_translation([25, 22, 0])
    s2 = sw.copy(); s2.apply_translation([45, 30, 0])
    screws = []
    for z in F.SW_HOLES_Z:
        sc = F.xcyl(1.0, -40, -28, F.SW_HOLE_Y, z); sc.apply_translation([-25, 0, 0]); screws.append(sc)
    items = [(rview(body), COL["fairlead_body"]), (rview(fl), COL["fairlead_flap"]), (rview(s2), COL["switch_kw12"]),
             (rview(pin), "#f59e0b")] + [(rview(sc), "#57606a") for sc in screws]
    img, proj = raster.render(items, elev=12, azim=215, W=1300, H=900)
    fig, ax = plt.subplots(figsize=(13, 9.6)); ax.imshow(img); ax.set_axis_off()
    ax.set_title("Fairlead sub-assembly (1 body, 1 flap): M2 hinge bolt in from the flap side, threads into the body,\nswitch on the plate's far side with 2x M2 through the slots, roller end toward the fairlead", fontsize=12)
    ax.legend(handles=[mp.Patch(color=COL["fairlead_body"], label="fairlead_body.stl (x1)"),
                       mp.Patch(color=COL["fairlead_flap"], label="fairlead_flap.stl (x1)"),
                       mp.Patch(color="#f59e0b", label="hinge pin: M2 bolt, 16 to 20 mm"),
                       mp.Patch(color=COL["switch_kw12"], label="KW12-3 roller switch"),
                       mp.Patch(color="#57606a", label="2x M2 x 12 screw + nut")], loc="lower left", fontsize=10)
    fig.savefig(os.path.join(IMG, "fairlead_exploded.png"), dpi=100, bbox_inches="tight"); plt.close(fig)

def inverted_png():
    """The owner's inverted install: device turned over on two 6 in corner braces standing up the beam, line out through the base."""
    import inverted as INV
    A = INV.assembly_inverted(); A.update(INV.line_and_bead())
    A.update({k: G.I(m, G.bx(-200, 250, -300, 200, -25, 135)) for k, m in INV.porch().items()})   # a short length of beam and ceiling, so the device reads
    key = lambda k: "brace" if k.startswith("brace") else k
    img, proj = raster.render([(INV.view_inv(m), COL[key(k)]) for k, m in A.items()], elev=-12, azim=-30, W=1300, H=1000)
    labels = [lbl(proj, (INV.LINE_X, -INV.LINE_Z, -110), 12, -60, f"line falls {INV.LINE_X - INV.X_BEAM:.0f} mm from the beam's face", True),
              lbl(proj, (INV.X_BEAM + 140, -INV.BRACE_Z[0], -2), 260, 60, "base sits on the braces' flat legs", True),
              lbl(proj, (INV.LINE_X + 10, -INV.LINE_Z, -30), 200, 60, "fairlead, flap and switch under the base", True),
              lbl(proj, (95, -62, -40), 120, 120, "radar under the servo end, looking at the approach", True)]
    save(img, "inverted_install.png", "Inverted install (the owner's plan): device turned over, sitting on two 6 in steel corner braces that stand up the beam, line out the bottom (view from below, inside the porch)",
         labels, keys=["bracket", "electronics", "fairlead_base", "fairlead_flap", "switch_kw12", "brace", "line", "bead", "ld2450_fork_screw", "ld2450_cradle", "ld2450_radar", "beam", "ceiling"], loc="upper right")

def inverted_fairlead_png(elev=-12, azim=35, name="inverted_fairlead.png"):
    """Close-up for the build guide: the fairlead block under the base, flap, switch, both block screws, line and bead."""
    import inverted as INV
    A = INV.assembly_inverted(); L = INV.line_and_bead(drop=45)
    base = G.I(A["bracket"], G.bx(0, 55, -60, 12, 10, 105))                  # just the base around the block
    screws = [G.U(G.vcyl(1.5, 12, -8.0, x, z), G.vcyl(2.75, 2.0, 4.0, x, z)) for x, z in INV.BLOCK_SCREWS]   # M3 x 12 from inside the base
    items = [(INV.view_inv(base), "#d0d3d6")]
    items += [(INV.view_inv(A[k]), COL[k]) for k in ("fairlead_base", "fairlead_flap", "switch_kw12")]
    items += [(INV.view_inv(m), "#57606a") for m in screws] + [(INV.view_inv(L["line"]), "#111111"), (INV.view_inv(L["bead"]), COL["bead"])]
    img, proj = raster.render(items, elev=elev, azim=azim, W=1300, H=1000)
    labels = [lbl(proj, (INV.LINE_X, -INV.LINE_Z, 25), 60, -40, "line: from the spool, down through the 7 mm hole, the block's bore, the flap's slot", True),
              lbl(proj, (INV.LINE_X, -INV.LINE_Z, -40), -420, -60, "bead: lifts the flap at home", True),
              lbl(proj, (43, -47, -15), 60, 20, "KW12-3 on the outer face, legs up; roller on the flap's tab", True),
              lbl(proj, (32, -83, -8), 80, -60, "M3 x 12 from inside the base (x2)", True)]
    save(img, name, "Inverted install, fairlead v2: switch above the flap, legs up, flap lowest (only the base is drawn above it)",
         labels, keys=["fairlead_base", "fairlead_flap_inv", "switch_kw12", "bead"], loc="lower left")

def rod_section_png(elev=8, azim=12):
    """Every part on the rod cut in half along the rod, so the HF0612 one-way bearing inside the spool shows (owner 2026-09-28)."""
    A = G.assembly()
    keys = ["bracket", "motor_nema11", "coupler", "rod_6mm", "spacer_A", "spool_ratchet", "hf0612", "spool_body", "spacer_B", "bearing_606"]
    items = []
    for k in keys:
        m = A[k]
        if k == "bracket": m = G.I(m, G.bx(-40, 40, 12, 80, -5, 110))
        if k == "coupler": m = G.D(m, A["rod_6mm"], G.cyl(2.5, 20, 0, 0, G.AXIS_Y))
        cut = trimesh.intersections.slice_mesh_plane(m, plane_normal=[-1, 0, 0], plane_origin=[0, 0, 0], cap=True)
        items.append((rview(cut), "#d6d9dc" if k == "bracket" else COL[k]))
    img, proj = raster.render(items, elev=elev, azim=azim, W=1700, H=900)
    Y = G.AXIS_Y
    P = lambda y, z: (0, z, -y)
    labels = [lbl(proj, P(Y + 10, -16), -40, 150, "NEMA 11 motor", True),
              lbl(proj, P(Y + 5.5, 22), -60, 190, "5-to-6 mm coupler", True),
              lbl(proj, P(Y + 4.5, 33), -20, 230, "spacer A", True),
              lbl(proj, P(Y + 28, 39), -40, 120, "ratchet disk (spool_ratchet)", True),
              lbl(proj, P(Y - 4, 44), 40, -330, "HF0612 ONE-WAY BEARING (the clutch)\npressed into spool_body, flush with its flange,\n2 mm stub into the ratchet disk", True),
              lbl(proj, P(Y + 20, 48), 60, 110, "spool_body (line winds on the 50 mm barrel)", True),
              lbl(proj, P(Y + 4.5, 75), 40, 170, "spacer B", True),
              lbl(proj, P(Y + 7, 103), 20, 120, "606ZZ ball bearing in the end plate", True),
              lbl(proj, P(Y, 112), -40, -120, "6 mm rod", True)]
    save(img, "rod_section.png", "Cut through the rod: every part on it, motor on the left, 606ZZ end on the right", labels)

def drive_direction_png():
    """Ratchet disk and finger seen from behind the motor (every direction in the docs is, owner 2026-09-28): which way the rod drives the spool through the HF0612, and which tooth face meets the finger (owner 2026-09-28)."""
    import matplotlib.patches as mp
    fig, ax = plt.subplots(figsize=(11, 9))
    S = lambda x, y: (np.asarray(x), -np.asarray(y))   # part frame to this view: seen from -z (behind the motor), floor side down
    # the spool body sits BEHIND the disk in this view: its flange (r 32) shows in the tooth gaps
    ax.add_patch(plt.Circle((0, 0), 32, color="#c9d6e6", ec="#7d8fa6", lw=1, ls="--"))
    ax.annotate("spool flange, behind the disk", xy=(-22, -24), xytext=(-100, -62), fontsize=9, color="#4b5d73", arrowprops=dict(arrowstyle="->", color="#4b5d73"))
    P = G.ratchet_poly(); xs, ys = S(*P.exterior.xy)
    ax.fill(xs, ys, color="#8fb6f7"); ax.plot(xs, ys, "#1f6feb", lw=1.5)
    for w in G.spoke_window_polys(4.6):   # the disk's three windows; the spool body's own windows sit right behind them (a little larger round the screws), so you see straight through both
        wx, wy = S(*w.exterior.xy); ax.fill(wx, wy, color="white", ec="#1f6feb", lw=1.2)
    ax.text(0, -16, "ratchet disk\n(nearest you)", fontsize=9, color="#0b3d91", ha="center", bbox=dict(fc="white", ec="#1f6feb", lw=0.6, alpha=0.9, pad=1.5))
    # side strip: where you stand and which way you look
    zx = lambda z: -95 + (z + 32) * 1.05; yc, k = 82, 0.33
    def bar(z0, z1, r, col, label=None, dy=0):
        ax.add_patch(plt.Rectangle((zx(z0), yc - r * k), zx(z1) - zx(z0), 2 * r * k, color=col, ec="#333", lw=0.6))
        if label: ax.text((zx(z0) + zx(z1)) / 2, yc + r * k + 1.5 + dy, label, fontsize=8, ha="center", va="bottom")
    ax.plot([zx(-32), zx(106)], [yc, yc], color="#444", lw=1.5)
    bar(-32, 0, 14, "#24292f", "motor"); bar(10, 30, 6, "#d4a72c", "coupler"); bar(30, 36, 6, "#2da44e")
    bar(36, 42, 33, "#8fb6f7", "ratchet disk"); bar(42, 48, 25, "#c9d6e6"); bar(48, 50, 32, "#c9d6e6"); ax.text(zx(46), yc - 32 * k - 1.5, "spool", fontsize=8, ha="center", va="top")
    bar(50, 100, 4.8, "#2da44e", "spacer B"); bar(100, 106, 8.5, "#57606a", "606ZZ")
    ax.annotate("", xy=(zx(-34), yc), xytext=(zx(-34) - 14, yc), arrowprops=dict(arrowstyle="-|>", lw=2.5, color="k"))
    ax.text(zx(-34) - 15, yc - 7, "you, behind the motor,\nlooking this way", fontsize=8, va="top")
    ax.text(zx(-32), yc + 20, "Side view: where this picture is seen from (motor and coupler left out of the big view)", fontsize=9, color="#333")
    # the three faces of one tooth, picked out: long face (ramp) and steep face
    def pol(r, deg): a = math.radians(deg); return S(r * math.cos(a), r * math.sin(a))
    ramp = np.array([pol(G.TOOTH_TIP_R + (G.TOOTH_ROOT_R - G.TOOTH_TIP_R) * k / 20, 150 + 27 * k / 20) for k in range(21)])
    ax.plot(ramp[:, 0], ramp[:, 1], color="#16a34a", lw=5, solid_capstyle="round")
    st = np.array([pol(G.TOOTH_ROOT_R, 180), pol(G.TOOTH_TIP_R, 180)])
    ax.plot(st[:, 0], st[:, 1], color="#dc2626", lw=5, solid_capstyle="round")
    x, y = pol(31, 163); ax.annotate("LONG CURVED FACE\n(the finger slides up it)", xy=(x, y), xytext=(-100, -30), fontsize=10, color="#16a34a", fontweight="bold", arrowprops=dict(arrowstyle="->", color="#16a34a"))
    x, y = pol(31, 180); ax.annotate("STEEP FACE\n(stops against the finger)", xy=(x, y), xytext=(-100, 22), fontsize=10, color="#dc2626", fontweight="bold", arrowprops=dict(arrowstyle="->", color="#dc2626"))
    # rod, one-way bearing, spool hub
    ax.add_patch(plt.Circle((0, 0), G.HF0612_OD / 2, color="#f59e0b")); ax.add_patch(plt.Circle((0, 0), 3, color="#444"))
    ax.annotate("rod inside the HF0612 one-way bearing (orange)", xy=(-3, 3), xytext=(-100, 50), fontsize=10, arrowprops=dict(arrowstyle="->"))
    # finger, locked, its tip against the steep face at part angle 0
    fx, fy = S(G.SERVO_SHAFT_X, 0); tx, _ = S(G.SERVO_SHAFT_X - 20.5, 0)
    ax.add_patch(plt.Rectangle((fx, fy - 3), tx - fx, 6, color="#e5534b")); ax.add_patch(plt.Circle((fx, fy), 5, color="#e5534b"))
    ax.text(fx - 2, fy + 7, "finger (locked)", color="#e5534b", fontsize=10, ha="center")
    # the two directions
    ax.add_patch(mp.FancyArrowPatch(pol(40, 285), pol(40, 335), connectionstyle="arc3,rad=-0.25", arrowstyle="-|>,head_width=6,head_length=10", lw=3, color="#16a34a"))
    ax.text(48, 58, "CLOCKWISE: the rod DRIVES the spool.\nWinding the spider up. The bearing locks,\nthe finger rides up each long face and clicks\noff the tip: no tooth cuts into the finger.", fontsize=10, color="#16a34a", va="top")
    ax.add_patch(mp.FancyArrowPatch(pol(40, 75), pol(40, 25), connectionstyle="arc3,rad=0.25", arrowstyle="-|>,head_width=6,head_length=10", lw=3, color="#dc2626"))
    ax.text(48, -40, "COUNTERCLOCKWISE: the way the spider's weight pulls.\nA steep face lands on the finger: that is the HOLD.\nOn the drop the finger is out and the motor turns\nthis way; the spool can lag it but never outrun it.", fontsize=10, color="#dc2626", va="top")
    ax.text(0, -78, "Hand check, spool on a spare rod, seen from behind the motor: hold the rod still.\nThe spool must spin FREE clockwise and LOCK counterclockwise. If it is the other way round, press the HF0612 out and flip it.\nSame in the ceiling and the inverted install.",
            fontsize=10, ha="center", va="top", bbox=dict(fc="#fff7ed", ec="#f59e0b"))
    ax.set_aspect("equal"); ax.set_xlim(-122, 130); ax.set_ylim(-98, 106); ax.set_axis_off()
    ax.set_title("Which way the rod drives the spool, seen from behind the motor (looking along the rod toward the spool)", fontsize=12)
    fig.savefig(os.path.join(IMG, "drive_direction.png"), dpi=110, bbox_inches="tight"); plt.close(fig)

if __name__ == "__main__":
    base_png(); lock_png(); assembly_png(); exploded_png(); steps_png(); rod_section_png(); drive_direction_png(); fairlead_png(); fairlead_exploded_png(); inverted_png()
    print("renders written to", os.path.abspath(IMG))
