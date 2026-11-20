#!/bin/bash
# Sixteen new alien-framing worlds for working alone and the periodic board (docs/PILOT_MULTIAGENT.md, addendum
# 2026-11-17). Start, or resume after any interruption, with:
#   setsid nohup bash scripts/run_multiagent_worlds24.sh >> results/multiagent/logs/worlds24_driver.log 2>&1 < /dev/null &
# Safe to start at any time and any number of times:
#   * detached from the terminal, so a dropped connection or a closed session does not stop it
#   * one copy only (lock); a second copy exits at once
#   * every finished episode is on disk and is skipped, so it continues at the first episode not yet recorded;
#     an episode cut off mid-way is redone from its first round
#   * each arm's dollar cap is read from results/multiagent/logs/w24_cap__<arm>.txt and enforced by the run script
#     before every episode, counting episodes in flight, so the cap cannot be passed
#   * ends by running the analysis fixed in the addendum (paper/scripts/stats_worlds24.py)
set -uo pipefail
cd "$(dirname "$0")/.."
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
MODEL=gpt-5.6-sol
LOGS=results/multiagent/logs
OFFSET=16; WORLDS=16; REPS=3
export LEM_WORKERS=${LEM_WORKERS:-4}
mkdir -p "$LOGS"
exec 9>"$LOGS/.worlds24_driver.lock"
flock -n 9 || { echo "$(date -u +%FT%TZ) worlds24: another copy is running"; exit 0; }
say() { echo "$(date -u +%FT%TZ) worlds24: $*"; }

have_new() {   # episodes recorded for this arm on the new worlds
  $PY - "$1" <<'PYEOF'
import json, pathlib, sys
sys.path.insert(0, ".")
from env.world_generator import load_world_set, world_id
arm = sys.argv[1]
new = {world_id(w) for w in load_world_set("data/worlds_main.json")["val"][16:32]}
f = pathlib.Path(f"results/multiagent/{arm}__gpt-5.6-sol.jsonl")
keys = {json.loads(l)["key"] for l in f.open() if l.strip() and json.loads(l)["world_id"] in new}
print(len(keys))
PYEOF
}

run_arm() {
  local name=$1 flags=$2 need=$3
  local spendf=results/multiagent/spend__${name}__${MODEL}.json capf=$LOGS/w24_cap__${name}.txt
  [ -f "$capf" ] || { say "$name: no cap file, not started"; return; }
  exec 8>"$LOGS/.w24_${name}.lock"
  flock -n 8 || { say "$name: another copy is running"; return; }
  local cap; cap=$(cat "$capf")
  for try in 1 2 3 4 5 6; do
    local have spent
    have=$(have_new "$name")
    [ "$have" -ge "$need" ] && { say "$name complete ($have episodes on the new worlds)"; return; }
    spent=$($PY -c "import json;print(json.load(open('$spendf'))['total'])")
    if awk -v s="$spent" -v c="$cap" 'BEGIN{exit !(s+0 >= c-0.5)}'; then
      say "$name stopped at its cap (\$$spent of \$$cap) with $have of $need episodes"; return
    fi
    say "$name attempt $try ($have of $need episodes, \$$spent of \$$cap, workers $LEM_WORKERS)"
    # shellcheck disable=SC2086
    $PY experiments/shared_world.py $flags --alien --model "$MODEL" --world-offset "$OFFSET" --worlds "$WORLDS" \
        --reps "$REPS" --cap "$cap" --workers "$LEM_WORKERS"
    sleep 15
  done
  say "$name gave up after 6 attempts"
}

say "start (offset $OFFSET, worlds $WORLDS, reps $REPS)"
run_arm solo_alien "--arm solo" $((WORLDS * 3 * REPS)) >> "$LOGS/w24_solo_alien.log" 2>&1 &
run_arm share_at6-11-16_alien "--arm share --share-at 6,11,16" $((WORLDS * REPS)) >> "$LOGS/w24_share_at6-11-16_alien.log" 2>&1 &
wait
say "runs finished; analysis"
$PY paper/scripts/stats_worlds24.py >> "$LOGS/worlds24_analysis.log" 2>&1 && say "analysis written" || say "analysis FAILED, see $LOGS/worlds24_analysis.log"
say "DONE"
