#!/bin/bash
# A second run of the other five conditions in both framings (docs/PILOT_MULTIAGENT.md, addendum 2026-11-05).
#   bash scripts/run_multiagent_reps2.sh                 all ten arms in parallel
#   bash scripts/run_multiagent_reps2.sh share_from3     one arm by name
# Safe to rerun: recorded episodes are skipped, each arm's dollar cap is fixed at its first launch, one copy per arm.
set -uo pipefail
cd "$(dirname "$0")/.."
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
MODEL=gpt-5.6-sol
WORLDS=8
REPS=2
LOGS=results/multiagent/logs
mkdir -p "$LOGS"

run_arm() {   # name, allowance in dollars, flags for shared_world.py
  local name=$1 allow=$2; shift 2
  local spendf=results/multiagent/spend__${name}__${MODEL}.json capf=$LOGS/rep_cap__${name}.txt
  exec 8>"$LOGS/.rep_${name}.lock"
  flock -n 8 || { echo "$(date -u +%FT%TZ) $name: another copy is running"; return; }
  [ -f "$capf" ] || $PY -c "import json,pathlib;p=pathlib.Path('$spendf');print(round((json.loads(p.read_text())['total'] if p.exists() else 0)+$allow,4))" > "$capf"
  local cap; cap=$(cat "$capf")
  local need=$((WORLDS * 3 * REPS))
  for try in 1 2 3 4 5 6; do
    local have spent
    have=$($PY -c "import json,pathlib;f=pathlib.Path('results/multiagent/${name}__${MODEL}.jsonl');print(len({json.loads(l)['key'] for l in f.open() if l.strip()}))")
    [ "$have" -ge "$need" ] && { echo "$(date -u +%FT%TZ) $name reps=$REPS complete ($have episodes)"; break; }
    spent=$($PY -c "import json;print(json.load(open('$spendf'))['total'])")
    if awk -v s="$spent" -v c="$cap" 'BEGIN{exit !(s+0 >= c-0.5)}'; then
      echo "$(date -u +%FT%TZ) $name stopped at its cap (\$$spent of \$$cap)"; return
    fi
    echo "$(date -u +%FT%TZ) $name reps=$REPS attempt $try ($have of $need episodes, \$$spent of \$$cap)"
    $PY experiments/shared_world.py "$@" --model "$MODEL" --worlds "$WORLDS" --reps "$REPS" --cap "$cap"
    sleep 15
  done
  echo "$(date -u +%FT%TZ) $name ARM_DONE"
}

arm() {
  case $1 in
    share_from3)            run_arm share_from3            6.4 --arm share --share-from 3 ;;
    share_from11)           run_arm share_from11           5.8 --arm share --share-from 11 ;;
    share_from16)           run_arm share_from16           4.9 --arm share --share-from 16 ;;
    share_protocol)         run_arm share_protocol         8.4 --arm share_protocol ;;
    share_staggered)        run_arm share_staggered        5.6 --arm share --stagger ;;
    share_from3_alien)      run_arm share_from3_alien      6.4 --arm share --share-from 3 --alien ;;
    share_from11_alien)     run_arm share_from11_alien     5.7 --arm share --share-from 11 --alien ;;
    share_from16_alien)     run_arm share_from16_alien     4.6 --arm share --share-from 16 --alien ;;
    share_protocol_alien)   run_arm share_protocol_alien   8.4 --arm share_protocol --alien ;;
    share_staggered_alien)  run_arm share_staggered_alien  5.6 --arm share --stagger --alien ;;
    *) echo "unknown arm $1"; exit 2 ;;
  esac
}

ALL="share_from3 share_from11 share_from16 share_protocol share_staggered share_from3_alien share_from11_alien share_from16_alien share_protocol_alien share_staggered_alien"
for a in ${@:-$ALL}; do
  arm "$a" >> "$LOGS/rep_${a}.log" 2>&1 &
done
wait
echo "$(date -u +%FT%TZ) REPS2_DONE"
