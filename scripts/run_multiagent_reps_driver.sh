#!/bin/bash
# Driver for the repeat runs (docs/PILOT_MULTIAGENT.md, addenda 2026-11-04/05). Start, or resume after any interruption, with:
#   setsid nohup bash scripts/run_multiagent_reps_driver.sh >> results/multiagent/logs/driver.log 2>&1 < /dev/null &
# It is safe to start at any time and any number of times:
#   * detached from the terminal, so a dropped connection or a closed session does not stop it
#   * one copy only (lock); a second copy exits at once
#   * every finished episode is on disk and is skipped, so it continues at the first episode not yet recorded.
#     An episode cut off mid-way is redone from its first round; that is at most one episode per arm.
#   * phase A: every arm completes repeat 1. Phase B: repeat 2 of six arms, paid from what is left under the caps.
#     The phase B caps are computed once, from recorded cost only, and stored; a restart reuses them.
#   * ends by running the analysis fixed in the addenda (paper/scripts/stats_multiagent_reps.py).
set -uo pipefail
cd "$(dirname "$0")/.."
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
LOGS=results/multiagent/logs
exec 9>"$LOGS/.reps_driver.lock"
flock -n 9 || { echo "$(date -u +%FT%TZ) driver: another copy is running"; exit 0; }
say() { echo "$(date -u +%FT%TZ) driver: $*"; }

A_ARMS="solo share share_from6 share_at6-11-16 solo_alien share_alien share_from6_alien share_at6-11-16_alien share_from3 share_from11 share_from16 share_protocol share_staggered share_from3_alien share_from11_alien share_from16_alien share_protocol_alien share_staggered_alien"
B_ARMS="solo solo_alien share share_alien share_at6-11-16 share_at6-11-16_alien"

todo() {   # arms of the list that still lack episodes for --reps $1 and have room under their cap
  local reps=$1; shift
  $PY - "$reps" "$@" <<'PYEOF'
import json, pathlib, sys
reps, arms = int(sys.argv[1]), sys.argv[2:]
R, L = pathlib.Path("results/multiagent"), pathlib.Path("results/multiagent/logs")
out = []
for a in arms:
    have = len({json.loads(l)["key"] for l in (R / f"{a}__gpt-5.6-sol.jsonl").open() if l.strip()})
    spent = json.loads((R / f"spend__{a}__gpt-5.6-sol.json").read_text())["total"]
    cap = float((L / f"rep_cap__{a}.txt").read_text())
    if have < 24 * reps and spent < cap - 0.5:
        out.append(a)
print(" ".join(out))
PYEOF
}

phase() {  # reps, arms...
  local reps=$1; shift
  for round in $(seq 1 12); do
    while pgrep -u "$USER" -f "experiments/shared_world.py" > /dev/null; do sleep 30; done
    local left; left=$(todo "$reps" "$@")
    [ -z "$left" ] && { say "reps=$reps: nothing left to run"; return 0; }
    say "reps=$reps round $round: running $left"
    # shellcheck disable=SC2086
    bash scripts/run_multiagent_repN.sh "$reps" $left >> "$LOGS/repN_master.log" 2>&1
    sleep 20
  done
  say "reps=$reps: gave up after 12 rounds, still left: $(todo "$reps" "$@")"
}

say "started on $(hostname)"
# shellcheck disable=SC2086
phase 2 $A_ARMS

if [ ! -f "$LOGS/phaseB_caps.json" ]; then
  $PY - <<'PYEOF'
import json, pathlib
R, L = pathlib.Path("results/multiagent"), pathlib.Path("results/multiagent/logs")
B = R / "backup_before_reps_2026-11-04"
ALLOWED, RESERVE = 133.80, 8.00            # addenda 2026-11-04/05; reserve for the unrecorded episodes of the first launch
arms18 = "solo share share_from6 share_at6-11-16 solo_alien share_alien share_from6_alien share_at6-11-16_alien share_from3 share_from11 share_from16 share_protocol share_staggered share_from3_alien share_from11_alien share_from16_alien share_protocol_alien share_staggered_alien".split()
spent = lambda a: json.loads((R / f"spend__{a}__gpt-5.6-sol.json").read_text())["total"]
before = lambda a: json.loads((B / f"spend__{a}__gpt-5.6-sol.json").read_text())["total"]
new = {a: spent(a) - before(a) for a in arms18}
pool = ALLOWED - RESERVE - sum(new.values())
alloc = {}
for group in (["solo", "solo_alien"], ["share", "share_alien"], ["share_at6-11-16", "share_at6-11-16_alien"]):
    need = {a: 1.08 * new[a] for a in group}          # a third run costs about what the second did, plus 8%
    give = min(pool, sum(need.values()))
    for a in group:
        alloc[a] = max(0.0, give * need[a] / sum(need.values()))
    pool -= give
for a in arms18:                                       # every arm's cap is now what it has spent, plus its phase B share
    (L / f"rep_cap__{a}.txt").write_text(f"{spent(a) + alloc.get(a, 0.0):.4f}\n")
json.dump({"new_spend_after_phase_A": new, "total_new": sum(new.values()), "allowed": ALLOWED, "reserve": RESERVE,
           "phase_B_allocation": alloc, "left_unallocated": pool}, open(L / "phaseB_caps.json", "w"), indent=1)
print("phase B allocation:", {k: round(v, 2) for k, v in alloc.items()}, "| unallocated", round(pool, 2))
PYEOF
  say "phase B caps written"
fi
# shellcheck disable=SC2086
phase 3 $B_ARMS

$PY paper/scripts/stats_multiagent_reps.py > "$LOGS/stats_reps_stdout.txt" 2>&1 && say "analysis written to results/multiagent/stats_reps.md" || say "analysis script failed, see $LOGS/stats_reps_stdout.txt"
$PY - <<'PYEOF'
import json, pathlib
R = pathlib.Path("results/multiagent"); B = R / "backup_before_reps_2026-11-04"
arms = [p.name[len("spend__"):-len("__gpt-5.6-sol.json")] for p in sorted(B.glob("spend__*__gpt-5.6-sol.json"))]
new = sum(json.loads((R / f"spend__{a}__gpt-5.6-sol.json").read_text())["total"] - json.loads((B / f"spend__{a}__gpt-5.6-sol.json").read_text())["total"] for a in arms)
print(f"recorded new spend ${new:.2f}; project total ${476.17 + new:.2f} of $610 (plus the unrecorded episodes of the first launch)")
PYEOF
say "DRIVER_DONE"
