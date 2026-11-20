"""Per-run condition means for the sharing write-up and the arXiv tables. Writes results/multiagent/writeup_run_means.json.

For each framing, measure and condition: one value per repeat, the mean over the 8 pilot worlds of that repeat's
team measure; `mean` is the mean of those per-run values and `sd` their sample standard deviation, which is the
run-to-run wobble shown after the plus-minus sign in the main table.

    python3 paper/scripts/run_means_multiagent.py
Uses the loaders of stats_multiagent_reps.py, so the pilot-world restriction and the measures are the same.
"""
import collections
import importlib.util
import json
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("sr", HERE / "stats_multiagent_reps.py")
sr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sr)


def main():
    out = {}
    for suf, name in sr.FRAMINGS:
        for a in sr.ARMS:
            T = sr.teams(a + suf)
            worlds = {w for (w, _r) in T}
            for meas in ("best_peak", "sum_pct", "unique"):
                by_rep = collections.defaultdict(dict)
                for (w, rep), m in T.items():
                    by_rep[rep][w] = m[meas]
                runs = [st.mean(v[w] for w in worlds) for rep, v in sorted(by_rep.items()) if set(v) == worlds]
                out[f"{name}|{meas}|{a}"] = {"runs": runs, "mean": st.mean(runs),
                                             "sd": st.stdev(runs) if len(runs) > 1 else 0.0}
    (sr.OUT / "writeup_run_means.json").write_text(json.dumps(out, indent=1))
    print("wrote", sr.OUT / "writeup_run_means.json", len(out), "keys")


if __name__ == "__main__":
    main()
