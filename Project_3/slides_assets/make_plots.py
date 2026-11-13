"""Slide charts for the pitch (PNG, 16:9-friendly). Run from Project_3/: .venv/bin/python slides_assets/make_plots.py
All numbers are measured results from this project (held out by source reply, event endpoint, claude-haiku-4.5)."""
import json
import os
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.join(HERE, "..", "starter_pack")
OURS, BASE = "#2a78d6", "#a8a69f"          # series: ours (categorical slot 1), starting judge (recessive gray)
REJ = "#e34948"                            # only for "rejected" markers, always with a text label
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e4df", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF, "axes.facecolor": SURF})


def per_type(csv, pairs="dev_pairs.jsonl"):
    out = os.path.join(HERE, "_tmp.json")
    subprocess.run([sys.executable, "score.py", csv, pairs, "--json", out], cwd=SP, check=True, capture_output=True)
    d = json.load(open(out))["result"]
    os.remove(out)
    return d


def clean(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)


def save(fig, name):
    fig.savefig(os.path.join(HERE, name), dpi=200, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    print("wrote", name)


# 1. Headline: both official criteria, starting judge vs ours --------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5.2))
groups = ["Criterion 1\nover-promising", "Criterion 2 (surprise)\npolicy stated correctly"]
base, ours = [0.697, 0.652], [0.900, 0.863]
x = range(len(groups))
w = 0.34
for i, (b, o) in enumerate(zip(base, ours)):
    ax.bar(i - w / 2 - 0.01, b, w, color=BASE, zorder=2)
    ax.bar(i + w / 2 + 0.01, o, w, color=OURS, zorder=2)
    ax.text(i - w / 2 - 0.01, b + 0.015, f"{b:.2f}", ha="center", color=INK2, fontsize=15)
    ax.text(i + w / 2 + 0.01, o + 0.015, f"{o:.2f}", ha="center", color=INK, fontsize=17, fontweight="bold")
    ax.text(i + w / 2 + 0.01, o / 2, f"+{o - b:.2f}", ha="center", color="white", fontsize=14, fontweight="bold")
ax.set_xticks(list(x), groups, fontsize=14, color=INK)
ax.set_ylim(0, 1.05)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax.yaxis.grid(True, color=GRID, zorder=0)
ax.set_ylabel("combined score (catch × keep balance)")
clean(ax)
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=BASE), plt.Rectangle((0, 0), 1, 1, color=OURS)],
          labels=["SIXT starting judge", "Our recipe (same code for both)"], frameon=False, loc="upper center",
          ncol=2, bbox_to_anchor=(0.5, 1.12), fontsize=13)
save(fig, "1_headline.png")

# 2. Where it got better: criterion 1 per edit type ----------------------------------------------------------------
b = per_type("baseline_dev_verdicts.csv")["per_edit_type"]
o = per_type("e5_c1.csv")["per_edit_type"]
names = {"condition_removal": "condition dropped", "hedge_removal": '"usually" → "always"',
         "wrong_number": "wrong number", "wrong_policy_detail": "wrong detail",
         "translation": "translated", "sentence_reorder": "sentences reordered", "polite_opener": "polite opener",
         "filler_padding": "filler sentence", "padding_removal": "pleasantry removed"}
harmful = ["condition_removal", "hedge_removal", "wrong_number", "wrong_policy_detail"]
harmless = ["translation", "sentence_reorder", "filler_padding", "polite_opener"]
rows = [(names[t], b[t]["catch"], o[t]["catch"], "caught") for t in harmful] + \
       [(names[t], b[t]["keep"], o[t]["keep"], "kept") for t in harmless]
fig, ax = plt.subplots(figsize=(10, 5.8))
for i, (n, bv, ov, kind) in enumerate(reversed(rows)):
    ax.plot([bv, ov], [i, i], color=GRID, lw=3, zorder=1, solid_capstyle="round")
    ax.scatter([bv], [i], s=110, color=BASE, zorder=3, edgecolor=SURF, linewidth=2)
    ax.scatter([ov], [i], s=130, color=OURS, zorder=4, edgecolor=SURF, linewidth=2)
    ax.text(ov + (0.025 if ov >= bv else -0.025), i, f"{ov:.0%}", va="center", ha="left" if ov >= bv else "right",
            color=INK, fontsize=12, fontweight="bold")
    ax.text(bv + (-0.025 if ov >= bv else 0.025), i, f"{bv:.0%}", va="center", ha="right" if ov >= bv else "left",
            color=INK2, fontsize=11)
ax.set_yticks(range(len(rows)), [f"{n}  ({k})" for n, _, _, k in reversed(rows)], fontsize=12, color=INK)
ax.axhline(len(harmless) - 0.5, color=GRID, lw=1)
ax.text(1.02, len(rows) - 1, "harmful edits\n→ must be caught", transform=ax.get_yaxis_transform(), va="top",
        fontsize=11, color=INK2)
