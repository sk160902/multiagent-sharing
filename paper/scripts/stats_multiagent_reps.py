"""Paired tests for the repeat runs of the shared-workspace pilot.

Plan fixed in docs/PILOT_MULTIAGENT.md, addenda 2026-11-04 and 2026-11-05, before the runs they cover.
Unit: the world. A world's value for a condition is the mean over its completed keyed runs.
Contrasts: each of the eight sharing conditions minus solo, the mean of the eight minus solo
(`all_sharing`), and the mean of the three conditions of the first addendum minus solo
(`core_sharing`), within a framing and with the two framings averaged per world. Exact two-sided sign-flip
test over the worlds and a 95% t interval on the world-level differences.

    .venv/bin/python paper/scripts/stats_multiagent_reps.py
Writes results/multiagent/stats_reps.json and stats_reps.md.
"""
import collections
import itertools
import json
import math
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from env.world_generator import load_world_set, world_id  # noqa: E402

OUT = ROOT / "results" / "multiagent"
MODEL = "gpt-5.6-sol"
# The 8 pilot worlds. Since 2026-11-17 the solo and periodic-board files also hold the 16 extension worlds
# (val[16:32]); this analysis is the 8-world one and reads only the pilot worlds (added 2026-11-20, no change
# to any number: the pilot-world records are untouched).
PILOT = {world_id(w) for w in load_world_set(ROOT / "data" / "worlds_main.json")["val"][:8]}
CORE = ["share", "share_from6", "share_at6-11-16"]
SHARING = ["share", "share_from3", "share_from6", "share_from11", "share_from16", "share_at6-11-16",
           "share_protocol", "share_staggered"]
ARMS = ["solo"] + SHARING
FRAMINGS = [("", "lemonade"), ("_alien", "alien")]
MEASURES = ["best_peak", "sum_pct", "unique", "reached_best"]
TCRIT = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365}
ROUNDS = 20


