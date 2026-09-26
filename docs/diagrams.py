"""Draws docs/img/wiring.png and docs/img/install.png. Run: python diagrams.py"""
import os, math, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img"); os.makedirs(IMG, exist_ok=True)

def pins_box(ax, x, y, w, title, left=(), right=(), color="#f6f8fa", step=0.55):
    n = max(len(left), len(right)); h = 0.5 + n * step
    ax.add_patch(FancyBboxPatch((x, y - h), w, h, boxstyle="round,pad=0.02,rounding_size=0.15", fc=color, ec="#24292f", lw=1.5))
    ax.text(x + w / 2, y + 0.12, title, ha="center", va="bottom", fontsize=11, weight="bold")
    pos = {}
    for i, p in enumerate(left):
        py = y - 0.5 - i * step; ax.plot(x, py, "o", color="#24292f", ms=4); ax.text(x + 0.12, py, p, va="center", fontsize=9.5); pos[p] = (x, py)
    for i, p in enumerate(right):
        py = y - 0.5 - i * step; ax.plot(x + w, py, "o", color="#24292f", ms=4); ax.text(x + w - 0.12, py, p, va="center", ha="right", fontsize=9.5); pos[p] = (x + w, py)
    return pos

def line(ax, a, b, color, label=None, mid=None, lw=2.4):
    (x0, y0), (x1, y1) = a, b
    if abs(y0 - y1) < 1e-6: ax.plot([x0, x1], [y0, y1], color=color, lw=lw)
    else:
        xm = mid if mid is not None else (x0 + x1) / 2
        ax.plot([x0, xm, xm, x1], [y0, y0, y1, y1], color=color, lw=lw)
    if label: ax.text((x0 + x1) / 2, y0 + 0.08, label, ha="center", va="bottom", fontsize=8.5, color=color)

RED, BLK, BLU, GRN, ORG, PUR, GRY = "#cf222e", "#24292f", "#0969da", "#1a7f37", "#bc4c00", "#8250df", "#6e7781"

