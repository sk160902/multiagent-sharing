"""Timing chart for the short sharing write-up: averages over all runs, bars = standard deviation across runs.

    python3 -I paper/scripts/fig_multiagent_timing_runs.py
Reads results/multiagent/writeup_run_means.json; writes results/multiagent/fig_sharing_timing_runs.png.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

OUT = Path(__file__).resolve().parents[2] / "results" / "multiagent"
R = json.loads((OUT / "writeup_run_means.json").read_text())
LEM, ALI = "#2F6DB5", "#D9661F"
x = [1, 3, 6, 11, 16]
arms = ["share", "share_from3", "share_from6", "share_from11", "share_from16"]
get = lambda name, a, k: R[f"{name}|best_peak|{a}"][k]
lem, ali = [get("lemonade", a, "mean") for a in arms], [get("alien", a, "mean") for a in arms]
lem_sd, ali_sd = [get("lemonade", a, "sd") for a in arms], [get("alien", a, "sd") for a in arms]
lem_solo, ali_solo = get("lemonade", "solo", "mean"), get("alien", "solo", "mean")

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "text.color": "black",
                     "axes.labelcolor": "black", "xtick.color": "black", "ytick.color": "black"})
fig, ax = plt.subplots(figsize=(11.2, 6.0), dpi=120)
fig.subplots_adjust(left=0.07, right=0.97, top=0.80, bottom=0.25)
D = 0.13                                              # the two series sit side by side so their bars do not overlap
xl, xa = [v - D for v in x], [v + D for v in x]
ax.errorbar(xl, lem, yerr=lem_sd, color=LEM, lw=2.4, marker="o", ms=8, mfc=LEM, mec=LEM, elinewidth=1.6, capsize=4, zorder=3)
ax.errorbar(xa, ali, yerr=ali_sd, color=ALI, lw=2.4, marker="o", ms=8, mfc=ALI, mec=ALI, elinewidth=1.6, capsize=4, zorder=3)
ax.axhline(lem_solo, color=LEM, lw=1.4, ls=(0, (7, 4)), zorder=2)
ax.axhline(ali_solo, color=ALI, lw=1.4, ls=(0, (7, 4)), zorder=2)
# labels sit diagonally off each point, on the side its line and its bar leave free
LEM_OFF = {1: (-10, 12), 3: (-10, -12), 6: (-10, -12), 11: (-10, -12), 16: (10, -12)}
ALI_OFF = {1: (10, -12), 3: (10, 12), 6: (10, -12), 11: (10, -12), 16: (10, 26)}
for series, xs, off in ((lem, xl, LEM_OFF), (ali, xa, ALI_OFF)):
    for x0, xi, v in zip(x, xs, series):
        dx, dy = off[x0]
        ax.annotate(f"{v:.1f}", (xi, v), textcoords="offset points", xytext=(dx, dy), ha="right" if dx < 0 else "left",
                    va="bottom" if dy > 0 else "top", fontsize=12)
ax.text(7.2, ali_solo + 0.8, f"alien alone {ali_solo:.1f}", ha="left", va="bottom", fontsize=11, color=ALI)
ax.text(7.2, lem_solo - 0.8, f"lemonade alone {lem_solo:.1f}", ha="left", va="top", fontsize=11, color=LEM)
ax.set_xticks(x, ["1 (all along)", "3", "6", "11", "16"])
ax.set_xlim(-0.3, 17.4)
ax.set_ylim(55, 96)
ax.set_yticks(range(60, 100, 10))
ax.set_xlabel("Round in which the shared board opens", labelpad=10)
ax.grid(axis="y", color="black", alpha=0.15, lw=0.8)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("black")
ax.tick_params(length=0)
handles = [Line2D([], [], color=LEM, lw=2.4, marker="o", ms=8, mfc=LEM, label="Lemonade version, sharing"),
           Line2D([], [], color=ALI, lw=2.4, marker="o", ms=8, mfc=ALI, label="Alien version, sharing"),
           Line2D([], [], color=LEM, lw=1.4, ls=(0, (7, 4)), label="Lemonade version, working alone"),
           Line2D([], [], color=ALI, lw=1.4, ls=(0, (7, 4)), label="Alien version, working alone")]
fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.035), frameon=False, fontsize=11, ncol=2,
           labelcolor="black", columnspacing=3)
fig.text(0.03, 0.955, "Opening the board late helps in both versions, with different shapes", fontsize=17, ha="left", va="top")
fig.text(0.03, 0.885, "Team's maximum single-round profit as % of the world's. Bars show the spread across runs.", fontsize=12, ha="left", va="top")
fig.savefig(OUT / "fig_sharing_timing_runs.png", dpi=120, facecolor="white")
print("written")
