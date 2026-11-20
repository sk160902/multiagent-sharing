#!/bin/bash
# Supervisor for the shared-workspace pilot (docs/PILOT_MULTIAGENT.md).
#
#   setsid nohup bash scripts/run_multiagent_pilot.sh >> logs/multiagent_pilot.log 2>&1 < /dev/null &
#
# Safe to run again at any time: it resumes rather than repeats.
#   * detached from the terminal, so an SSH drop or a closed session does not kill it
#   * a lock file means a second copy exits instead of double-spending on the API
#   * each arm restarts on a crash or a network error, up to MAX_TRIES, with a pause between tries
#   * shared_world.py skips every episode already in its .jsonl, so a restart continues where it stopped.
#     An episode interrupted mid-flight is redone from its first round: at most one team episode is lost.
#   * each arm has its own dollar cap, counted in results/multiagent/spend__<arm>__<model>.json across restarts
set -uo pipefail
cd "$(dirname "$0")/.."

PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
MODEL=${MODEL:-gpt-5.6-sol}
WORLDS=${WORLDS:-8}
MAX_TRIES=${MAX_TRIES:-20}
LOCK=logs/.multiagent_pilot.lock

exec 9>"$LOCK"
if ! flock -n 9; then
  echo "$(date -u +%FT%TZ) another copy holds $LOCK; exiting"
  exit 0
fi

arm_done() {   # an arm is finished when every episode it plans is already recorded
  $PY - "$1" "$MODEL" "$WORLDS" <<'EOF'
import json, pathlib, sys
arm, model, worlds = sys.argv[1], sys.argv[2], int(sys.argv[3])
f = pathlib.Path("results/multiagent") / f"{arm}__{model}.jsonl"
need = worlds * (3 if arm == "solo" else 3)      # solo: 3 independent runs per world; teams: 3 agents per world
have = len({json.loads(l)["key"] for l in f.open() if l.strip()}) if f.exists() else 0   # unique episodes, not lines
sys.exit(0 if have >= need else 1)
EOF
}

for arm in solo share share_protocol; do
  cap=6; [ "$arm" = solo ] || cap=9
  for try in $(seq 1 "$MAX_TRIES"); do
    if arm_done "$arm"; then
      echo "$(date -u +%FT%TZ) $arm complete"
      break
    fi
    echo "$(date -u +%FT%TZ) $arm attempt $try"
    spent=$($PY -c "import json,pathlib;p=pathlib.Path('results/multiagent/spend__${arm}__${MODEL}.json');print(json.loads(p.read_text())['total'] if p.exists() else 0)")
    if awk -v s="$spent" -v c="$cap" 'BEGIN{exit !(s+0 >= c-0.2)}'; then
      echo "$(date -u +%FT%TZ) $arm stopped at its cap (\$$spent of \$$cap); raise the cap to continue"
      break
    fi
    $PY experiments/shared_world.py --arm "$arm" --model "$MODEL" --worlds "$WORLDS" --cap "$cap"
    rc=$?
    [ $rc -eq 0 ] || echo "$(date -u +%FT%TZ) $arm exited $rc; retrying"
    sleep 20
  done
done
echo "$(date -u +%FT%TZ) ALL_ARMS_DONE"
