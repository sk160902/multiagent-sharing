#!/bin/bash
# Sixteen new lemonade-framing worlds for working alone and the periodic board (docs/PILOT_MULTIAGENT.md, addendum
# 2026-11-19, lemonade 24 worlds), mirroring scripts/run_multiagent_worlds24.sh for the alien framing. Start, or resume
# after any interruption, with:
#   setsid nohup bash scripts/run_multiagent_worlds24_lemonade.sh >> results/multiagent/logs/w24lem_driver.log 2>&1 < /dev/null &
# Safe to start at any time and any number of times: detached, one copy only (lock), every recorded episode is skipped,
# each arm's dollar cap is read from results/multiagent/logs/w24lem_cap__<arm>.txt (the arm's spend-file total plus its
# allowance) and enforced per episode by the run script, episodes in flight counted; ends by running the analysis fixed
# in the addendum (paper/scripts/stats_worlds24.py lemonade).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
MODEL=gpt-5.6-sol
LOGS=results/multiagent/logs
OFFSET=16; WORLDS=16; REPS=3
export LEM_WORKERS=${LEM_WORKERS:-4}
mkdir -p "$LOGS"
exec 9>"$LOGS/.w24lem_driver.lock"
flock -n 9 || { echo "$(date -u +%FT%TZ) w24lem: another copy is running"; exit 0; }
say() { echo "$(date -u +%FT%TZ) w24lem: $*"; }

have_new() {   # episodes recorded for this arm on the new worlds (val[16:32])
  $PY scripts/count_new_worlds.py "$1" "$MODEL"
}

run_arm() {
  local name=$1 flags=$2 need=$3
  local spendf=results/multiagent/spend__${name}__${MODEL}.json capf=$LOGS/w24lem_cap__${name}.txt
  [ -f "$capf" ] || { say "$name: no cap file, not started"; return; }
  exec 8>"$LOGS/.w24lem_${name}.lock"
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
    $PY experiments/shared_world.py $flags --model "$MODEL" --world-offset "$OFFSET" --worlds "$WORLDS" \
        --reps "$REPS" --cap "$cap" --workers "$LEM_WORKERS"
    sleep 15
  done
  say "$name gave up after 6 attempts"
}

say "start (lemonade framing, offset $OFFSET, worlds $WORLDS, reps $REPS, workers $LEM_WORKERS)"
run_arm solo "--arm solo" $((WORLDS * 3 * REPS)) >> "$LOGS/w24lem_solo.log" 2>&1 &
run_arm share_at6-11-16 "--arm share --share-at 6,11,16" $((WORLDS * REPS)) >> "$LOGS/w24lem_share_at6-11-16.log" 2>&1 &
wait
say "runs finished; analysis"
$PY paper/scripts/stats_worlds24.py lemonade >> "$LOGS/w24lem_analysis.log" 2>&1 && say "analysis written" || say "analysis FAILED, see $LOGS/w24lem_analysis.log"
say "DONE"
