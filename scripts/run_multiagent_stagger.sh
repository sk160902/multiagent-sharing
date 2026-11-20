#!/bin/bash
# Staggered-turn arm: within each round agents move one at a time in a rotating order, each seeing what the
# agents ahead of it did in that same round (docs/PILOT_MULTIAGENT.md).
#   setsid nohup bash scripts/run_multiagent_stagger.sh >> logs/multiagent_stagger.log 2>&1 < /dev/null &
# Safe to rerun: skips episodes already recorded; one copy at a time.
set -uo pipefail
cd "$(dirname "$0")/.."
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
MODEL=${MODEL:-gpt-5.6-sol}
WORLDS=${WORLDS:-8}
CAP=${CAP:-8}
exec 9>logs/.multiagent_stagger.lock
flock -n 9 || { echo "another copy is running"; exit 0; }
for try in 1 2 3 4 5; do
  have=$($PY -c "
import json,pathlib
f=pathlib.Path('results/multiagent/share_staggered__${MODEL}.jsonl')
print(len({json.loads(l)['key'] for l in f.open() if l.strip()}) if f.exists() else 0)")
  [ "$have" -ge $((WORLDS * 3)) ] && { echo "$(date -u +%FT%TZ) share_staggered complete"; break; }
  echo "$(date -u +%FT%TZ) share_staggered attempt $try ($have episodes so far)"
  $PY experiments/shared_world.py --arm share --stagger --model "$MODEL" --worlds "$WORLDS" --cap "$CAP"
  sleep 15
done
echo "$(date -u +%FT%TZ) STAGGER_DONE"
