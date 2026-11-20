"""The two figures of the sharing write-up, from the combined runs.

    .venv/bin/python paper/scripts/fig_multiagent_reps.py
Reads results/multiagent/stats_reps.json and writeup_numbers.json; writes fig_sharing_intervals.png and
fig_sharing_timing.png next to them.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

OUT = Path(__file__).resolve().parents[2] / "results" / "multiagent"
LEM, ALI, INK, INK2, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df"
ROWS = [("share", "Sharing all along"), ("share_from3", "Sharing after 2 private rounds"),
        ("share_from6", "Sharing after 5 private rounds"), ("share_from11", "Sharing after 10 private rounds"),
        ("share_from16", "Sharing after 15 private rounds"), ("share_at6-11-16", "Sharing in 3 rounds only"),
        ("share_protocol", "Sharing, told to stay different"), ("share_staggered", "One agent at a time")]
PANELS = [("best_peak", "Maximum single-round profit", "pp, relative to working alone"),
          ("sum_pct", "Cumulative earnings", "pp, relative to working alone"),
          ("unique", "Distinct setups tried", "setups out of 60")]


def intervals(res):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": INK, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK})
    fig, axes = plt.subplots(1, 3, figsize=(11.2, 7.0), dpi=120, sharey=True)
    fig.subplots_adjust(left=0.235, right=0.985, top=0.83, bottom=0.17, wspace=0.10)
    ys, y_all = list(range(len(ROWS), 0, -1)), -0.6
    for ax, (meas, title, xlabel) in zip(axes, PANELS):
        for (key, _lab), y in zip(ROWS, ys):
            for name, col, dy in (("lemonade", LEM, 0.17), ("alien", ALI, -0.17)):
                r = res[f"{name}|{meas}|{key}"]
                ax.plot([r["lo"], r["hi"]], [y + dy, y + dy], color=col, lw=2, solid_capstyle="round", zorder=2)
                ax.plot(r["mean"], y + dy, "o", color=col, ms=7, mec="white", mew=1.2, zorder=3)
        for name, col, dy in (("lemonade", LEM, 0.17), ("alien", ALI, -0.17)):
            r = res[f"{name}|{meas}|all_sharing"]
            ax.plot([r["lo"], r["hi"]], [y_all + dy, y_all + dy], color=col, lw=3, solid_capstyle="round", zorder=2)
            ax.plot(r["mean"], y_all + dy, "D", color=col, ms=8, mec="white", mew=1.2, zorder=3)
        ax.axvline(0, color=INK, lw=1, zorder=1)
        ax.axhline(0.2, color=GRID, lw=1, zorder=0)
        ax.set_title(title, fontsize=12, color=INK, pad=8)
        ax.set_xlabel(xlabel, fontsize=9.5, labelpad=6)
        ax.grid(axis="x", color=GRID, lw=0.8, zorder=0)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(length=0, labelsize=9.5)
        ax.set_ylim(-1.3, len(ROWS) + 0.6)
        lim = max(abs(v) for v in ax.get_xlim())
        ax.set_xlim(-lim, lim)
    axes[0].set_yticks(ys + [y_all], [lab for _k, lab in ROWS] + ["All sharing conditions"], fontsize=10.5)
    axes[0].get_yticklabels()[-1].set_fontweight("bold")
    handles = [Line2D([], [], color=LEM, lw=2, marker="o", ms=7, mec="white", label="Lemonade version"),
               Line2D([], [], color=ALI, lw=2, marker="o", ms=7, mec="white", label="Alien version")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.015), ncol=2, frameon=False, fontsize=10.5,
               columnspacing=3, labelcolor=INK)
    fig.text(0.02, 0.965, "Sharing compared with working alone, all runs", fontsize=16, ha="left", va="top", color=INK)
    fig.text(0.02, 0.905, "Average difference on the same world. Bars are 95% confidence intervals over the eight worlds. "
             "A bar that crosses zero could be chance.", fontsize=10.5, ha="left", va="top", color=INK2)
    fig.savefig(OUT / "fig_sharing_intervals.png", dpi=120, facecolor="white")
    plt.close(fig)


def timing(num):
    x = [1, 3, 6, 11, 16]
    arms = ["share", "share_from3", "share_from6", "share_from11", "share_from16"]
    m = lambda name, a: num["tables"][f"{name}|best_peak|{a}"]["mean"]
    lem, ali = [m("lemonade", a) for a in arms], [m("alien", a) for a in arms]
    lem_solo, ali_solo = m("lemonade", "solo"), m("alien", "solo")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "text.color": INK, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2})
    fig, ax = plt.subplots(figsize=(11.2, 6.0), dpi=120)
    fig.subplots_adjust(left=0.07, right=0.97, top=0.80, bottom=0.25)
    ax.plot(x, lem, color=LEM, lw=2, marker="o", ms=8, mfc=LEM, mec="white", mew=1.5, zorder=3)
    ax.plot(x, ali, color=ALI, lw=2, marker="o", ms=8, mfc=ALI, mec="white", mew=1.5, zorder=3)
    ax.axhline(lem_solo, color=LEM, lw=1.4, ls=(0, (7, 4)), zorder=2)
    ax.axhline(ali_solo, color=ALI, lw=1.4, ls=(0, (7, 4)), zorder=2)

    def lab(xi, v, dy):
        ax.annotate(f"{v:.1f}", (xi, v), textcoords="offset points", xytext=(0, dy), ha="center",
                    va="bottom" if dy > 0 else "top", fontsize=12, color=INK)
    for xi, v, a in zip(x, lem, ali):       # the lower of the two points is labelled below, the higher above
        lab(xi, v, 10 if v > a else -14)
    for xi, v, l in zip(x, ali, lem):
        above = v > l
        clear = max(lem_solo, ali_solo) + 0.4          # a label above must clear both dashed lines
        dy = (10 if v + 3.6 < min(lem_solo, ali_solo) else int((clear - v) * 5.9) + 2) if above else -14
        lab(xi, v, dy)
    ax.text(0.2, ali_solo + 0.9, f"alien, working alone {ali_solo:.1f}", ha="left", va="bottom", fontsize=11, color=INK2)
    ax.text(0.2, lem_solo - 0.9, f"lemonade, working alone {lem_solo:.1f}", ha="left", va="top", fontsize=11, color=INK2)
    ax.set_xticks(x, ["1 (all along)", "3", "6", "11", "16"])
    ax.set_xlim(0.0, 16.8)
    ax.set_ylim(60, 96)
    ax.set_yticks(range(60, 100, 10))
    ax.set_xlabel("Round in which the shared board opens", labelpad=10)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(INK2)
    ax.tick_params(length=0)
    handles = [Line2D([], [], color=LEM, lw=2, marker="o", ms=8, mfc=LEM, mec="white", label="Lemonade version, sharing"),
               Line2D([], [], color=ALI, lw=2, marker="o", ms=8, mfc=ALI, mec="white", label="Alien version, sharing"),
               Line2D([], [], color=LEM, lw=1.4, ls=(0, (7, 4)), label="Lemonade version, working alone"),
               Line2D([], [], color=ALI, lw=1.4, ls=(0, (7, 4)), label="Alien version, working alone")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.035), frameon=False, fontsize=11, ncol=2,
               labelcolor=INK, columnspacing=3)
    fig.text(0.03, 0.955, "Maximum single-round profit by the round in which the board opens", fontsize=17, ha="left", va="top", color=INK)
    fig.text(0.03, 0.885, "Team's maximum single-round profit as % of the world's, averaged over eight worlds and all runs.",
             fontsize=12, ha="left", va="top", color=INK2)
    fig.savefig(OUT / "fig_sharing_timing.png", dpi=120, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    intervals(json.loads((OUT / "stats_reps.json").read_text())["all_runs"])
    timing(json.loads((OUT / "writeup_numbers.json").read_text()))
    print("figures written")
