"""Illustrations with simple drawn icons for slides 1 and 2 (PNG).
Run from Project_3/: .venv/bin/python slides_assets/make_visuals.py"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Arc, Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OURS, INK, INK2, SURF, LINE = "#2a78d6", "#0b0b0b", "#52514e", "#fcfcfb", "#d9d7d1"
CUST = "#eef0f3"
BAD, BAD_BG, GOOD, GOOD_BG = "#c4302f", "#fdecec", "#1f7a3a", "#e8f5ec"
GREY = "#8e8c85"
plt.rcParams.update({"font.family": "DejaVu Sans", "figure.facecolor": SURF})


def box(ax, x, y, w, h, fc, ec=LINE, r=0.25, lw=1.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw))


def rbox(ax, x, y, w, h, fc, ec="none", r=0.08, lw=0, z=5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw,
                                zorder=z))


# ---------------------------------------------------------------- icons (centre cx, cy; size s = height)
def icon_person(ax, cx, cy, s, c):
    ax.add_patch(Circle((cx, cy + 0.22 * s), 0.2 * s, color=c, zorder=5))
    ax.add_patch(FancyBboxPatch((cx - 0.33 * s, cy - 0.5 * s), 0.66 * s, 0.5 * s,
                                boxstyle=f"round,pad=0,rounding_size={0.25 * s}", fc=c, ec="none", zorder=5))


def icon_robot(ax, cx, cy, s, c):
    rbox(ax, cx - 0.4 * s, cy - 0.35 * s, 0.8 * s, 0.62 * s, c, r=0.14 * s)
    for dx in (-0.16, 0.16):
        ax.add_patch(Circle((cx + dx * s, cy - 0.05 * s), 0.08 * s, color="white", zorder=6))
    ax.plot([cx, cx], [cy + 0.27 * s, cy + 0.45 * s], color=c, lw=2.5 * s, zorder=5, solid_capstyle="round")
    ax.add_patch(Circle((cx, cy + 0.48 * s), 0.07 * s, color=c, zorder=5))
    ax.plot([cx - 0.14 * s, cx + 0.14 * s], [cy - 0.22 * s, cy - 0.22 * s], color="white", lw=2 * s, zorder=6,
            solid_capstyle="round")


def icon_shield(ax, cx, cy, s, c, mark):
    w, h = 0.8 * s, s
    pts = [(cx - w / 2, cy + h * 0.38), (cx, cy + h * 0.5), (cx + w / 2, cy + h * 0.38), (cx + w / 2, cy - h * 0.02),
           (cx, cy - h * 0.5), (cx - w / 2, cy - h * 0.02)]
    ax.add_patch(Polygon(pts, closed=True, fc=c, ec="none", zorder=5))
    if mark == "check":
        ax.plot([cx - 0.17 * s, cx - 0.04 * s, cx + 0.2 * s], [cy + 0.0 * s, cy - 0.14 * s, cy + 0.16 * s],
                color="white", lw=4.5 * s, zorder=6, solid_capstyle="round", solid_joinstyle="round")
    else:
        for a, b in (((-0.15, 0.15), (0.15, -0.15)), ((-0.15, -0.15), (0.15, 0.15))):
            ax.plot([cx + a[0] * s, cx + b[0] * s], [cy + a[1] * s, cy + b[1] * s], color="white", lw=4.5 * s,
                    zorder=6, solid_capstyle="round")


def icon_car(ax, cx, cy, s, c):
    rbox(ax, cx - 0.62 * s, cy - 0.18 * s, 1.24 * s, 0.38 * s, c, r=0.1 * s)
    ax.add_patch(Polygon([(cx - 0.36 * s, cy + 0.18 * s), (cx - 0.2 * s, cy + 0.44 * s), (cx + 0.24 * s, cy + 0.44 * s),
                          (cx + 0.42 * s, cy + 0.18 * s)], closed=True, fc=c, ec="none", zorder=5))
    ax.add_patch(Polygon([(cx - 0.27 * s, cy + 0.2 * s), (cx - 0.16 * s, cy + 0.37 * s), (cx + 0.2 * s, cy + 0.37 * s),
                          (cx + 0.32 * s, cy + 0.2 * s)], closed=True, fc="white", ec="none", zorder=6))
    for dx in (-0.36, 0.36):
        ax.add_patch(Circle((cx + dx * s, cy - 0.2 * s), 0.15 * s, color=INK, zorder=7))
        ax.add_patch(Circle((cx + dx * s, cy - 0.2 * s), 0.06 * s, color="white", zorder=8))


def icon_doc(ax, cx, cy, s, c):
    rbox(ax, cx - 0.33 * s, cy - 0.45 * s, 0.66 * s, 0.9 * s, "white", ec=c, r=0.06 * s, lw=2.2)
    for i, w in enumerate((0.42, 0.42, 0.42, 0.26)):
        y = cy + 0.25 * s - i * 0.17 * s
        ax.plot([cx - 0.2 * s, cx - 0.2 * s + w * s], [y, y], color=c, lw=2.2, zorder=6, solid_capstyle="round")


def icon_list(ax, cx, cy, s, c):
    for i in range(3):
        y = cy + 0.28 * s - i * 0.28 * s
        ax.add_patch(Circle((cx - 0.3 * s, y), 0.07 * s, color=c, zorder=6))
        ax.plot([cx - 0.15 * s, cx + 0.35 * s], [y, y], color=c, lw=2.6, zorder=6, solid_capstyle="round")


def icon_magnifier(ax, cx, cy, s, c):
    ax.add_patch(Circle((cx - 0.08 * s, cy + 0.08 * s), 0.26 * s, fc="white", ec=c, lw=3, zorder=6))
    ax.plot([cx + 0.11 * s, cx + 0.34 * s], [cy - 0.11 * s, cy - 0.34 * s], color=c, lw=4.5, zorder=6,
            solid_capstyle="round")


def icon_scales(ax, cx, cy, s, c):
    ax.plot([cx, cx], [cy - 0.4 * s, cy + 0.3 * s], color=c, lw=2.8, zorder=6, solid_capstyle="round")
    ax.plot([cx - 0.24 * s, cx + 0.24 * s], [cy - 0.4 * s, cy - 0.4 * s], color=c, lw=3, zorder=6,
            solid_capstyle="round")
    ax.plot([cx - 0.4 * s, cx + 0.4 * s], [cy + 0.26 * s, cy + 0.26 * s], color=c, lw=2.8, zorder=6,
            solid_capstyle="round")
    for dx in (-0.4, 0.4):
        ax.plot([cx + dx * s, cx + dx * s], [cy + 0.26 * s, cy + 0.02 * s], color=c, lw=1.6, zorder=6)
        ax.add_patch(Arc((cx + dx * s, cy + 0.02 * s), 0.34 * s, 0.24 * s, theta1=180, theta2=360, color=c, lw=2.6,
                         zorder=6))


def save(fig, name):
    fig.savefig(os.path.join(HERE, name), dpi=200, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    print("wrote", name)


# Slide 1: the chat scene ----------------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(13, 6.6))
ax.set_xlim(0, 13)
ax.set_ylim(0, 6.6)
ax.set_aspect("equal")
ax.axis("off")

icon_person(ax, 0.6, 5.42, 0.75, GREY)
box(ax, 1.15, 5.0, 5.35, 0.85, CUST)
ax.text(1.4, 5.43, "“Can I keep the car a few days longer?”", va="center", fontsize=13.5, color=INK)
icon_car(ax, 7.25, 5.42, 0.9, OURS)

icon_robot(ax, 0.6, 3.9, 0.8, GOOD)
box(ax, 1.15, 3.1, 5.35, 1.55, GOOD_BG, ec=GOOD, lw=2)
ax.text(1.4, 4.38, "Chatbot (correct)", fontsize=11, color=GOOD, fontweight="bold")
ax.text(1.4, 3.85, "“You can usually extend your rental,", fontsize=13, color=INK)
ax.text(1.4, 3.38, "as long as the car is not reserved.”", fontsize=13, color=GOOD, fontweight="bold")

icon_robot(ax, 0.6, 1.95, 0.8, BAD)
box(ax, 1.15, 1.15, 5.35, 1.55, BAD_BG, ec=BAD, lw=2)
ax.text(1.4, 2.43, "Chatbot (one half-sentence missing)", fontsize=11, color=BAD, fontweight="bold")
ax.text(1.4, 1.9, "“You can usually extend your rental.”", fontsize=13, color=INK)
ax.text(1.4, 1.45, "→ a promise SIXT cannot keep", fontsize=12, color=BAD, style="italic")

ax.add_patch(FancyArrowPatch((6.6, 1.92), (7.4, 1.92), arrowstyle="-|>", mutation_scale=22, color=INK2, lw=2))
ax.annotate("", xy=(7.4, 3.9), xytext=(7.0, 2.0),
            arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.6, connectionstyle="arc3,rad=-0.25"))

box(ax, 7.45, 3.1, 5.3, 1.55, "#f3f2ef", ec=LINE, lw=2)
icon_shield(ax, 8.1, 3.88, 0.9, GREY, "check")
ax.text(8.75, 4.3, "Starting AI checker", fontsize=12, color=INK2, fontweight="bold")
ax.text(8.75, 3.82, "PASS — sends it out", fontsize=13.5, color=BAD, fontweight="bold")
ax.text(8.75, 3.38, "misses 93% of dropped conditions", fontsize=11.5, color=INK2)

box(ax, 7.45, 0.8, 5.3, 1.95, "#eaf2fc", ec=OURS, lw=2.5)
icon_shield(ax, 8.1, 1.78, 0.9, OURS, "cross")
ax.text(8.75, 2.4, "Our checker", fontsize=12, color=OURS, fontweight="bold")
ax.text(8.75, 1.9, "BLOCKED", fontsize=15, color=BAD, fontweight="bold")
ax.text(8.75, 1.45, "drops “as long as the car is", fontsize=11.5, color=INK)
ax.text(8.75, 1.08, "not reserved” (policy: extensions)", fontsize=11.5, color=INK)
ax.text(6.5, 0.3, "Every reply is checked before it reaches the customer", ha="center", fontsize=12.5, color=INK2)
save(fig, "0_problem_scene.png")

# Slide 2: the recipe as a flow ----------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(13, 4.8))
ax.set_xlim(0, 13)
ax.set_ylim(0, 4.8)
ax.set_aspect("equal")
ax.axis("off")
steps = [("1", "Quote the rule", "find the policy line\nthe reply is about", icon_doc),
         ("2", "List statements", "every concrete claim\nin the reply", icon_list),
         ("3", "Find differences", "numbers, conditions,\ncertainty, scope", icon_magnifier),
         ("4", "Criterion decides", "only differences the\ncriterion names count", icon_scales)]
x0, w, gap = 0.25, 2.75, 0.45
for i, (n, title, sub, icon) in enumerate(steps):
    x = x0 + i * (w + gap)
    box(ax, x, 1.35, w, 2.75, "#eaf2fc" if i == 3 else "white", ec=OURS, r=0.2, lw=2.2 if i == 3 else 1.6)
    ax.add_patch(Circle((x + 0.45, 3.65), 0.25, color=OURS, zorder=5))
    ax.text(x + 0.45, 3.65, n, ha="center", va="center", color="white", fontsize=13, fontweight="bold", zorder=6)
    icon(ax, x + w / 2 + 0.35, 3.5, 0.75, OURS)
    ax.text(x + 0.25, 2.65, title, va="center", fontsize=14, color=INK, fontweight="bold")
    ax.text(x + 0.25, 1.95, sub, va="center", fontsize=12, color=INK2, linespacing=1.4)
    if i < 3:
        ax.add_patch(FancyArrowPatch((x + w + 0.05, 2.7), (x + w + gap - 0.05, 2.7), arrowstyle="-|>",
                                     mutation_scale=20, color=OURS, lw=2))
ax.text(0.25, 0.8, "+ examples picked automatically from labelled data   "
        "+ code checks numbers (tests itself first)   + asked twice: blocked only if both say FAIL",
        fontsize=11.5, color=INK2)
ax.text(0.25, 0.3, "Same code for every rule: only the criterion text and a few examples change.",
        fontsize=12.5, color=OURS, fontweight="bold")
save(fig, "0_recipe_flow.png")
