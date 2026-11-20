"""Claude Opus 5 replication against GPT-5.6: share and the periodic board minus solo, both framings, 8 pilot worlds.

Plan fixed in docs/PILOT_MULTIAGENT.md, addendum 2026-11-17 (Claude), before the runs.
Unit: the world; a world's value is the mean over its completed keyed runs. Exact two-sided sign-flip test over the
worlds and a 95% t interval. The GPT-5.6 rows use the same three conditions' existing runs.

    .venv/bin/python paper/scripts/stats_claude.py
Writes results/multiagent/stats_claude.json and stats_claude.md.
"""
import collections
import json
import math
import statistics as st
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parents[2] / "results" / "multiagent"
MODELS = ["claude-opus-5-5", "gpt-5.6-sol"]   # claude-opus-5 refused; its two refused teams are not analysed
ARMS = ["share", "share_at6-11-16"]
FRAMINGS = [("", "lemonade"), ("_alien", "alien")]
MEASURES = ["best_peak", "sum_pct", "unique", "reached_best"]
TCRIT = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365}
ROUNDS = 20


def load(arm, model):
    f = OUT / f"{arm}__{model}.jsonl"
    rows, seen = [], set()
    if not f.exists():
        return rows
    for line in f.read_text().splitlines():
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
    best = 100 * max(max(e["profits"][:ROUNDS]) for e in eps) / g
    n = sum(len(e["profits"][:ROUNDS]) for e in eps)
    return {"best_peak": best,
            "sum_pct": 100 * sum(sum(e["profits"][:ROUNDS]) for e in eps) / (g * n),
            "unique": float(len({setting(a) for e in eps for a in e["actions"][:ROUNDS]})),
            "reached_best": 100.0 * (best > 60)}


import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from env.world_generator import load_world_set, world_id  # noqa: E402
PILOT = {world_id(w) for w in load_world_set(Path(__file__).resolve().parents[2] / "data" / "worlds_main.json")["val"][:8]}


def world_values(arm, model, meas):
    """Pilot worlds only, so the GPT rows match the Claude rows world for world (GPT's periodic-board arm also has
    16 further worlds; those are analysed in stats_worlds24.py)."""
    by = collections.defaultdict(list)
    for r in load(arm, model):
        if r["world_id"] not in PILOT:
            continue
        by[(r["world_id"], int(str(r["repeat"]).split(".")[0]))].append(r)
    vals = collections.defaultdict(list)
    for (w, rep), eps in by.items():
        if len(eps) == 3:
            vals[w].append(measures(eps)[meas])
    return {w: st.mean(v) for w, v in vals.items()}


def perm_p(d):
    d = np.asarray(d, dtype=float)
    n, obs = len(d), abs(d.sum())
    idx = np.arange(2 ** n, dtype=np.int64)
    bits = ((idx[:, None] >> np.arange(n)) & 1).astype(float) * 2 - 1
    return float((np.abs(bits @ d) >= obs - 1e-9).mean())


def summ(d):
    n, m = len(d), sum(d) / len(d)
    h = TCRIT.get(n - 1, 2.0) * st.stdev(d) / math.sqrt(n) if n > 1 else float("nan")
    return {"n": n, "mean": m, "lo": m - h, "hi": m + h, "p": perm_p(d),
            "up": sum(x > 1e-9 for x in d), "down": sum(x < -1e-9 for x in d)}


def main():
    res, lines = {}, ["# Share and periodic board minus solo, paired over the 8 pilot worlds\n",
                      "| model | framing | measure | condition | n | solo | condition | diff [95% CI] | p | up/down |",
                      "|---|---|---|---|---|---|---|---|---|---|"]
    for model in MODELS:
        for suf, fr in FRAMINGS:
            for meas in MEASURES:
                solo = world_values("solo" + suf, model, meas)
                for arm in ARMS:
                    a = world_values(arm + suf, model, meas)
                    ws = sorted(set(solo) & set(a))
                    if len(ws) < 2:
                        lines.append(f"| {model} | {fr} | {meas} | {arm} | {len(ws)} | not enough complete worlds | | | | |")
                        continue
                    r = summ([a[w] - solo[w] for w in ws])
                    r["solo_mean"], r["arm_mean"] = st.mean(solo[w] for w in ws), st.mean(a[w] for w in ws)
                    res[f"{model}|{fr}|{meas}|{arm}"] = r
                    lines.append(f"| {model} | {fr} | {meas} | {arm} | {r['n']} | {r['solo_mean']:.1f} | {r['arm_mean']:.1f} | "
                                 f"{r['mean']:+.1f} [{r['lo']:+.1f}, {r['hi']:+.1f}] | {r['p']:.3f} | {r['up']}/{r['down']} |")
    (OUT / "stats_claude.json").write_text(json.dumps(res, indent=1))
    (OUT / "stats_claude.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
