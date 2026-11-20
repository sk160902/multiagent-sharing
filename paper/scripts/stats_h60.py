"""Sixty-round games: sharing all along against working alone, both framings, 8 pilot worlds, GPT-5.6.

Plan fixed in docs/PILOT_MULTIAGENT.md, addendum 2026-11-19 (horizon), before any 60-round episode ran.

Question: is the 20-round picture (sharing earns more over the game, explores less, and never raises the best round)
a property of the game or of stopping at round 20? Arms: solo_h60, share_h60, solo_alien_h60, share_alien_h60, each
8 worlds x 3 runs, compared with the existing 20-round runs of solo, share, solo_alien and share_alien on the same
worlds.

Unit: the world; a world's value is the mean over its completed runs (a run is the 3 agents of one repeat). Contrast:
share minus solo, paired within world, exact two-sided sign-flip test over the 8 worlds and a 95% t interval, on

  * the whole 60-round game: best_peak, sum_pct, unique, reached_best;
  * the late window, rounds 21-60: sum_pct_late, best_peak_late (the direct test of the comment: do the lone agents
    overtake once a late discovery has time to pay);
  * the first 20 rounds of the 60-round game, side by side with the 20-round runs (does being told "of 60" instead of
    "of 20" change early play).

Decision rule, fixed now (one framing is enough to trigger it):
  C1  sum_pct over 60 rounds, share minus solo: the sign reverses (negative) -> change.
  C2  sum_pct over rounds 21-60, share minus solo: negative -> change.
  C3  best_peak over 60 rounds, share minus solo: in a framing whose 20-round gap is below -5 points, a 60-round gap
      above -5 points -> change (sharing catches up on the ceiling given time).
  C4  unique over 60 rounds, share minus solo: positive -> change (unexpected; reported, not expected).
"No change" is all four holding their 20-round sign in both framings: the paper stays at 20 rounds and the 16-world
lemonade extension runs at 20 rounds. "Change" is any of C1-C3: the paper's horizon moves to 60 and the extension
runs there. Nothing is stopped or extended on the way.

    .venv/bin/python paper/scripts/stats_h60.py
Writes results/multiagent/stats_h60.json and stats_h60.md.
"""
import collections
import json
import math
import statistics as st
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from env.world_generator import load_world_set, world_id  # noqa: E402

OUT = ROOT / "results" / "multiagent"
MODEL = "gpt-5.6-sol"
FRAMINGS = [("", "lemonade"), ("_alien", "alien")]
H = 60
LATE = (20, 60)          # rounds 21-60, as a slice
TCRIT = {7: 2.365}
CLOSE = 5.0              # C3: a best_peak gap above -5 points counts as closed


def load(arm):
    f = OUT / f"{arm}__{MODEL}.jsonl"
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


def measures(eps, lo, hi):
    """Team measures over rounds lo+1..hi (a slice), as in stats_worlds24.py but on a window."""
    g = eps[0]["metrics"]["gmax"]
    peaks = [max(e["profits"][lo:hi]) for e in eps]
    n = sum(len(e["profits"][lo:hi]) for e in eps)
    best = 100 * max(peaks) / g
    return {"best_peak": best,
            "sum_pct": 100 * sum(sum(e["profits"][lo:hi]) for e in eps) / (g * n),
            "unique": float(len({setting(a) for e in eps for a in e["actions"][lo:hi]})),
            "reached_best": 100.0 * (best > 60)}


def teams(arm, pilot, lo, hi, horizon):
    by = collections.defaultdict(list)
    for r in load(arm):
        if r["world_id"] not in pilot or r.get("horizon", 20) != horizon or len(r["profits"]) < hi:
            continue
        by[(r["world_id"], int(str(r["repeat"]).split(".")[0]))].append(r)
    return {k: measures(v, lo, hi) for k, v in by.items() if len(v) == 3}


def world_values(T, meas):
    out = collections.defaultdict(list)
    for (w, rep), m in T.items():
        out[w].append(m[meas])
    return {w: st.mean(v) for w, v in out.items()}


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


def contrast(Ta, Tb, meas):
    """Paired world-level difference a minus b; None if fewer than two worlds have both."""
    a, b = world_values(Ta, meas), world_values(Tb, meas)
    ws = sorted(set(a) & set(b))
    if len(ws) < 2:
        return None
    r = summ([a[w] - b[w] for w in ws])
    r["b_mean"], r["a_mean"] = st.mean(b[w] for w in ws), st.mean(a[w] for w in ws)
    return r