def wiring():
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(15, 15), gridspec_kw={"height_ratios": [1.05, 1]})
    for a in (a1, a2): a.set_xlim(0, 15); a.axis("off")
    a1.set_ylim(-1.4, 8.2); a2.set_ylim(-0.2, 7.0)
    a1.set_title("1. SIGNAL WIRING (thin jumper wires)", fontsize=14, weight="bold", loc="left")
    drv = pins_box(a1, 0.4, 7.0, 3.2, "Expansion board + TMC2209", right=["STEP", "DIR", "EN", "GND"], color="#fff8c5")
    esp = pins_box(a1, 5.9, 7.0, 3.2, "ESP32 DevKit V1 (30-pin)", left=["GPIO25", "GPIO26", "GPIO27", "GND"],
                   right=["GPIO13", "GPIO16 (RX2)", "GPIO17 (TX2)", "GPIO32", "GND ", "GPIO33"], color="#ddf4ff")
    srv = pins_box(a1, 11.4, 7.4, 3.2, "SG90 servo", left=["orange = signal"], color="#dafbe1")
    rad = pins_box(a1, 11.4, 5.85, 3.2, "LD2450 radar (primary)", left=["TX", "RX"], color="#dafbe1")
    lim = pins_box(a1, 11.4, 3.85, 3.2, "KW12-3 limit switch", left=["NO", "COM"], color="#dafbe1")
    old = pins_box(a1, 11.4, 1.85, 3.2, "LD2410C (fallback, optional)", left=["OUT"], color="#eaeef2")
    for p, q, c, l in [("STEP", "GPIO25", BLU, "step"), ("DIR", "GPIO26", BLU, "direction"), ("EN", "GPIO27", BLU, "enable"), ("GND", "GND", BLK, "ground")]:
        line(a1, drv[p], esp[q], c, l)
    line(a1, esp["GPIO13"], srv["orange = signal"], GRN, "servo signal", mid=10.2)
    line(a1, esp["GPIO16 (RX2)"], rad["TX"], PUR, "radar data", mid=10.5)
    line(a1, esp["GPIO17 (TX2)"], rad["RX"], PUR, None, mid=10.8)
    line(a1, esp["GPIO32"], lim["NO"], ORG, "home switch", mid=10.35)
    line(a1, esp["GND "], lim["COM"], BLK, None, mid=10.65)
    line(a1, esp["GPIO33"], old["OUT"], GRY, "fallback", mid=10.95)
    mot = pins_box(a1, 0.4, 2.4, 3.2, "NEMA 11 motor, 4 wires", right=["black", "green", "red", "blue"], color="#eaeef2")
    ter = pins_box(a1, 5.9, 2.4, 3.2, "Expansion board motor terminal", left=["1A", "1B", "2A", "2B"], color="#fff8c5")
    for p, q, c in [("black", "1A", BLK), ("green", "1B", GRN), ("red", "2A", RED), ("blue", "2B", BLU)]: line(a1, mot[p], ter[q], c)
    a1.text(0.4, -1.35, "Expansion board setup before anything else:\nDIP switches 1, 2, 3 all OFF (1/8 step).  TMC2209 pot to Vref 0.85 V (= 0.6 A) with the motor UNPLUGGED.\nDriver's EN pin on the expansion board's EN.  Motor buzzes but won't turn: swap black and green.  Never unplug the motor with 12 V on.",
            fontsize=10, va="bottom", bbox=dict(fc="#fff8c5", ec="0.6"))
    a1.text(7.5, 7.75, "Same GPIO numbers on the 38-pin NodeMCU-32S. BOOT button (GPIO0) = manual test drop. KW12-3 NC leg unused.", fontsize=9.5, ha="center")

    a2.set_title("2. POWER WIRING (thicker wire for the 12 V run, 22 AWG is fine)", fontsize=14, weight="bold", loc="left")
    psu = pins_box(a2, 0.4, 6.3, 3.2, "12 V 2 A adapter + jack", right=["+12 V", "GND"], color="#ffebe9")
    drvp = pins_box(a2, 5.9, 6.3, 3.2, "Expansion board power", left=["VMOT (+12 V)", "GND"], color="#fff8c5")
    buck = pins_box(a2, 5.9, 4.3, 3.2, "MP1584EN buck, fixed 5 V (meter it first!)", left=["IN+", "IN-"], right=["OUT+", "OUT-"], color="#ffebe9")
    e5 = pins_box(a2, 11.4, 6.3, 3.2, "ESP32", left=["VIN", "GND"], color="#ddf4ff")
    s5 = pins_box(a2, 11.4, 4.6, 3.2, "SG90 servo", left=["red (5 V)", "brown (GND)"], color="#dafbe1")
    r5 = pins_box(a2, 11.4, 2.55, 3.2, "LD2450 (and LD2410C if fitted)", left=["VCC (5 V)", "GND"], color="#dafbe1")
    line(a2, psu["+12 V"], drvp["VMOT (+12 V)"], RED, "+12 V")
    line(a2, psu["GND"], drvp["GND"], BLK, "GND")
    line(a2, psu["+12 V"], buck["IN+"], RED, None, mid=4.4)
    line(a2, psu["GND"], buck["IN-"], BLK, None, mid=4.0)
    for dst, bx in [((e5["VIN"]), 10.0), ((s5["red (5 V)"]), 10.3), ((r5["VCC (5 V)"]), 10.6)]: line(a2, buck["OUT+"], dst, ORG, None, mid=bx)
    for dst, bx in [((e5["GND"]), 9.6), ((s5["brown (GND)"]), 9.8), ((r5["GND"]), 10.9)]: line(a2, buck["OUT-"], dst, BLK, None, mid=bx)
    a2.add_patch(Circle((11.0, 4.37), 0.16, fc="white", ec=ORG, lw=2, ls="--"))
    a2.text(7.3, 0.35, "Dashed circle: 470 uF capacitor at the servo, ONLY if the ESP32 restarts when the finger moves.\nAll grounds tie together: adapter, expansion board, buck, ESP32, servo, radar, switch COM.\nUSB can stay plugged in for the serial console while 12 V is on.",
            fontsize=10, ha="center", bbox=dict(fc="white", ec="0.6"))
    fig.savefig(os.path.join(IMG, "wiring.png"), dpi=100, bbox_inches="tight"); plt.close(fig)

