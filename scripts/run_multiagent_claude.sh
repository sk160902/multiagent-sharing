#!/bin/bash
# Claude Opus 5 replication of solo, share and the periodic board in both framings (docs/PILOT_MULTIAGENT.md, addendum
# 2026-11-17, Claude). Start, or resume after any interruption, with:
#   setsid nohup bash scripts/run_multiagent_claude.sh >> results/multiagent/logs/claude_driver.log 2>&1 < /dev/null &
# Safe to start at any time and any number of times: detached, one copy only (lock), every recorded episode is skipped,
# each arm's dollar cap is read from results/multiagent/logs/claude_cap__<arm>.txt and enforced per episode by the run
# script (episodes in flight counted), and it ends by running paper/scripts/stats_claude.py.
set -uo pipefail
cd "$(dirname "$0")/.."
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
MODEL=claude-opus-5-5     # claude-opus-5 refuses the alien prompt and the board; amendment 2026-11-17
LOGS=results/multiagent/logs
WORLDS=8; REPS=2
export LEM_WORKERS=${LEM_WORKERS:-2}
mkdir -p "$LOGS"
exec 9>"$LOGS/.claude_driver.lock"
flock -n 9 || { echo "$(date -u +%FT%TZ) claude: another copy is running"; exit 0; }
say() { echo "$(date -u +%FT%TZ) claude: $*"; }

flags() {
  local base=${1%_alien} extra=""
  [ "$base" != "$1" ] && extra="--alien"
  case $base in
    solo)             echo "--arm solo $extra" ;;
    share)            echo "--arm share $extra" ;;
    share_at6-11-16)  echo "--arm share --share-at 6,11,16 $extra" ;;
    *) echo "UNKNOWN" ;;
  esac
}

have() {  # recorded episodes of this arm for this model
  local f=results/multiagent/$1__${MODEL}.jsonl
  [ -f "$f" ] || { echo 0; return; }
  $PY -c "import json;print(len({json.loads(l)['key'] for l in open('$f') if l.strip()}))"
}

run_arm() {
  local name=$1 f need; f=$(flags "$name")
  [ "$f" = UNKNOWN ] && { say "unknown arm $name"; return; }
  case $name in solo*) need=$((WORLDS * 3 * REPS));; *) need=$((WORLDS * REPS));; esac
  local spendf=results/multiagent/spend__${name}__${MODEL}.json capf=$LOGS/claude_cap__${name}.txt
  [ -f "$capf" ] || { say "$name: no cap file, not started"; return; }
  exec 8>"$LOGS/.claude_${name}.lock"
  flock -n 8 || { say "$name: another copy is running"; return; }
  local cap; cap=$(cat "$capf")
  for try in 1 2 3 4 5 6; do
    local h spent
    h=$(have "$name")
    [ "$h" -ge "$need" ] && { say "$name complete ($h episodes)"; return; }
    spent=0; [ -f "$spendf" ] && spent=$($PY -c "import json;print(json.load(open('$spendf'))['total'])")
    if awk -v s="$spent" -v c="$cap" 'BEGIN{exit !(s+0 >= c-0.5)}'; then
      say "$name stopped at its cap (\$$spent of \$$cap) with $h of $need episodes"; return
    fi
    say "$name attempt $try ($h of $need episodes, \$$spent of \$$cap, workers $LEM_WORKERS)"
    # shellcheck disable=SC2086
    $PY experiments/shared_world.py $f --model "$MODEL" --worlds "$WORLDS" --reps "$REPS" --cap "$cap" --workers "$LEM_WORKERS"
    sleep 20
  done
  say "$name gave up after 6 attempts"
}

say "start (model $MODEL, worlds $WORLDS, reps $REPS)"
for a in solo share share_at6-11-16 solo_alien share_alien share_at6-11-16_alien; do
  run_arm "$a" >> "$LOGS/claude_${a}.log" 2>&1 &
done
wait
say "runs finished; analysis"
$PY paper/scripts/stats_claude.py >> "$LOGS/claude_analysis.log" 2>&1 && say "analysis written" || say "analysis FAILED, see $LOGS/claude_analysis.log"
say "DONE"
