#!/bin/bash
# Rerun of every alien-framing sharing arm with the board rendered in the agent's own vocabulary
# (docs/PILOT_MULTIAGENT.md, addendum 2026-11-20). Start, or resume after any interruption, with:
#   setsid nohup bash scripts/run_multiagent_alien_board.sh >> results/multiagent/logs/alienfix_driver.log 2>&1 < /dev/null &
# Safe to start at any time and any number of times: detached, one copy only (lock), every recorded episode is
# skipped, each arm's dollar cap is read from results/multiagent/logs/alienfix_cap__<arm>__<model>.txt and enforced
# per episode by the run script (episodes in flight counted); an arm with no cap file is not started. Ends by
# regenerating every analysis that reads an alien sharing arm.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
LOGS=results/multiagent/logs
mkdir -p "$LOGS"
exec 9>"$LOGS/.alienfix_driver.lock"
flock -n 9 || { echo "$(date -u +%FT%TZ) alienfix: another copy is running"; exit 0; }
say() { echo "$(date -u +%FT%TZ) alienfix: $*"; }

have() {  # recorded episodes of this arm for this model
  local f=results/multiagent/$1__$2.jsonl
  [ -f "$f" ] || { echo 0; return; }
  $PY -c "import json;print(len({json.loads(l)['key'] for l in open('$f') if l.strip()}))"
}

# run_arm <arm name> <model> <episodes needed> <workers> <invocation 1> [<invocation 2> ...]
# Each invocation is one shared_world.py flag string; an arm that spans two world sets has two.
run_arm() {
  local name=$1 model=$2 need=$3 workers=$4; shift 4
  local spendf=results/multiagent/spend__${name}__${model}.json capf=$LOGS/alienfix_cap__${name}__${model}.txt
  [ -f "$capf" ] || { say "$name/$model: no cap file, not started"; return; }
  exec 8>"$LOGS/.alienfix_${name}_${model}.lock"
  flock -n 8 || { say "$name/$model: another copy is running"; return; }
  local cap; cap=$(cat "$capf")
  for try in 1 2 3 4 5 6; do
    local h spent
    h=$(have "$name" "$model")
    [ "$h" -ge "$need" ] && { say "$name/$model complete ($h episodes)"; return; }
    spent=0; [ -f "$spendf" ] && spent=$($PY -c "import json;print(json.load(open('$spendf'))['total'])")
    if awk -v s="$spent" -v c="$cap" 'BEGIN{exit !(s+0 >= c-0.5)}'; then
      say "$name/$model stopped at its cap (\$$spent of \$$cap) with $h of $need episodes"; return
    fi
    say "$name/$model attempt $try ($h of $need episodes, \$$spent of \$$cap, workers $workers)"
    for flags in "$@"; do
      # shellcheck disable=SC2086
      $PY experiments/shared_world.py $flags --alien --model "$model" --cap "$cap" --workers "$workers"
    done
    sleep 20
  done
  say "$name/$model gave up after 6 attempts"
}

G=gpt-5.6-sol; C=claude-opus-5-5
say "start"
run_arm share_alien            $G  72 3 "--arm share --worlds 8 --reps 3"                                   >> "$LOGS/alienfix_share_alien.log" 2>&1 &
run_arm share_from3_alien      $G  48 3 "--arm share --share-from 3 --worlds 8 --reps 2"                   >> "$LOGS/alienfix_share_from3_alien.log" 2>&1 &
run_arm share_from6_alien      $G  48 3 "--arm share --share-from 6 --worlds 8 --reps 2"                   >> "$LOGS/alienfix_share_from6_alien.log" 2>&1 &
run_arm share_from11_alien     $G  48 3 "--arm share --share-from 11 --worlds 8 --reps 2"                  >> "$LOGS/alienfix_share_from11_alien.log" 2>&1 &
run_arm share_from16_alien     $G  48 3 "--arm share --share-from 16 --worlds 8 --reps 2"                  >> "$LOGS/alienfix_share_from16_alien.log" 2>&1 &
run_arm share_at6-11-16_alien  $G 216 3 "--arm share --share-at 6,11,16 --worlds 8 --reps 3" \
                                        "--arm share --share-at 6,11,16 --world-offset 16 --worlds 16 --reps 3" >> "$LOGS/alienfix_share_at6-11-16_alien.log" 2>&1 &
run_arm share_protocol_alien   $G  48 3 "--arm share_protocol --worlds 8 --reps 2"                          >> "$LOGS/alienfix_share_protocol_alien.log" 2>&1 &
run_arm share_staggered_alien  $G  48 3 "--arm share --stagger --worlds 8 --reps 2"                         >> "$LOGS/alienfix_share_staggered_alien.log" 2>&1 &
run_arm share_alien_h60        $G  72 4 "--arm share --horizon 60 --worlds 8 --reps 3"                      >> "$LOGS/alienfix_share_alien_h60.log" 2>&1 &
run_arm share_alien            $C  48 2 "--arm share --worlds 8 --reps 2"                                   >> "$LOGS/alienfix_share_alien_claude.log" 2>&1 &
run_arm share_at6-11-16_alien  $C  48 2 "--arm share --share-at 6,11,16 --worlds 8 --reps 2"               >> "$LOGS/alienfix_share_at6-11-16_alien_claude.log" 2>&1 &
wait
say "runs finished; analyses"
for s in stats_multiagent_reps writeup_numbers_multiagent run_means_multiagent stats_worlds24 stats_claude stats_h60 arxiv_sharing_tables; do
  $PY paper/scripts/$s.py >> "$LOGS/alienfix_analysis.log" 2>&1 && say "$s written" || say "$s FAILED, see $LOGS/alienfix_analysis.log"
done
say "DONE"
