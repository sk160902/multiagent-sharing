"""Tables for the arXiv write-up of the shared-board pilot (arxiv/lemonade_sharing_arxiv/tables/*.tex).

Reads only what the analysis scripts already wrote:
  results/multiagent/writeup_numbers.json    (paper/scripts/writeup_numbers_multiagent.py)
  results/multiagent/writeup_run_means.json  (per-run condition means, SD across runs)
  results/multiagent/stats_reps.json         (paper/scripts/stats_multiagent_reps.py)
No number is typed by hand. Run from the repo root:
  .venv/bin/python paper/scripts/arxiv_sharing_tables.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "multiagent"
OUT = ROOT / "arxiv" / "lemonade_sharing_arxiv" / "tables"
OUT.mkdir(parents=True, exist_ok=True)

W = json.loads((RES / "writeup_numbers.json").read_text())
R = json.loads((RES / "writeup_run_means.json").read_text())
S = json.loads((RES / "stats_reps.json").read_text())

ARMS = ["solo", "share", "share_from3", "share_from6", "share_from11", "share_from16",
        "share_at6-11-16", "share_protocol", "share_staggered"]
NAME = {
    "solo": "Working alone",
    "share": "Sharing all along",
    "share_from3": "Sharing after 2 private rounds",
    "share_from6": "Sharing after 5 private rounds",
    "share_from11": "Sharing after 10 private rounds",
    "share_from16": "Sharing after 15 private rounds",
    "share_at6-11-16": "Sharing at rounds 6, 11 and 16 only",
    "share_protocol": "Sharing, told to stay different",
    "share_staggered": "One agent at a time",
}
MEAS = {"best_peak": "Max", "sum_pct": "Cumulative", "unique": "Distinct setups"}
FRAMES = ["lemonade", "alien"]


def f1(x: float) -> str:
    return f"{x:.1f}"


def write(name: str, body: str) -> None:
    (OUT / name).write_text(body)
    print("wrote", OUT / name)


# ---------------------------------------------------------------- main table: condition means ± SD across runs
rows = []
for a in ARMS:
    cells = [NAME[a], str(len(R[f"lemonade|best_peak|{a}"]["runs"]))]
    for fr in FRAMES:
        for m in MEAS:
            r = R[f"{fr}|{m}|{a}"]
            cells.append(f"{f1(r['mean'])} $\\pm$ {f1(r['sd'])}")
    rows.append(" & ".join(cells) + r" \\")
write("tab_main.tex", "\n".join([
    r"\begin{tabular}{l c ccc ccc}", r"\toprule",
    r" & & \multicolumn{3}{c}{Lemonade framing} & \multicolumn{3}{c}{Alien framing} \\",
    r"\cmidrule(lr){3-5} \cmidrule(lr){6-8}",
    r"Condition & Runs & Max & Cumulative & Distinct & Max & Cumulative & Distinct \\",
    r"\midrule", *rows, r"\bottomrule", r"\end{tabular}"]))

# ---------------------------------------------------------------- pooled contrasts: all sharing minus solo
def cell(block: str, key: str, unit: str) -> str:
    t = S[block][key]
    return (f"{t['mean']:+.1f}{unit} [{t['lo']:+.1f}, {t['hi']:+.1f}] & {t['p']:.3f}")

rows = []
for m, unit in (("best_peak", ""), ("sum_pct", ""), ("unique", "")):
    for fr in ("lemonade", "alien", "both"):
        key = f"{fr}|{m}|all_sharing"
        rows.append(" & ".join([
            MEAS[m] if fr == "lemonade" else "",
            fr,
            cell("first_run_only", key, unit),
            cell("new_runs_only", key, unit),
            cell("all_runs", key, unit),
        ]) + r" \\")
    rows.append(r"\addlinespace")
write("tab_contrasts.tex", "\n".join([
    r"\begin{tabular}{l l rc rc rc}", r"\toprule",
    r" & & \multicolumn{2}{c}{First run} & \multicolumn{2}{c}{Repeat runs only} & \multicolumn{2}{c}{All runs} \\",
    r"\cmidrule(lr){3-4} \cmidrule(lr){5-6} \cmidrule(lr){7-8}",
    r"Measure & Framing & Difference [95\% CI] & $p$ & Difference [95\% CI] & $p$ & Difference [95\% CI] & $p$ \\",
    r"\midrule", *rows[:-1], r"\bottomrule", r"\end{tabular}"]))

# ---------------------------------------------------------------- per-condition contrasts, all runs
rows = []
for a in ARMS[1:]:
    cells = [NAME[a]]
    for fr in FRAMES:
        for m in MEAS:
            t = S["all_runs"][f"{fr}|{m}|{a}"]
            star = r"$^{\ast}$" if t["p"] < 0.05 else ""
            cells.append(f"{t['mean']:+.1f}{star}")
    rows.append(" & ".join(cells) + r" \\")
write("tab_percondition.tex", "\n".join([
    r"\begin{tabular}{l ccc ccc}", r"\toprule",
    r" & \multicolumn{3}{c}{Lemonade framing} & \multicolumn{3}{c}{Alien framing} \\",
    r"\cmidrule(lr){2-4} \cmidrule(lr){5-7}",
    r"Difference from working alone & Max & Cumulative & Distinct & Max & Cumulative & Distinct \\",
    r"\midrule", *rows, r"\bottomrule", r"\end{tabular}"]))

# ---------------------------------------------------------------- reached the best location
rows = []
for a in ARMS:
    cells = [NAME[a]]
    for fr in FRAMES:
        n, d = W["reached"][f"{fr}|{a}"]
        cells.append(f"{n} of {d}")
        cells.append(f"{100 * n / d:.0f}\\%")
    rows.append(" & ".join(cells) + r" \\")
write("tab_reached.tex", "\n".join([
    r"\begin{tabular}{l cc cc}", r"\toprule",
    r" & \multicolumn{2}{c}{Lemonade framing} & \multicolumn{2}{c}{Alien framing} \\",
    r"\cmidrule(lr){2-3} \cmidrule(lr){4-5}",
    r"Condition & World-runs & Share & World-runs & Share \\",
    r"\midrule", *rows, r"\bottomrule", r"\end{tabular}"]))

# ---------------------------------------------------------------- per-world appendix tables
for fr in FRAMES:
    for m in MEAS:
        rows = []
        for a in ARMS:
            t = W["tables"][f"{fr}|{m}|{a}"]
            rows.append(" & ".join([NAME[a], *[f1(x) for x in t["by_world"]], f1(t["mean"])]) + r" \\")
        write(f"tab_world_{fr}_{m}.tex", "\n".join([
            r"\begin{tabular}{l rrrrrrrr r}", r"\toprule",
            r"Condition & W1 & W2 & W3 & W4 & W5 & W6 & W7 & W8 & Mean \\",
            r"\midrule", *rows, r"\bottomrule", r"\end{tabular}"]))

# ---------------------------------------------------------------- first run vs repeats agreement
agree = W["agree"]
rows = []
for fr in FRAMES:
    for m in MEAS:
        g = agree[f"{fr}|{m}"]
        rows.append(f"{fr} & {MEAS[m]} & {g['same_side']} of {g['of']} \\\\")
write("tab_agree.tex", "\n".join([
    r"\begin{tabular}{l l c}", r"\toprule",
    r"Framing & Measure & Conditions on the same side of working alone \\",
    r"\midrule", *rows, r"\bottomrule", r"\end{tabular}"]))

# ---------------------------------------------------------------- numbers macros used in the prose
own = W["own_best"]
macros = {
    "NWorlds": "8", "NAgents": "3", "NRounds": "20", "NAttempts": "60",
    "LemSoloMax": f1(R["lemonade|best_peak|solo"]["mean"]),
    "LemShareMax": f1(R["lemonade|best_peak|share"]["mean"]),
    "AliSoloMax": f1(R["alien|best_peak|solo"]["mean"]),
    "AliShareMax": f1(R["alien|best_peak|share"]["mean"]),
    "LemSoloSum": f1(R["lemonade|sum_pct|solo"]["mean"]),
    "LemShareSum": f1(R["lemonade|sum_pct|share"]["mean"]),
    "AliSoloSum": f1(R["alien|sum_pct|solo"]["mean"]),
    "AliShareSum": f1(R["alien|sum_pct|share"]["mean"]),
    "LemSoloUniq": f1(R["lemonade|unique|solo"]["mean"]),
    "LemShareUniq": f1(R["lemonade|unique|share"]["mean"]),
    "AliSoloUniq": f1(R["alien|unique|solo"]["mean"]),
    "AliShareUniq": f1(R["alien|unique|share"]["mean"]),
    "AliPeriodicMax": f1(R["alien|best_peak|share_at6-11-16"]["mean"]),
    "AliProtocolMax": f1(R["alien|best_peak|share_protocol"]["mean"]),
    "LemPeriodicMax": f1(R["lemonade|best_peak|share_at6-11-16"]["mean"]),
    "LemProtocolMax": f1(R["lemonade|best_peak|share_protocol"]["mean"]),
    "LemStaggerSum": f1(R["lemonade|sum_pct|share_staggered"]["mean"]),
    "AliProtocolSum": f1(R["alien|sum_pct|share_protocol"]["mean"]),
    "OwnBestLem": f"{own['lemonade']['all_sharing_minus_solo']['mean']:+.1f}",
    "OwnBestAli": f"{own['alien']['all_sharing_minus_solo']['mean']:+.1f}",
    "SameLocSoloLem": f"{W['same_location']['lemonade|solo']:.0f}",
    "SameLocShareLem": f"{W['same_location']['lemonade|share']:.0f}",
    "SameLocSoloAli": f"{W['same_location']['alien|solo']:.0f}",
    "SameLocShareAli": f"{W['same_location']['alien|share']:.0f}",
}
for fr, tag in (("lemonade", "Lem"), ("alien", "Ali"), ("both", "Both")):
    for m, mt in (("best_peak", "Max"), ("sum_pct", "Sum"), ("unique", "Uniq")):
        t = S["all_runs"][f"{fr}|{m}|all_sharing"]
        macros[f"All{tag}{mt}"] = f"{t['mean']:+.1f}"
        macros[f"All{tag}{mt}Lo"] = f"{t['lo']:+.1f}"
        macros[f"All{tag}{mt}Hi"] = f"{t['hi']:+.1f}"
        macros[f"All{tag}{mt}P"] = f"{t['p']:.3f}"
t = S["all_runs"]["alien|best_peak|share_at6-11-16"]
macros.update({"AliPeriodicDiff": f"{t['mean']:+.1f}", "AliPeriodicLo": f"{t['lo']:+.1f}",
               "AliPeriodicHi": f"{t['hi']:+.1f}", "AliPeriodicP": f"{t['p']:.2f}"})
t = S["all_runs"]["alien|best_peak|share_protocol"]
macros.update({"AliProtocolDiff": f"{t['mean']:+.1f}", "AliProtocolP": f"{t['p']:.2f}"})
n, d = W["reached"]["alien|share_at6-11-16"]; macros["AliPeriodicReached"] = f"{n} of {d}"
n, d = W["reached"]["alien|solo"]; macros["AliSoloReached"] = f"{n} of {d}"
n, d = W["reached"]["lemonade|solo"]; macros["LemSoloReached"] = f"{n} of {d}"
n, d = W["reached"]["lemonade|share"]; macros["LemShareReached"] = f"{n} of {d}"
n, d = W["reached"]["alien|share"]; macros["AliShareReached"] = f"{n} of {d}"
same = sum(agree[k]["same_side"] for k in agree); of = sum(agree[k]["of"] for k in agree)
macros["AgreeSame"] = str(same); macros["AgreeOf"] = str(of)

# ---------------------------------------------------------------- 24-world follow-ups (stats_worlds24*.json), if present
# Alien framing: macros W<New|All><Max|Sum|Uniq|Reached>...; lemonade framing (addendum 2026-11-19): WL<...>.
W24 = {}
for fr, fname, prefix in (("alien", "stats_worlds24.json", "W"), ("lemonade", "stats_worlds24_lemonade.json", "WL")):
    f = RES / fname
    if not f.exists():
        continue
    S24 = json.loads(f.read_text())
    W24[fr] = S24
    for meas, tag in (("best_peak", "Max"), ("sum_pct", "Sum"), ("unique", "Uniq"), ("reached_best", "Reached")):
        for label, lt in (("new16", "New"), ("all24", "All"), ("pilot8", "Pilot")):
            t = S24.get(f"{meas}|{label}")
            if not t:
                continue
            k = f"{prefix}{lt}{tag}"
            macros[k] = f"{t['mean']:+.1f}"
            macros[k + "Lo"] = f"{t['lo']:+.1f}"
            macros[k + "Hi"] = f"{t['hi']:+.1f}"
            macros[k + "P"] = f"={t['p']:.3f}" if t["p"] >= 0.001 else "<0.001"   # used as $p\W...P$
            macros[k + "Down"] = str(t["down"])
            macros[k + "Up"] = str(t["up"])
            macros[k + "Solo"] = f"{t['solo_mean']:.1f}"
            macros[k + "Arm"] = f"{t['arm_mean']:.1f}"
            macros[k + "N"] = str(t["n"])
if W24:
    rows = []
    for fr, fname in (("lemonade", "Lemonade"), ("alien", "Alien")):
        if fr not in W24:
            continue
        S24 = W24[fr]
        for meas, name in (("best_peak", "Max"), ("sum_pct", "Cumulative"), ("unique", "Distinct setups"),
                           ("reached_best", "Reached best location (\\%)")):
            cells = [fname if meas == "best_peak" else "", name]
            for label in ("new16", "pilot8", "all24"):
                t = S24[f"{meas}|{label}"]
                p = f"{t['p']:.3f}" if t["p"] >= 0.001 else "$<$0.001"
                cells.append(f"{t['mean']:+.1f} [{t['lo']:+.1f}, {t['hi']:+.1f}] & {p}")
            rows.append(" & ".join(cells) + r" \\")
        rows.append(r"\addlinespace")
    write("tab_worlds24.tex", "\n".join([
        r"\begin{tabular}{l l rc rc rc}", r"\toprule",
        r" & & \multicolumn{2}{c}{16 new worlds} & \multicolumn{2}{c}{8 pilot worlds} & \multicolumn{2}{c}{All 24 worlds} \\",
        r"\cmidrule(lr){3-4} \cmidrule(lr){5-6} \cmidrule(lr){7-8}",
        r"Framing & Measure & Difference [95\% CI] & $p$ & Difference [95\% CI] & $p$ & Difference [95\% CI] & $p$ \\",
        r"\midrule", *rows[:-1], r"\bottomrule", r"\end{tabular}"]))
# ---------------------------------------------------------------- Claude Opus 5.5 replication (stats_claude.json), if present
cl = RES / "stats_claude.json"
if cl.exists():
    SC = json.loads(cl.read_text())
    MT = {"best_peak": "Max", "sum_pct": "Sum", "unique": "Uniq", "reached_best": "Reached"}
    for model, mtag in (("claude-opus-5-5", "C"), ("gpt-5.6-sol", "G")):
        for fr, ft in (("lemonade", "Lem"), ("alien", "Ali")):
            for meas, tag in MT.items():
                for arm, at in (("share", "Share"), ("share_at6-11-16", "Periodic")):
                    t = SC.get(f"{model}|{fr}|{meas}|{arm}")
                    if not t:
                        continue
                    k = f"{mtag}{ft}{tag}{at}"
                    macros[k] = f"{t['mean']:+.1f}"
                    macros[k + "Lo"] = f"{t['lo']:+.1f}"
                    macros[k + "Hi"] = f"{t['hi']:+.1f}"
                    macros[k + "P"] = f"={t['p']:.3f}" if t["p"] >= 0.001 else "<0.001"
                    macros[k + "Solo"] = f"{t['solo_mean']:.1f}"
                    macros[k + "Arm"] = f"{t['arm_mean']:.1f}"
                    macros[k + "Up"] = str(t["up"])
                    macros[k + "Down"] = str(t["down"])
    rows = []
    for fr, fname in (("lemonade", "Lemonade"), ("alien", "Alien")):
        for meas, name in (("best_peak", "Max"), ("sum_pct", "Cumulative"), ("unique", "Distinct setups")):
            cells = [fname if meas == "best_peak" else "", name]
            for model in ("claude-opus-5-5", "gpt-5.6-sol"):
                for arm in ("share", "share_at6-11-16"):
                    t = SC[f"{model}|{fr}|{meas}|{arm}"]
                    star = r"$^{\ast}$" if t["p"] < 0.05 else ""
                    cells.append(f"{t['mean']:+.1f}{star} [{t['lo']:+.1f}, {t['hi']:+.1f}]")
            rows.append(" & ".join(cells) + r" \\")
        rows.append(r"\addlinespace")
    write("tab_claude.tex", "\n".join([
        r"\begin{tabular}{l l cc cc}", r"\toprule",
        r" & & \multicolumn{2}{c}{Claude Opus 5.5} & \multicolumn{2}{c}{GPT-5.6} \\",
        r"\cmidrule(lr){3-4} \cmidrule(lr){5-6}",
        r"Framing & Measure & Sharing all along & Sharing at 6, 11, 16 & Sharing all along & Sharing at 6, 11, 16 \\",
        r"\midrule", *rows[:-1], r"\bottomrule", r"\end{tabular}"]))

# ---------------------------------------------------------------- 60-round games (stats_h60.json), if present
h60 = RES / "stats_h60.json"
if h60.exists():
    SH = json.loads(h60.read_text())
    MT = {"best_peak": "Max", "sum_pct": "Sum", "unique": "Uniq", "reached_best": "Reached"}
    WIN = {"20-round game": "Game", "rounds 1-60": "Full", "rounds 21-60": "Late", "rounds 1-20 of 60": "Early"}
    for fr, ft in (("lemonade", "Lem"), ("alien", "Ali")):
        for win, wt in WIN.items():
            for meas, tag in MT.items():
                t = SH.get(f"{fr}|{win}|{meas}")
                if not t:
                    continue
                k = f"H{ft}{tag}{wt}"
                macros[k] = f"{t['mean']:+.1f}"
                macros[k + "Lo"] = f"{t['lo']:+.1f}"
                macros[k + "Hi"] = f"{t['hi']:+.1f}"
                macros[k + "P"] = f"={t['p']:.3f}" if t["p"] >= 0.001 else "<0.001"
                macros[k + "Solo"] = f"{t['b_mean']:.1f}"
                macros[k + "Arm"] = f"{t['a_mean']:.1f}"
                macros[k + "Up"] = str(t["up"])
                macros[k + "Down"] = str(t["down"])
        # early play: the first 20 rounds of the 60-round game minus the 20-round game, per arm
        for arm, at in (("solo", "Solo"), ("share", "Share")):
            for meas, tag in (("best_peak", "Max"), ("sum_pct", "Sum"), ("unique", "Uniq")):
                t = SH.get(f"{fr}|early|{arm}|{meas}")
                if not t:
                    continue
                k = f"E{ft}{at}{tag}"
                macros[k] = f"{t['mean']:+.1f}"
                macros[k + "Lo"] = f"{t['lo']:+.1f}"
                macros[k + "Hi"] = f"{t['hi']:+.1f}"
                macros[k + "P"] = f"={t['p']:.3f}" if t["p"] >= 0.001 else "<0.001"
                macros[k + "Hsixty"] = f"{t['a_mean']:.1f}"
                macros[k + "Htwenty"] = f"{t['b_mean']:.1f}"
    rows = []
    for fr, fname in (("lemonade", "Lemonade"), ("alien", "Alien")):
        for meas, name in (("best_peak", "Max"), ("sum_pct", "Cumulative"), ("unique", "Distinct setups"),
                           ("reached_best", "Reached best location")):
            cells = [fname if meas == "best_peak" else "", name]
            for win in ("20-round game", "rounds 1-60", "rounds 21-60"):
                t = SH[f"{fr}|{win}|{meas}"]
                star = r"$^{\ast}$" if t["p"] < 0.05 else ""
                cells.append(f"{t['mean']:+.1f}{star} [{t['lo']:+.1f}, {t['hi']:+.1f}]")
            rows.append(" & ".join(cells) + r" \\")
        rows.append(r"\addlinespace")
    write("tab_h60.tex", "\n".join([
        r"\begin{tabular}{l l c cc}", r"\toprule",
        r" & & 20-round game & \multicolumn{2}{c}{60-round game} \\",
        r"\cmidrule(lr){3-3} \cmidrule(lr){4-5}",
        r"Framing & Measure & rounds 1--20 & rounds 1--60 & rounds 21--60 \\",
        r"\midrule", *rows[:-1], r"\bottomrule", r"\end{tabular}"]))

lines = [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in macros.items()]
write("numbers.tex", "% GENERATED by paper/scripts/arxiv_sharing_tables.py; do not edit.\n" + "\n".join(lines) + "\n")