def fmt(r):
    if r is None:
        return "not enough complete worlds"
    return (f"n={r['n']} | {r['b_mean']:.1f} -> {r['a_mean']:.1f} | diff {r['mean']:+.1f} "
            f"[{r['lo']:+.1f}, {r['hi']:+.1f}] p={r['p']:.3f} ({r['up']} up, {r['down']} down)")


def main():
    pilot = {world_id(w) for w in load_world_set(ROOT / "data" / "worlds_main.json")["val"][:8]}
    res, lines = {}, ["# Sixty-round games: sharing all along minus working alone, paired over the 8 pilot worlds\n"]
    verdict = {}
    for suf, fr in FRAMINGS:
        s60, a60 = teams(f"solo{suf}_h60", pilot, 0, H, H), teams(f"share{suf}_h60", pilot, 0, H, H)
        s60l, a60l = teams(f"solo{suf}_h60", pilot, *LATE, H), teams(f"share{suf}_h60", pilot, *LATE, H)
        s60f, a60f = teams(f"solo{suf}_h60", pilot, 0, 20, H), teams(f"share{suf}_h60", pilot, 0, 20, H)
        s20, a20 = teams(f"solo{suf}", pilot, 0, 20, 20), teams(f"share{suf}", pilot, 0, 20, 20)
        res[f"{fr}|runs"] = {"solo_h60": len(s60), "share_h60": len(a60), "solo_20": len(s20), "share_20": len(a20)}
        lines.append(f"\n## {fr} framing: runs solo_h60 {len(s60)}, share_h60 {len(a60)} "
                     f"(20-round comparators: solo {len(s20)}, share {len(a20)})\n")
        lines.append("| window | measure | share minus solo |")
        lines.append("|---|---|---|")
        for label, Ts, Ta in (("rounds 1-60", s60, a60), ("rounds 21-60", s60l, a60l),
                              ("rounds 1-20 of 60", s60f, a60f), ("20-round game", s20, a20)):
            for meas in ("best_peak", "sum_pct", "unique", "reached_best"):
                r = contrast(Ta, Ts, meas)
                res[f"{fr}|{label}|{meas}"] = r
                lines.append(f"| {label} | {meas} | {fmt(r)} |")
        lines.append("\n| stated horizon, same window (rounds 1-20) | measure | 60-round game minus 20-round game |")
        lines.append("|---|---|---|")
        for arm, Tf, T20 in (("solo", s60f, s20), ("share", a60f, a20)):
            for meas in ("best_peak", "sum_pct", "unique"):
                r = contrast(Tf, T20, meas)
                res[f"{fr}|early|{arm}|{meas}"] = r
                lines.append(f"| {arm} | {meas} | {fmt(r)} |")
        # decision rule
        c1 = res.get(f"{fr}|rounds 1-60|sum_pct")
        c2 = res.get(f"{fr}|rounds 21-60|sum_pct")
        c3 = res.get(f"{fr}|rounds 1-60|best_peak")
        c3_20 = res.get(f"{fr}|20-round game|best_peak")
        c4 = res.get(f"{fr}|rounds 1-60|unique")
        v = {"C1_sum_reversed": bool(c1 and c1["mean"] < 0),
             "C2_late_sum_negative": bool(c2 and c2["mean"] < 0),
             "C3_ceiling_gap_closed": bool(c3 and c3_20 and c3_20["mean"] < -CLOSE and c3["mean"] > -CLOSE),
             "C4_unique_positive": bool(c4 and c4["mean"] > 0),
             "complete": bool(c1 and c2 and c3 and c3_20 and c4)}
        verdict[fr] = v
        lines.append("\nDecision rule: " + ", ".join(f"{k} {'YES' if x else 'no'}" for k, x in v.items()))
    change = any(v["C1_sum_reversed"] or v["C2_late_sum_negative"] or v["C3_ceiling_gap_closed"] for v in verdict.values())
    complete = all(v["complete"] for v in verdict.values())
    res["verdict"] = {"by_framing": verdict, "horizon_changes_the_story": change, "complete": complete}
    lines.append(f"\n**Horizon changes the story (C1-C3, either framing): {'YES' if change else 'no'}"
                 f"{'' if complete else ' (incomplete: some contrasts lack worlds)'}**")
    (OUT / "stats_h60.json").write_text(json.dumps(res, indent=1, default=dict))
    (OUT / "stats_h60.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
