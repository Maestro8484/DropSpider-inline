"""Renders assembly images into ../docs/img. Run after generate.py: python render.py"""
import os, math, numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import generate as G
import raster

IMG = os.path.join(G.HERE, "..", "docs", "img"); os.makedirs(IMG, exist_ok=True)
COL = {"bracket": "#9aa0a6", "spool_ratchet": "#1f6feb", "spool_body": "#58a6ff",
       "fairlead_body": "#8b5cf6", "fairlead_flap": "#d946ef", "switch_kw12": "#111111",
       "finger": "#e5534b", "rod_6mm": "#444", "coupler": "#d4a72c", "spacer_A": "#2da44e", "spacer_B": "#2da44e",
       "bearing_606": "#57606a", "motor_nema11": "#24292f", "servo_sg90": "#0969da",
       "ld2450_holder": "#f97316", "ld2450_radar": "#1d4f38"}
LABEL = {"bracket": "bracket.stl", "spool_ratchet": "spool_ratchet.stl", "spool_body": "spool_body.stl + HF0612",
         "fairlead_body": "fairlead_body.stl", "fairlead_flap": "fairlead_flap.stl (hinged bumper)",
         "switch_kw12": "KW12-3 limit switch", "finger": "finger.stl on SG90 horn", "rod_6mm": "6 mm rod, 100 mm",
         "coupler": "5-to-6 mm coupler", "spacer_A": "spacer_A_6mm.stl", "spacer_B": "spacer_B_50mm.stl",
         "bearing_606": "606ZZ", "motor_nema11": "NEMA 11 motor", "servo_sg90": "SG90 servo",
         "ld2450_holder": "ld2450_holder.stl", "ld2450_radar": "LD2450 radar"}

def rview(m):
    # render world: X = x, Y = z (rod), Z = -y (floor is down, ceiling mount on top)
    mm = m.copy(); v = mm.vertices.copy(); mm.vertices = np.column_stack([v[:, 0], v[:, 2], -v[:, 1]]); return mm

def save(img, name, title, labels=(), keys=()):
    import matplotlib.patches as mp
    fig, ax = plt.subplots(figsize=(img.shape[1] / 100, img.shape[0] / 100 + 0.5))
    ax.imshow(img); ax.set_axis_off(); ax.set_title(title, fontsize=13)
    for (x, y, t) in labels: ax.text(x, y, t, fontsize=10, bbox=dict(fc="white", ec="0.6", alpha=0.9))
    if keys:
        ax.legend(handles=[mp.Patch(color=COL[k], label=LABEL[k]) for k in keys], loc="upper right", fontsize=10, framealpha=0.95)
    fig.savefig(os.path.join(IMG, name), dpi=100, bbox_inches="tight"); plt.close(fig)

def lbl(proj, pt, dx, dy, text):
    x, y, _ = proj(np.array([pt])); return (x[0] + dx, y[0] + dy, text)

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
           "spool_ratchet": (0, 90, 20), "spool_body": (0, 90, 55), "spacer_B": (0, 90, 95),
           "bearing_606": (0, 90, 150), "rod_6mm": (0, 150, 20),
           "fairlead_body": (-110, 40, -40), "fairlead_flap": (-110, 40, -40), "switch_kw12": (-110, 40, -40),
           "ld2450_holder": (60, 60, 20), "ld2450_radar": (95, 75, 20)}
    items = []
    for k, m in A.items():
        mm = m.copy(); mm.apply_translation(off.get(k, (0, 0, 0))); items.append((rview(mm), COL[k]))
    img, proj = raster.render(items, elev=-12, azim=-30, W=1600, H=1050)
    save(img, "exploded.png", "Exploded view. Rod order from motor: coupler, spacer A, ratchet disk, spool body, spacer B, 606ZZ", (), keys=list(A.keys()))

