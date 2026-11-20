#!/bin/bash
# Resume or extend the repeat runs of the shared-workspace conditions (docs/PILOT_MULTIAGENT.md, addenda 2026-11-04/05).
#   setsid nohup bash scripts/run_multiagent_repN.sh <reps> <arm> [<arm> ...] >> results/multiagent/logs/repN_master.log 2>&1 < /dev/null &
# <reps> is the --reps value: 2 completes repeat 1, 3 completes repeat 2. Each arm's dollar cap is read from
# results/multiagent/logs/rep_cap__<arm>.txt (the spend file's total may not pass it). Detached, so a closed
# session does not stop it. Recorded episodes are skipped; one copy per arm.
set -uo pipefail
cd "$(dirname "$0")/.."
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
MODEL=gpt-5.6-sol
WORLDS=8
LOGS=results/multiagent/logs
REPS=$1; shift

flags() {
  local base=${1%_alien} extra=""
  [ "$base" != "$1" ] && extra="--alien"
  case $base in
    solo)             echo "--arm solo $extra" ;;
    share)            echo "--arm share $extra" ;;
    share_from3)      echo "--arm share --share-from 3 $extra" ;;
    share_from6)      echo "--arm share --share-from 6 $extra" ;;
    share_from11)     echo "--arm share --share-from 11 $extra" ;;
    share_from16)     echo "--arm share --share-from 16 $extra" ;;
    share_at6-11-16)  echo "--arm share --share-at 6,11,16 $extra" ;;
    share_protocol)   echo "--arm share_protocol $extra" ;;
    share_staggered)  echo "--arm share --stagger $extra" ;;
    *) echo "UNKNOWN" ;;
  esac
}

run_arm() {
  local name=$1 f; f=$(flags "$name")
  [ "$f" = UNKNOWN ] && { echo "unknown arm $name"; return; }
  local spendf=results/multiagent/spend__${name}__${MODEL}.json capf=$LOGS/rep_cap__${name}.txt
  [ -f "$capf" ] || { echo "$(date -u +%FT%TZ) $name: no cap file, not started"; return; }
  exec 8>"$LOGS/.rep_${name}.lock"
  flock -n 8 || { echo "$(date -u +%FT%TZ) $name: another copy is running"; return; }
  local cap need; cap=$(cat "$capf"); need=$((WORLDS * 3 * REPS))
  for try in 1 2 3 4 5 6; do
    local have spent
    have=$($PY -c "import json,pathlib;f=pathlib.Path('results/multiagent/${name}__${MODEL}.jsonl');print(len({json.loads(l)['key'] for l in f.open() if l.strip()}))")
    [ "$have" -ge "$need" ] && { echo "$(date -u +%FT%TZ) $name reps=$REPS complete ($have episodes)"; return; }
    spent=$($PY -c "import json;print(json.load(open('$spendf'))['total'])")
    if awk -v s="$spent" -v c="$cap" 'BEGIN{exit !(s+0 >= c-0.5)}'; then
      echo "$(date -u +%FT%TZ) $name stopped at its cap (\$$spent of \$$cap) with $have of $need episodes"; return
    fi
    echo "$(date -u +%FT%TZ) $name reps=$REPS attempt $try ($have of $need episodes, \$$spent of \$$cap)"
    # shellcheck disable=SC2086
    $PY experiments/shared_world.py $f --model "$MODEL" --worlds "$WORLDS" --reps "$REPS" --cap "$cap"
    sleep 15
  done
  echo "$(date -u +%FT%TZ) $name gave up after 6 attempts"
}

for a in "$@"; do
  run_arm "$a" >> "$LOGS/rep_${a}.log" 2>&1 &
done
wait
echo "$(date -u +%FT%TZ) PHASE_DONE reps=$REPS arms: $*"
