"""Every number the sharing write-up quotes, from the combined runs. Writes results/multiagent/writeup_numbers.json.

    .venv/bin/python paper/scripts/writeup_numbers_multiagent.py
Uses the loaders and the tests of stats_multiagent_reps.py, so the write-up and the pre-specified analysis agree.
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
OUT = sr.OUT
ORDER = ["solo", "share", "share_from3", "share_from6", "share_from11", "share_from16", "share_at6-11-16",
         "share_protocol", "share_staggered"]


def same_location(arm):
    """Share of rounds 6 to 20 in which all three agents of a team are at one location, averaged over teams."""
    by = collections.defaultdict(list)
    for r in pilot_rows(arm):
        by[(r["world_id"], str(r["repeat"]).split(".")[0])].append([a["location"] for a in r["actions"][:20]])
    return st.mean(100 * st.mean(len({a[t] for a in ag}) == 1 for t in range(5, 20)) for ag in by.values() if len(ag) == 3)


def pilot_rows(arm):
    """Episodes of the 8 pilot worlds at 20 rounds, the same restriction stats_multiagent_reps.teams applies."""
    return [r for r in sr.load(arm) if r["world_id"] in sr.PILOT and r.get("horizon", 20) == sr.ROUNDS]


def own_best(arm):
    """world -> each agent's own best round as % of the optimum, averaged over agents and runs."""
    by = collections.defaultdict(list)
    for r in pilot_rows(arm):
        by[r["world_id"]].append(100 * max(r["profits"][:20]) / r["metrics"]["gmax"])
    return {w: st.mean(v) for w, v in by.items()}


def main():
    stats = json.loads((OUT / "stats_reps.json").read_text())
    T = {a + suf: sr.teams(a + suf) for suf, _ in sr.FRAMINGS for a in ORDER}
    worlds = sorted({w for (w, _r) in T["solo"]})
    out = {"worlds": worlds, "tables": {}, "runs": {}, "reached": {}, "same_location": {}, "own_best": {}, "agree": {}}
    for suf, name in sr.FRAMINGS:
        for a in ORDER:
            t = T[a + suf]
            out["runs"][f"{name}|{a}"] = len(t) // 8
            flags = [m["best_peak"] > 60 for m in t.values()]
            out["reached"][f"{name}|{a}"] = [sum(flags), len(flags)]
            for meas in ("best_peak", "sum_pct", "unique"):
                v = sr.world_values(T, a + suf, meas, {0, 1, 2})
                out["tables"][f"{name}|{meas}|{a}"] = {"by_world": [v[w] for w in worlds], "mean": st.mean(v.values())}
        for a in ("solo", "share", "share_from6", "share_from16"):
            out["same_location"][f"{name}|{a}"] = same_location(a + suf)
        solo = own_best("solo" + suf)
        arms = {a: own_best(a + suf) for a in ORDER[1:]}
        d = [st.mean(arms[a][w] for a in arms) - solo[w] for w in worlds]
        out["own_best"][name] = {"solo": st.mean(solo.values()), "share": st.mean(arms["share"].values()), "all_sharing_minus_solo": sr.summ(d)}
    # first run against the new runs: is each condition on the same side of working alone both times
    for meas in ("best_peak", "sum_pct", "unique"):
        for name in ("lemonade", "alien"):
            rows = {a: stats["first_vs_new"][f"{name}|{meas}|{a}"] for a in ORDER[1:]}
            out["agree"][f"{name}|{meas}"] = {"same_side": sum(r["same_side"] for r in rows.values()), "of": len(rows),
                                             "rows": {a: [round(r["first"], 1), round(r["new"], 1), r["same_side"]] for a, r in rows.items()}}
    (OUT / "writeup_numbers.json").write_text(json.dumps(out, indent=1))
    for k, v in out["agree"].items():
        print(k, f"{v['same_side']} of {v['of']} on the same side", {a: r for a, r in v["rows"].items() if not r[2]})
    print("same location:", {k: round(v) for k, v in out["same_location"].items()})
    print("own best:", {k: (round(v["solo"], 1), round(v["share"], 1), round(v["all_sharing_minus_solo"]["mean"], 1), round(v["all_sharing_minus_solo"]["p"], 3)) for k, v in out["own_best"].items()})
    print("reached best location, runs:", out["reached"])
    for name in ("lemonade", "alien"):
        for meas in ("best_peak", "sum_pct", "unique"):
            print(name, meas, {a: round(out["tables"][f"{name}|{meas}|{a}"]["mean"], 1) for a in ORDER})


if __name__ == "__main__":
    main()
