"""Draws docs/img/wiring.png and docs/img/install.png. Run: python diagrams.py"""
import os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Polygon

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img"); os.makedirs(IMG, exist_ok=True)

def box(ax, x, y, w, h, title, pins, side="r", color="#f6f8fa"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15", fc=color, ec="#24292f", lw=1.5))
    ax.text(x + w / 2, y + h + 0.15, title, ha="center", va="bottom", fontsize=11, weight="bold")
    pos = {}
    for i, p in enumerate(pins):
        py = y + h - 0.45 - i * 0.5
        px = x + w if side == "r" else x
        ax.plot(px, py, "o", color="#24292f", ms=4)
        ax.text(px + (-0.12 if side == "r" else 0.12), py, p, ha="right" if side == "r" else "left", va="center", fontsize=9)
        pos[p] = (px, py)
    return pos

def wire(ax, a, b, color, label=None, mid=None):
    (x0, y0), (x1, y1) = a, b
    xm = mid if mid is not None else (x0 + x1) / 2
    ax.plot([x0, xm, xm, x1], [y0, y0, y1, y1], color=color, lw=2.2, solid_capstyle="round")
    if label: ax.text(xm + 0.06, (y0 + y1) / 2, label, fontsize=8, color=color, rotation=90, va="center")

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
    a1.set_ylim(0, 7.6); a2.set_ylim(-0.2, 7.0)
    a1.set_title("1. SIGNAL WIRING (thin jumper wires)", fontsize=14, weight="bold", loc="left")
    drv = pins_box(a1, 0.4, 7.0, 3.2, "Driver carrier + TMC2209", right=["STEP", "DIR", "EN", "GND"], color="#fff8c5")
    esp = pins_box(a1, 5.9, 7.0, 3.2, "ESP32-S NodeMCU (38-pin)", left=["GPIO25", "GPIO26", "GPIO27", "GND"],
                   right=["GPIO13", "GPIO33", "GPIO16 (RX2)", "GPIO17 (TX2)", "GPIO32"], color="#ddf4ff")
    srv = pins_box(a1, 11.4, 7.0, 3.2, "SG90 servo", left=["orange = signal"], color="#dafbe1")
    rad = pins_box(a1, 11.4, 5.5, 3.2, "LD2410C radar", left=["OUT", "TX  (optional)", "RX  (optional)"], color="#dafbe1")
    for p, q, c, l in [("STEP", "GPIO25", BLU, "step"), ("DIR", "GPIO26", BLU, "direction"), ("EN", "GPIO27", BLU, "enable"), ("GND", "GND", BLK, "ground")]:
        line(a1, drv[p], esp[q], c, l)
    line(a1, esp["GPIO13"], srv["orange = signal"], GRN, "servo signal")
    line(a1, esp["GPIO33"], rad["OUT"], PUR, "presence", mid=10.4)
    line(a1, esp["GPIO16 (RX2)"], rad["TX  (optional)"], GRY, "optional", mid=10.7)
    line(a1, esp["GPIO17 (TX2)"], rad["RX  (optional)"], GRY, None, mid=11.0)
    lim = pins_box(a1, 11.4, 2.95, 3.2, "Limit switch (3-pin)", left=["signal (NO)"], color="#dafbe1")
    line(a1, esp["GPIO32"], lim["signal (NO)"], PUR, "home", mid=10.1)
    mot = pins_box(a1, 0.4, 3.3, 3.2, "NEMA 11 motor, 4 wires", right=["black", "green", "red", "blue"], color="#eaeef2")
    ter = pins_box(a1, 5.9, 3.3, 3.2, "Carrier motor terminal", left=["1A", "1B", "2A", "2B"], color="#fff8c5")
    for p, q, c in [("black", "1A", BLK), ("green", "1B", GRN), ("red", "2A", RED), ("blue", "2B", BLU)]: line(a1, mot[p], ter[q], c)
    a1.text(9.3, 1.7, "Carrier setup before anything else:\n- DIP switches 1, 2, 3 all OFF (1/8 step)\n- TMC2209 pot set to Vref 0.85 V (= 0.6 A)\n  with the motor UNPLUGGED\n- Driver's EN pin lines up with carrier's EN\n- Motor buzzes but won't turn: swap black and green\n- Never unplug the motor with 12 V on",
            fontsize=10, va="top", bbox=dict(fc="#fff8c5", ec="0.6"))
    a1.text(9.5, 7.45, "BOOT button (GPIO0) = manual test drop.  Blue LED (GPIO2) blinks = armed.", fontsize=9.5, ha="center")

    a2.set_title("2. POWER WIRING (thicker wire for the 12 V run, 22 AWG is fine)", fontsize=14, weight="bold", loc="left")
    psu = pins_box(a2, 0.4, 6.3, 3.2, "12 V 2 A adapter + jack", right=["+12 V", "GND"], color="#ffebe9")
    drvp = pins_box(a2, 5.9, 6.3, 3.2, "Driver carrier power", left=["VMOT (+12 V)", "GND"], color="#fff8c5")
    buck = pins_box(a2, 5.9, 4.3, 3.2, "LM2596 buck (set 5.0 V first!)", left=["IN+", "IN-"], right=["OUT+", "OUT-"], color="#ffebe9")
    e5 = pins_box(a2, 11.4, 6.3, 3.2, "ESP32", left=["VIN", "GND"], color="#ddf4ff")
    s5 = pins_box(a2, 11.4, 4.6, 3.2, "SG90 servo", left=["red (5 V)", "brown (GND)"], color="#dafbe1")
    r5 = pins_box(a2, 11.4, 2.55, 3.2, "LD2410C", left=["VCC (5 V)", "GND"], color="#dafbe1")
    line(a2, psu["+12 V"], drvp["VMOT (+12 V)"], RED, "+12 V")
    line(a2, psu["GND"], drvp["GND"], BLK, "GND")
    line(a2, psu["+12 V"], buck["IN+"], RED, None, mid=4.4)
    line(a2, psu["GND"], buck["IN-"], BLK, None, mid=4.0)
    for dst, bx in [((e5["VIN"]), 10.0), ((s5["red (5 V)"]), 10.3), ((r5["VCC (5 V)"]), 10.6)]: line(a2, buck["OUT+"], dst, ORG, None, mid=bx)
    for dst, bx in [((e5["GND"]), 9.6), ((s5["brown (GND)"]), 9.8), ((r5["GND"]), 10.9)]: line(a2, buck["OUT-"], dst, BLK, None, mid=bx)
    a2.add_patch(Circle((11.0, 4.37), 0.16, fc="white", ec=ORG, lw=2))
    a2.text(7.3, 0.35, "470 uF 16 V capacitor across the servo red/brown at the servo end (stripe = GND).\nAll grounds tie together: adapter, carrier, buck, ESP32, servo, radar.\nUSB can stay plugged in for the serial console while 12 V is on.",
            fontsize=10, ha="center", bbox=dict(fc="white", ec="0.6"))
    fig.savefig(os.path.join(IMG, "wiring.png"), dpi=100, bbox_inches="tight"); plt.close(fig)

def install():
    IN = 25.4
    fig, ax = plt.subplots(figsize=(15, 10))
    ceil, head = 96 * IN, 80 * IN
    wall_x0, wall_x1 = 0, 120          # 4.75 in wall
    ax.add_patch(Rectangle((-2200, ceil), 4100, 60, color="#d0d7de")); ax.text(-2150, ceil + 20, "ceiling (96 in / 2440 mm shown)")
    ax.add_patch(Rectangle((wall_x0, head), wall_x1 - wall_x0, ceil - head, color="#d0d7de"))
    ax.add_patch(Rectangle((-2200, -40), 4100, 40, color="#d0d7de")); ax.text(-2150, -30, "floor", va="top")
    ax.plot([wall_x0, wall_x0], [0, head], "k:", lw=1); ax.plot([wall_x1, wall_x1], [0, head], "k:", lw=1)
    ax.text(15, head / 2, "door opening\n80 in (2030 mm)", rotation=90, va="center", fontsize=9)
    # device on ceiling
    dx = wall_x1 + 300
    ax.add_patch(Rectangle((dx - 90, ceil - 76), 180, 76, fc="#9aa0a6", ec="k")); ax.text(dx + 110, ceil - 45, "DropSpider on the ceiling, room side.\nLine 300 mm (12 in) past the wall face,\ncentered on the door width", fontsize=9, va="top")
    # spider positions
    top_sp = ceil - 76 - 20
    ax.plot([dx, dx], [ceil - 76, 1550 + 150], "k-", lw=1)
    ax.add_patch(Circle((dx, top_sp - 45), 45, fc="#444", alpha=0.35)); ax.text(dx - 70, top_sp - 150, "retracted", fontsize=9, ha="right")
    ax.add_patch(Circle((dx, 1550 + 50), 55, fc="#222")); ax.text(dx + 70, 1600, "hangs at 1550 mm (61 in) after the bounce", fontsize=9)
    ax.add_patch(Circle((dx, 1450 + 50), 55, fc="none", ec="#cf222e", ls="--")); ax.text(dx + 70, 1450, "lowest point mid-bounce ~1450 mm (57 in)", color="#cf222e", fontsize=9)
    # person
    px = -1400
    ax.add_patch(Circle((px, 1600), 110, fc="#fff", ec="k")); ax.plot([px, px], [1490, 850], "k", lw=3)
    ax.plot([px, px - 150], [850, 0], "k", lw=3); ax.plot([px, px + 150], [850, 0], "k", lw=3)
    ax.annotate("", xy=(px + 500, 900), xytext=(px + 150, 900), arrowprops=dict(arrowstyle="->", lw=2))
    ax.text(px - 250, 1780, "approaching, about 1.2 m/s", fontsize=9)
    # sightline
    eye = (px + 60, 1600)
    ax.plot([eye[0], wall_x1 + 700], [eye[1], eye[1] + (head - eye[1]) * (wall_x1 + 700 - eye[0]) / (wall_x1 - eye[0])], color="#bc4c00", ls="--", lw=1)
    ax.text(-2150, 2330, "sight line under the door head: the retracted spider stays\nabove it until the person is about 0.6 m from the wall", color="#bc4c00", fontsize=9)
    # sensor
    ax.add_patch(Rectangle((wall_x0 - 30, head - 25), 30, 25, color="#1a7f37"))
    ax.text(-2150, 1150, "LD2410C at top of the opening, hallway side,\naimed down 45 deg toward the approach.\nMax moving gate 2 = triggers at 0.75 to 1.5 m", color="#1a7f37", fontsize=9)
    ax.plot([wall_x0 - 15, -1300], [head - 12, head - 1300], color="#1a7f37", lw=1, alpha=0.6)
    ax.plot([wall_x0 - 15, -500], [head - 12, head - 1600], color="#1a7f37", lw=1, alpha=0.6)
    # dims
    ax.annotate("", xy=(dx + 600, ceil - 96), xytext=(dx + 600, 1650), arrowprops=dict(arrowstyle="<->"))
    ax.text(dx + 620, (ceil + 1650) / 2, "drop ~ 700 mm (28 in)\n= line out below eyelet", fontsize=9)
    ax.set_xlim(-2200, 1900); ax.set_ylim(-60, ceil + 100); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Installation, side section through the doorway (8 ft ceiling, 6 ft 8 in door)", fontsize=13)
    fig.savefig(os.path.join(IMG, "install.png"), dpi=110, bbox_inches="tight"); plt.close(fig)

if __name__ == "__main__":
    wiring(); install(); print("wrote", IMG)