ax.text(1.02, len(harmless) - 1, "harmless edits\n→ must be kept", transform=ax.get_yaxis_transform(), va="top",
        fontsize=11, color=INK2)
ax.set_xlim(-0.05, 1.12)
ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0], ["0%", "25%", "50%", "75%", "100%"])
ax.xaxis.grid(True, color=GRID, zorder=0)
clean(ax)
ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", color=BASE, ms=10),
                   plt.Line2D([], [], marker="o", ls="", color=OURS, ms=10)],
          labels=["SIXT starting judge", "Our recipe"], frameon=False, loc="upper center", ncol=2,
          bbox_to_anchor=(0.45, 1.09), fontsize=12)
save(fig, "2_per_edit_type.png")

# 3. Generalisation: data and criteria the judge was never tuned on -----------------------------------------------
sets = [("Synthetic set 1\n(10 new topics)", 0.810, 0.931), ("Synthetic set 2\n(100 more cases)", 0.781, 0.908),
        ("Practice criterion\n\"facts correct\"", 0.932, 0.931), ("Practice criterion\n\"conditions kept\"", 0.556, 0.806),
        ("Practice criterion\n\"starts with answer\"", 0.424, 0.720)]
fig, ax = plt.subplots(figsize=(10, 5.6))
for i, (n, bv, ov) in enumerate(reversed(sets)):
    ax.barh(i + 0.19, bv, 0.36, color=BASE, zorder=2)
    ax.barh(i - 0.19, ov, 0.36, color=OURS, zorder=2)
    ax.text(bv + 0.01, i + 0.19, f"{bv:.2f}", va="center", color=INK2, fontsize=11)
    ax.text(ov + 0.01, i - 0.19, f"{ov:.2f}", va="center", color=INK, fontsize=12, fontweight="bold")
ax.set_yticks(range(len(sets)), [n for n, _, _ in reversed(sets)], fontsize=12, color=INK)
ax.set_xlim(0, 1.08)
ax.xaxis.grid(True, color=GRID, zorder=0)
ax.set_xlabel("combined score")
clean(ax)
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=BASE), plt.Rectangle((0, 0), 1, 1, color=OURS)],
          labels=["SIXT starting judge", "Our recipe (code unchanged)"], frameon=False, loc="upper center", ncol=2,
          bbox_to_anchor=(0.4, 1.09), fontsize=12)
save(fig, "3_generalisation.png")

# 4. The way of working: every idea measured, kept or rejected -----------------------------------------------------
kept = [("Start", 0.697), ("Step-by-step\nreasoning", 0.692), ("Benefit of\nthe doubt", 0.752), ("Ask twice,\nboth fail", 0.779),
        ("Extra good\nexamples", 0.791), ("Number\ncheck", 0.803), ("Numbers:\nno doubt", 0.840),
        ("Criterion\ndecides", 0.900)]
rejected = [(6, 0.838, "who-benefits\nreasoning"), (7, 0.783, "number rule\nas note"), (7, 0.862, "who-benefits\nagain"),
            (7, 0.846, "tone-aware\nstep 2"), (7, 0.821, "tone exception")]
fig, ax = plt.subplots(figsize=(12, 5.4))
xs = list(range(len(kept)))
ax.plot(xs, [v for _, v in kept], color=OURS, lw=2.5, zorder=3)
ax.scatter(xs, [v for _, v in kept], s=90, color=OURS, zorder=4, edgecolor=SURF, linewidth=2)
for xi, (_, v) in zip(xs, kept):
    ax.text(xi, v + 0.012, f"{v:.2f}", ha="center", fontsize=11, color=INK, fontweight="bold")
offs = {0.783: -0.05, 0.821: -0.035, 0.846: -0.02, 0.862: -0.005, 0.838: -0.04}
for xi, v, lab in rejected:
    xj = xi + 0.32
    ax.scatter([xj], [v], s=70, facecolor=SURF, edgecolor=REJ, linewidth=2, zorder=4)
ax.text(7.32, 0.765, "5 ideas tested\nand rejected\n(score fell)", color=REJ, fontsize=10.5, ha="center", va="top")
ax.text(6.32, 0.825, "rejected", color=REJ, fontsize=10, ha="center", va="top")
ax.set_xticks(xs, [n for n, _ in kept], fontsize=10.5, color=INK)
ax.set_ylim(0.65, 0.95)
ax.set_xlim(-0.4, 7.9)
ax.yaxis.grid(True, color=GRID, zorder=0)
ax.set_ylabel("criterion 1, combined score")
clean(ax)
ax.legend(handles=[plt.Line2D([], [], marker="o", color=OURS, ms=9, lw=2.5),
                   plt.Line2D([], [], marker="o", ls="", markerfacecolor=SURF, markeredgecolor=REJ, ms=9, mew=2)],
          labels=["kept: each step measured on held-out data", "rejected: measured, then reverted"], frameon=False,
          loc="upper left", fontsize=11)
save(fig, "4_journey.png")