def lock_png():
    fig, ax = plt.subplots(figsize=(10, 8))
    P = G.ratchet_poly(); xs, ys = P.exterior.xy
    ax.fill(np.array(xs), np.array(ys) + G.AXIS_Y, color="#1f6feb", alpha=0.25); ax.plot(np.array(xs), np.array(ys) + G.AXIS_Y, "#1f6feb")
    ax.add_patch(plt.Circle((0, G.AXIS_Y), 25, fill=False, ls="--", color="#58a6ff"))
    ax.add_patch(plt.Circle((0, G.AXIS_Y), 3, color="#444"))
    ax.add_patch(plt.Rectangle((G.SERVO_SHAFT_X - 20.5, G.AXIS_Y - 3), 23.5, 6, color="#e5534b"))
    ax.add_patch(plt.Circle((G.SERVO_SHAFT_X, G.AXIS_Y), 5, color="#e5534b"))
    a = math.radians(60)
    tipx, tipy = G.SERVO_SHAFT_X - 20.5 * math.cos(a), G.AXIS_Y + 20.5 * math.sin(a)
    ax.plot([G.SERVO_SHAFT_X, tipx], [G.AXIS_Y, tipy], color="#e5534b", lw=6, alpha=0.3)
    ax.text(tipx - 4, tipy + 3, "RELEASED (servo 30)", color="#e5534b", fontsize=9)
    ax.text(G.SERVO_SHAFT_X - 18, G.AXIS_Y + 5, "LOCKED (servo 90)", color="#e5534b", fontsize=9)
    ax.add_patch(plt.Rectangle((36, 4), 8, 32, color="#9aa0a6"))
    ax.text(45, 10, "ledge: takes the\nlocking load", fontsize=9)
    ax.add_patch(plt.Rectangle((-90, 0), 170, 4, color="#9aa0a6")); ax.text(-88, -7, "base, y = 0 (ceiling)", fontsize=9)
    ax.add_patch(plt.Rectangle((43.8, 33.6), 23.4, 12.8, fill=False, ec="#0969da", lw=2)); ax.text(60, 48, "SG90", color="#0969da")
    ax.add_patch(plt.Rectangle((-36, 70), 17, 8, color="#8b5cf6")); ax.text(-70, 82, "fairlead (see doc 09)", color="#8b5cf6")
    ax.plot([-25, -25], [40, 115], color="k", lw=1.5); ax.text(-23, 105, "line to spider", fontsize=9)
    ax.annotate("", xy=(20, 65), xytext=(-20, 67), arrowprops=dict(arrowstyle="->", lw=2.5, color="green",
                connectionstyle="arc3,rad=-0.3"))
    ax.text(-8, 72, "UNWIND (spider falling):\ncounterclockwise in this view", color="green", fontsize=10, ha="center")
    ax.annotate("tooth pushes finger\nUP onto the ledge", xy=(31, 37), xytext=(5, 12), fontsize=9,
                arrowprops=dict(arrowstyle="->"))
    ax.set_aspect("equal"); ax.invert_yaxis(); ax.set_xlim(-95, 85); ax.set_ylim(118, -12)
    ax.set_title("Lock detail: section through the ratchet disk, viewed from the MOTOR end, installed on a ceiling\n(same thing seen from the 606ZZ end is CLOCKWISE)")
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
    rd = ("ld2450_holder", "ld2450_radar")
    steps = [("Step 1: press 606ZZ into the end plate, motor onto the motor plate", base, ["bearing_606", "motor_nema11"]),
             ("Step 2: coupler onto the motor shaft (set screw on the 5 mm side)", base + ["bearing_606", "motor_nema11"], ["coupler"]),
             ("Step 3: hold spacer A, spool, spacer B in the gap, disk toward the motor", base + ["bearing_606", "motor_nema11", "coupler"], ["spacer_A", "spool_ratchet", "spool_body", "spacer_B"]),
             ("Step 4: push the rod in from the 606ZZ end, through everything, into the coupler", base + ["bearing_606", "motor_nema11", "coupler", "spacer_A", "spool_ratchet", "spool_body", "spacer_B"], ["rod_6mm"]),
             ("Step 5: SG90 into the tower, finger on its horn", [k for k in A if k not in ("servo_sg90", "finger") + fl + rd], ["servo_sg90", "finger"]),
             ("Step 6: fairlead with flap and limit switch, glued to the pad", [k for k in A if k not in fl + rd], list(fl)),
             ("Step 7: LD2450 holder glued under the servo end, radar slid up into it", [k for k in A if k not in rd], list(rd))]
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
    """Fairlead sub-assembly: body, flap, filament pin, KW12-3, 2x M2 screws, exploded along the pin axis (x)."""
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
    ax.set_title("Fairlead sub-assembly (1 body, 1 flap): pin in from the flat outer face, flap on the pin,\nswitch on the plate's far side with 2x M2 through the slots, roller end toward the fairlead", fontsize=12)
    ax.legend(handles=[mp.Patch(color=COL["fairlead_body"], label="fairlead_body.stl (x1)"),
                       mp.Patch(color=COL["fairlead_flap"], label="fairlead_flap.stl (x1)"),
                       mp.Patch(color="#f59e0b", label="hinge pin: 30 mm of 1.75 mm filament"),
                       mp.Patch(color=COL["switch_kw12"], label="KW12-3 roller switch"),
                       mp.Patch(color="#57606a", label="2x M2 x 12 screw + nut")], loc="lower left", fontsize=10)
    fig.savefig(os.path.join(IMG, "fairlead_exploded.png"), dpi=100, bbox_inches="tight"); plt.close(fig)

if __name__ == "__main__":
    base_png(); lock_png(); assembly_png(); exploded_png(); steps_png(); fairlead_png(); fairlead_exploded_png()
    print("renders written to", os.path.abspath(IMG))
