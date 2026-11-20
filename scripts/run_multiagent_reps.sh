#!/bin/bash
# Repeat runs of four conditions in both framings (docs/PILOT_MULTIAGENT.md, addendum 2026-11-04).
#   bash scripts/run_multiagent_reps.sh            all eight arms in parallel
#   bash scripts/run_multiagent_reps.sh solo       one arm by name
# Safe to rerun: episodes already recorded are skipped, each arm keeps the dollar cap fixed at its first launch,
# and a lock per arm stops a second copy from double-spending.
set -uo pipefail
cd "$(dirname "$0")/.."
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
MODEL=gpt-5.6-sol
WORLDS=8
LOGS=results/multiagent/logs
mkdir -p "$LOGS"

run_arm() {   # name, allowance in dollars, flags for shared_world.py
  local name=$1 allow=$2; shift 2
  local spendf=results/multiagent/spend__${name}__${MODEL}.json capf=$LOGS/rep_cap__${name}.txt
  exec 8>"$LOGS/.rep_${name}.lock"
  flock -n 8 || { echo "$(date -u +%FT%TZ) $name: another copy is running"; return; }
  [ -f "$capf" ] || $PY -c "import json,pathlib;p=pathlib.Path('$spendf');print(round((json.loads(p.read_text())['total'] if p.exists() else 0)+$allow,4))" > "$capf"
  local cap; cap=$(cat "$capf")
  for reps in 2 3; do            # repeat 1 for every world first, then repeat 2
    local need=$((WORLDS * 3 * reps))
    for try in 1 2 3 4 5 6; do
      local have spent
      have=$($PY -c "import json,pathlib;f=pathlib.Path('results/multiagent/${name}__${MODEL}.jsonl');print(len({json.loads(l)['key'] for l in f.open() if l.strip()}))")
      [ "$have" -ge "$need" ] && { echo "$(date -u +%FT%TZ) $name reps=$reps complete ($have episodes)"; break; }
      spent=$($PY -c "import json;print(json.load(open('$spendf'))['total'])")
      if awk -v s="$spent" -v c="$cap" 'BEGIN{exit !(s+0 >= c-0.5)}'; then
        echo "$(date -u +%FT%TZ) $name stopped at its cap (\$$spent of \$$cap)"; return
      fi
      echo "$(date -u +%FT%TZ) $name reps=$reps attempt $try ($have of $need episodes, \$$spent of \$$cap)"
      $PY experiments/shared_world.py "$@" --model "$MODEL" --worlds "$WORLDS" --reps "$reps" --cap "$cap"
      sleep 15
    done
  done
  echo "$(date -u +%FT%TZ) $name ARM_DONE"
}

arm() {   # dispatch by name so one arm can be started alone
  case $1 in
    solo)                   run_arm solo                   4.2 --arm solo ;;
    share)                  run_arm share                  7.6 --arm share ;;
    share_from6)            run_arm share_from6           11.6 --arm share --share-from 6 ;;
    share_at6-11-16)        run_arm share_at6-11-16        8.2 --arm share --share-at 6,11,16 ;;
    solo_alien)             run_arm solo_alien             7.0 --arm solo --alien ;;
    share_alien)            run_arm share_alien           12.8 --arm share --alien ;;
    share_from6_alien)      run_arm share_from6_alien     12.0 --arm share --share-from 6 --alien ;;
    share_at6-11-16_alien)  run_arm share_at6-11-16_alien  8.6 --arm share --share-at 6,11,16 --alien ;;
    *) echo "unknown arm $1"; exit 2 ;;
  esac
}

ALL="solo share share_from6 share_at6-11-16 solo_alien share_alien share_from6_alien share_at6-11-16_alien"
for a in ${@:-$ALL}; do
  arm "$a" >> "$LOGS/rep_${a}.log" 2>&1 &
done
wait
echo "$(date -u +%FT%TZ) REPS_DONE"
