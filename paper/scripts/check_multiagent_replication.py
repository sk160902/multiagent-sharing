"""Does the pilot's headline survive a second run of the same conditions?

Three arms were run twice: solo, share and share_protocol each have a second episode under
keys that already existed (docs/RESULTS.md, duplicate-row note). The two passes are the same
worlds, the same prompts and the same seeds, differing only in sampling, so splitting the log
on how many times a key has been seen gives one free replication of the main comparison.

This matters because the protocol search already found that single runs of these arms swing
by up to 23 points on earnings (docs/RESULTS.md), and because the write-up's headline depends
on which measure is read. Each comparison is paired by world and tested by enumerating all
2^n sign flips of the paired differences.

    .venv/bin/python paper/scripts/check_multiagent_replication.py

Prints a table and writes results/multiagent/replication.md. Reads only; no run is launched.
"""
from __future__ import annotations

import collections
import itertools
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "paper" / "scripts"))

from table_multiagent_dvs import MODEL, OUT, measures  # noqa: E402

ARMS = ("solo", "share", "share_protocol")
TEAM = 3
COMPARISONS = [
    ("share_protocol", "share", "unique", "does telling agents to stay different restore the search"),
    ("share", "solo", "unique", "does an open board narrow the search"),
    ("share", "solo", "sum_pct", "does an open board raise what the team earns"),
    ("solo", "share", "best_peak", "does working alone reach a better single round"),
    ("share_protocol", "solo", "sum_pct", "does the protocol earn more than working alone"),
]


def passes(arm):
    """pass number -> world id -> the episodes of that world's team on that pass.

    The nth time an episode key appears in the log is the nth pass. A pass keeps a world
    only when all three of its agents are present on that pass.
    """
    seen, out = collections.Counter(), collections.defaultdict(lambda: collections.defaultdict(list))
    for line in (OUT / f"{arm}__{MODEL}.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        seen[r["key"]] += 1
        out[seen[r["key"]]][r["world_id"]].append(
            {"gmax": r["metrics"]["gmax"], "profits": r["profits"], "actions": r["actions"]})
    return {n: {w: eps for w, eps in by_world.items() if len(eps) == TEAM}
            for n, by_world in out.items()}


def sign_flip(diffs):
    """Two-sided p from enumerating every sign assignment of the paired differences."""
    obs = abs(sum(diffs))
    hits = sum(1 for sg in itertools.product((1, -1), repeat=len(diffs))
               if abs(sum(s * d for s, d in zip(sg, diffs))) >= obs - 1e-9)
    return hits / 2 ** len(diffs)


def main():
    p = {a: passes(a) for a in ARMS}
    rounds = sorted({n for a in ARMS for n in p[a]})
    lines = ["# Does the shared-workspace headline replicate?", "",
             "Pass 1 and pass 2 are the two independent runs of the same worlds, prompts and seeds "
             "found in the logs. Each row is paired by world; p enumerates every sign flip.", ""]
    header = "| comparison | measure | " + " | ".join(f"pass {n}" for n in rounds) + " |"
    lines += [header, "|" + "---|" * (len(rounds) + 2)]

    print(f"{'comparison':36s} {'measure':10s} " + "".join(f"{'pass '+str(n):>26s}" for n in rounds))
    for a, b, m, question in COMPARISONS:
        cells, show = [], []
        for n in rounds:
            worlds = sorted(set(p[a].get(n, {})) & set(p[b].get(n, {})))
            if len(worlds) < 3:
                cells.append("not run twice")
                show.append(f"{'not run twice':>26s}")
                continue
            A = {w: measures(p[a][n][w]) for w in worlds}
            B = {w: measures(p[b][n][w]) for w in worlds}
            d = [A[w][m] - B[w][m] for w in worlds]
            better = sum(1 for x in d if x > 0)
            txt = f"{statistics.mean(d):+.1f}, {better}/{len(d)} worlds, p={sign_flip(d):.3f}"
            cells.append(txt)
            show.append(f"{txt:>26s}")
        print(f"{a + ' - ' + b:36s} {m:10s} " + "".join(show))
        lines.append(f"| {a} - {b} <br>*{question}* | {m} | " + " | ".join(cells) + " |")

    lines += ["", "Worlds complete on each pass:", ""]
    for a in ARMS:
        lines.append(f"- {a}: " + ", ".join(f"pass {n} {len(p[a][n])} worlds" for n in sorted(p[a])))
    (OUT / "replication.md").write_text("\n".join(lines) + "\n")
    print()
    for a in ARMS:
        print(f"  {a:16s} " + "  ".join(f"pass {n}: {len(p[a][n])} worlds" for n in sorted(p[a])))
    print(f"\nwrote {OUT / 'replication.md'}")


if __name__ == "__main__":
    main()
