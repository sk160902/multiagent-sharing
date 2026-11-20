#!/bin/bash
# Delayed-sharing arms of the shared-workspace pilot (docs/PILOT_MULTIAGENT.md).
# The board stays empty until round N, so each agent explores privately first.
#   setsid nohup bash scripts/run_multiagent_delays.sh >> logs/multiagent_delays.log 2>&1 < /dev/null &
# Safe to rerun: each arm skips episodes already recorded. One copy at a time (lock).
set -uo pipefail
cd "$(dirname "$0")/.."
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
MODEL=${MODEL:-gpt-5.6-sol}
WORLDS=${WORLDS:-8}
CAP=${CAP:-8}
exec 9>logs/.multiagent_delays.lock
flock -n 9 || { echo "another copy is running"; exit 0; }
for n in 3 6 11; do
  for try in 1 2 3 4 5; do
    have=$($PY -c "
import json,pathlib
f=pathlib.Path('results/multiagent/share_from${n}__${MODEL}.jsonl')
print(len({json.loads(l)['key'] for l in f.open() if l.strip()}) if f.exists() else 0)")
    [ "$have" -ge $((WORLDS * 3)) ] && { echo "$(date -u +%FT%TZ) share_from$n complete"; break; }
    echo "$(date -u +%FT%TZ) share_from$n attempt $try ($have episodes so far)"
    $PY experiments/shared_world.py --arm share --share-from "$n" --model "$MODEL" --worlds "$WORLDS" --cap "$CAP"
    sleep 15
  done
done
echo "$(date -u +%FT%TZ) DELAY_ARMS_DONE"