def load(arm):
    """Episodes of one arm, first occurrence of each key kept."""
    rows, seen = [], set()
    for line in (OUT / f"{arm}__{MODEL}.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["key"] in seen:
            continue
        seen.add(r["key"])
        rows.append(r)
    return rows


def setting(a):
    return (a["location"], a["color"], a["sugar"], a["lemon"], a["price"])


def measures(eps):
    g = eps[0]["metrics"]["gmax"]
    peaks = [max(e["profits"][:ROUNDS]) for e in eps]
    n = sum(len(e["profits"][:ROUNDS]) for e in eps)
    best = 100 * max(peaks) / g
    return {"best_peak": best,
            "sum_pct": 100 * sum(sum(e["profits"][:ROUNDS]) for e in eps) / (g * n),
            "unique": float(len({setting(a) for e in eps for a in e["actions"][:ROUNDS]})),
            "reached_best": 100.0 * (best > 60)}


def teams(arm):
    """(world, repeat) -> measures, complete teams of three only."""
    by = collections.defaultdict(list)
    for r in load(arm):
        if r["world_id"] not in PILOT or r.get("horizon", 20) != ROUNDS:
            continue
        by[(r["world_id"], int(str(r["repeat"]).split(".")[0]))].append(r)
    return {k: measures(v) for k, v in by.items() if len(v) == 3}


def perm_p(d):
    obs, c = abs(sum(d)), 0
    for s in itertools.product((1, -1), repeat=len(d)):
        if abs(sum(x * y for x, y in zip(s, d))) >= obs - 1e-9:
            c += 1
    return c / 2 ** len(d)


def summ(d):
    n, m = len(d), sum(d) / len(d)
    h = TCRIT[n - 1] * st.stdev(d) / math.sqrt(n) if n > 1 else float("nan")
    return {"n": n, "mean": m, "lo": m - h, "hi": m + h, "p": perm_p(d),
            "up": sum(x > 1e-9 for x in d), "down": sum(x < -1e-9 for x in d)}


def world_values(T, arm, meas, reps):
    """world -> mean over the completed runs among `reps`."""
    out = collections.defaultdict(list)
    for (w, rep), m in T[arm].items():
        if rep in reps:
            out[w].append(m[meas])
    return {w: st.mean(v) for w, v in out.items()}


def contrasts(T, reps):
    res = {}
    per_framing = {}
    for suf, name in FRAMINGS:
        for meas in MEASURES:
            solo = world_values(T, "solo" + suf, meas, reps)
            arms = {a: world_values(T, a + suf, meas, reps) for a in SHARING}
            worlds = sorted(set(solo).intersection(*[set(v) for v in arms.values()]))
            if len(worlds) < 2:
                continue
            for a in SHARING:
                res[f"{name}|{meas}|{a}"] = summ([arms[a][w] - solo[w] for w in worlds])
            pooled = {w: st.mean(arms[a][w] for a in SHARING) - solo[w] for w in worlds}
            core = {w: st.mean(arms[a][w] for a in CORE) - solo[w] for w in worlds}
            res[f"{name}|{meas}|all_sharing"] = summ([pooled[w] for w in worlds])
            res[f"{name}|{meas}|core_sharing"] = summ([core[w] for w in worlds])
            per_framing[(name, meas)] = {"pooled": pooled, "core": core,
                                         **{a: {w: arms[a][w] - solo[w] for w in worlds} for a in SHARING}}
    for meas in MEASURES:
        if ("lemonade", meas) in per_framing and ("alien", meas) in per_framing:
            L, A = per_framing[("lemonade", meas)], per_framing[("alien", meas)]
            for k, lab in [("pooled", "all_sharing"), ("core", "core_sharing")] + [(a, a) for a in SHARING]:
                worlds = sorted(set(L[k]) & set(A[k]))
                res[f"both|{meas}|{lab}"] = summ([(L[k][w] + A[k][w]) / 2 for w in worlds])
    return res


def main():
    T = {a + suf: teams(a + suf) for suf, _ in FRAMINGS for a in ARMS}
    runs = {arm: dict(sorted(collections.Counter(rep for (_w, rep) in t).items())) for arm, t in T.items()}
    means = {}
    for suf, name in FRAMINGS:
        for a in ARMS:
            for meas in MEASURES:
                v = world_values(T, a + suf, meas, {0, 1, 2})
                means[f"{name}|{a}|{meas}"] = {"mean": st.mean(v.values()), "worlds": len(v),
                                               "by_world": {w[:8]: round(x, 1) for w, x in sorted(v.items())}}
    out = {"runs_per_arm": runs, "means_all_runs": means,
           "all_runs": contrasts(T, {0, 1, 2}), "first_run_only": contrasts(T, {0}), "new_runs_only": contrasts(T, {1, 2})}
    # does the new data fall on the same side of solo as the first run did
    same = {}
    for k, first in out["first_run_only"].items():
        new = out["new_runs_only"].get(k)
        if new is not None:
            same[k] = {"first": first["mean"], "new": new["mean"], "same_side": (first["mean"] > 0) == (new["mean"] > 0)}
    out["first_vs_new"] = same
    (OUT / "stats_reps.json").write_text(json.dumps(out, indent=1))

    def cell(v, unit):
        s = lambda x: ("+" if x > 0 else "-" if x < 0 else "") + f"{abs(x):.1f}"
        return f"{s(v['mean'])}{unit} [{s(v['lo'])}, {s(v['hi'])}] p={v['p']:.3f} ({v['up']} up, {v['down']} down)"
    lines = ["# Repeat runs: sharing conditions minus working alone, paired over worlds", "",
             f"Completed teams per arm and repeat: {json.dumps(runs)}", ""]
    for block, title in (("all_runs", "All runs (three per world where complete)"), ("first_run_only", "First run only"),
                         ("new_runs_only", "New runs only (repeats 1 and 2)")):
        cols = ["all_sharing", "core_sharing"] + SHARING
        lines += [f"## {title}", "", "| framing | measure | " + " | ".join(cols) + " |", "|---|---|" + "---|" * len(cols)]
        for name in ("lemonade", "alien", "both"):
            for meas in MEASURES:
                unit = "" if meas == "unique" else " pp"
                row = [out[block].get(f"{name}|{meas}|{k}") for k in cols]
                if all(r is None for r in row):
                    continue
                lines.append(f"| {name} | {meas} | " + " | ".join(cell(r, unit) if r else "n/a" for r in row) + " |")
        lines.append("")
    (OUT / "stats_reps.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
