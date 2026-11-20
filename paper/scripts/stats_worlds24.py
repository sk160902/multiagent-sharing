"""Periodic board against working alone in the alien framing on 24 worlds (8 pilot + 16 new).

Plan fixed in docs/PILOT_MULTIAGENT.md, addendum 2026-11-17, before the new worlds were run.
Unit: the world. A world's value for a condition is the mean over its completed keyed runs (three per world, pilot
and new alike). Contrast: share_at6-11-16_alien minus solo_alien, paired within world, on best_peak, sum_pct,
unique and reached_best. Exact two-sided sign-flip test over the worlds and a 95% t interval. Reported for the 16 new
worlds alone, the 8 pilot worlds alone, and all 24 together. The pre-specified primary result is best_peak on all 24.

    .venv/bin/python paper/scripts/stats_worlds24.py            # alien framing (default)
    .venv/bin/python paper/scripts/stats_worlds24.py lemonade   # lemonade framing (addendum 2026-11-19)
Writes results/multiagent/stats_worlds24.json and stats_worlds24.md for the alien framing, and
stats_worlds24_lemonade.{json,md} for the lemonade framing. Same design, same analysis, same worlds.
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
FRAMING = sys.argv[1] if len(sys.argv) > 1 else "alien"
assert FRAMING in ("alien", "lemonade"), FRAMING
_SUF = "_alien" if FRAMING == "alien" else ""
SOLO, ARM = "solo" + _SUF, "share_at6-11-16" + _SUF
_OUTNAME = "stats_worlds24" if FRAMING == "alien" else "stats_worlds24_lemonade"
MEASURES = ["best_peak", "sum_pct", "unique", "reached_best"]
TCRIT = {7: 2.365, 15: 2.131, 23: 2.069}
ROUNDS = 20


def load(arm):
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
    by = collections.defaultdict(list)
    for r in load(arm):
        by[(r["world_id"], int(str(r["repeat"]).split(".")[0]))].append(r)
    return {k: measures(v) for k, v in by.items() if len(v) == 3}


def world_values(T, meas):
    out = collections.defaultdict(list)
    for (w, rep), m in T.items():
        out[w].append(m[meas])
    return {w: st.mean(v) for w, v in out.items()}


def _signed_sums(v):
    """All 2^len(v) sums of +-v_i, built by doubling (no 2^n x n matrix)."""
    s = np.zeros(1)
    for x in v:
        s = np.concatenate([s + x, s - x])
    return s


def perm_p(d):
    """Exact two-sided sign-flip p over n worlds.

    Counts the sign patterns whose |sum| reaches the observed |sum| by meet-in-the-middle: the 2^(n/2) signed
    sums of each half are formed, the second half's are sorted, and for every first-half value the number of
    partners above obs - a and below -obs - a is read off with searchsorted. Same count as enumerating all 2^n
    patterns, which this function did until 2026-11-20 with a 2^24 x 24 matrix per test; on a shared machine that
    took minutes per call, this takes milliseconds. Ties within 1e-9 count as reaching the observed value, as before."""
    d = np.asarray(d, dtype=float)
    n, obs = len(d), abs(d.sum())
    a, b = _signed_sums(d[: n // 2]), np.sort(_signed_sums(d[n // 2:]))
    eps = 1e-9
    hi = len(b) - np.searchsorted(b, obs - eps - a, side="left")        # b >= obs - a  (sum >= obs)
    lo = np.searchsorted(b, -obs + eps - a, side="right")              # b <= -obs - a (sum <= -obs)
    count = int(hi.sum() + lo.sum())
    if obs <= eps:                                                     # the two sets coincide when obs is 0
        count = 2 ** n
    return count / 2 ** n


def summ(d):
    n, m = len(d), sum(d) / len(d)
    tc = TCRIT.get(n - 1, 2.0)
    h = tc * st.stdev(d) / math.sqrt(n) if n > 1 else float("nan")
    return {"n": n, "mean": m, "lo": m - h, "hi": m + h, "p": perm_p(d),
            "up": sum(x > 1e-9 for x in d), "down": sum(x < -1e-9 for x in d)}


def main():
    val = load_world_set(ROOT / "data" / "worlds_main.json")["val"]
    pilot = [world_id(w) for w in val[:8]]
    new = [world_id(w) for w in val[16:32]]
    Ts, Ta = teams(SOLO), teams(ARM)
    res = {"runs": {SOLO: collections.Counter(w for w, _ in Ts), ARM: collections.Counter(w for w, _ in Ta)}}
    lines = [f"# Periodic board minus working alone, {FRAMING} framing, paired over worlds\n"]
    for meas in MEASURES:
        s, a = world_values(Ts, meas), world_values(Ta, meas)
        for label, ws in (("new16", new), ("pilot8", pilot), ("all24", pilot + new)):
            have = [w for w in ws if w in s and w in a]
            if len(have) < 2:
                lines.append(f"| {meas} | {label} | not enough complete worlds ({len(have)}) |")
                continue
            r = summ([a[w] - s[w] for w in have])
            r["solo_mean"], r["arm_mean"] = st.mean(s[w] for w in have), st.mean(a[w] for w in have)
            res[f"{meas}|{label}"] = r
            lines.append(f"| {meas} | {label} | n={r['n']} | solo {r['solo_mean']:.1f} | periodic {r['arm_mean']:.1f} | "
                         f"diff {r['mean']:+.1f} [{r['lo']:+.1f}, {r['hi']:+.1f}] p={r['p']:.3f} "
                         f"({r['up']} up, {r['down']} down) |")
    (OUT / f"{_OUTNAME}.json").write_text(json.dumps(res, indent=1, default=dict))
    (OUT / f"{_OUTNAME}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