def install():
    IN = 25.4
    fig, ax = plt.subplots(figsize=(15, 10))
    # Porch, measured by the owner 2026-09-26: ceiling 8 ft, front beam hangs 10 in, device 12 in behind it.
    ceil, beam_d = 96 * IN, 10 * IN
    head = ceil - beam_d
    wall_x0, wall_x1 = 0, 140          # front beam, 140 mm thick (assumed)
    ax.add_patch(Rectangle((wall_x0, ceil), 2700 - wall_x0, 60, color="#d0d7de")); ax.text(wall_x1 + 900, ceil + 20, "porch ceiling (96 in / 2440 mm)")
    ax.add_patch(Rectangle((wall_x0, head), wall_x1 - wall_x0, ceil - head, color="#b9a58a"))
    ax.text(wall_x0 - 30, head + 20, "front beam,\nhangs 10 in\n(254 mm)", fontsize=8.5, va="bottom", ha="right")
    ax.add_patch(Rectangle((-2200, -40), 4900, 40, color="#d0d7de")); ax.text(-2150, -30, "ground", va="top")
    ax.text(-2150, ceil - 60, "outside, open sky", fontsize=9, color="#57606a")
    # device on the porch ceiling
    dx = wall_x1 + 12 * IN
    ax.add_patch(Rectangle((dx - 90, ceil - 112), 180, 112, fc="#9aa0a6", ec="k")); ax.text(dx + 110, ceil - 45, "DropSpider on the porch ceiling.\nSpider line 12 in (305 mm) behind the beam,\nradar end toward the beam", fontsize=9, va="top")
    # spider positions
    top_sp = ceil - 115
    ax.plot([dx, dx], [ceil - 112, 1550 + 150], "k-", lw=1)
    ax.add_patch(Circle((dx, top_sp - 45), 45, fc="#444", alpha=0.35)); ax.text(dx - 70, top_sp - 150, "retracted", fontsize=9, ha="right")
    ax.add_patch(Circle((dx, 1550 + 50), 55, fc="#222")); ax.text(dx + 70, 1600, "stops at 1550 mm (61 in); the motor sets this height", fontsize=9)
    ax.add_patch(Circle((dx, 1450 + 50), 55, fc="none", ec="#cf222e", ls="--")); ax.text(dx + 70, 1450, "only if the motor loses grip: line stretch catches ~1450 mm (57 in)", color="#cf222e", fontsize=9)
    # person walks in from outside, toward the porch (ruled by the owner 2026-09-26)
    px = -1500
    ax.add_patch(Circle((px, 1600), 110, fc="#fff", ec="k")); ax.plot([px, px], [1490, 850], "k", lw=3)
    ax.plot([px, px - 150], [850, 0], "k", lw=3); ax.plot([px, px + 150], [850, 0], "k", lw=3)
    ax.annotate("", xy=(px + 500, 900), xytext=(px + 150, 900), arrowprops=dict(arrowstyle="->", lw=2))
    ax.text(px - 250, 1780, "walking in, about 1.2 m/s", fontsize=9)
    # sight line under the beam: the retracted spider stays above it
    eye = (px + 60, 1600)
    ex = dx + 200
    ax.plot([eye[0], ex], [eye[1], eye[1] + (head - eye[1]) * (ex - eye[0]) / (wall_x0 - eye[0])], color="#bc4c00", ls="--", lw=1)
    ax.text(-2150, 2150, "sight line under the beam: the retracted spider\nstays hidden above it until the person is close", color="#bc4c00", fontsize=9)
    # radar on the device's servo end, facing out under the beam, tilted 40 degrees down
    sx, sy = dx - 95, ceil - 46
    ax.add_patch(Rectangle((sx - 6, sy - 22), 12, 44, color="#1a7f37"))
    lim = math.degrees(math.atan2(sy - head, sx - wall_x1))    # steepest ray the beam still blocks
    for ang, style in ((lim, "-"), (75, "-")):
        L = (sy - 0) / math.sin(math.radians(ang))
        ax.plot([sx, sx - L * math.cos(math.radians(ang))], [sy, sy - L * math.sin(math.radians(ang))], color="#1a7f37", lw=1.2, ls=style, alpha=0.8)
    ax.text(900, 1150, f"Green: LD2450 on the device, facing out under the beam.\nThe beam blocks rays shallower than {lim:.0f} degrees down, so the\nradar sees a walker's legs from about 1.7 m out and their\nchest from about 0.8 m out. Tilt it 50 degrees down: the\nstrongest middle of its beam then passes under the beam.", color="#1a7f37", fontsize=9)
    # dims
    ax.annotate("", xy=(dx + 600, ceil - 130), xytext=(dx + 600, 1650), arrowprops=dict(arrowstyle="<->"))
    ax.text(dx + 620, (ceil + 1650) / 2, "drop ~ 700 mm (28 in)", fontsize=9)
    ax.set_xlim(-2200, 2700); ax.set_ylim(-60, ceil + 100); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Installation under the porch, side section (8 ft ceiling, beam hangs 10 in, device 12 in behind it)", fontsize=13)
    fig.savefig(os.path.join(IMG, "install.png"), dpi=110, bbox_inches="tight"); plt.close(fig)

if __name__ == "__main__":
    wiring(); install(); print("wrote", IMG)
