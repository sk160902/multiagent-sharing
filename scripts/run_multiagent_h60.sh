#!/bin/bash
# Sixty-round games: working alone and sharing all along, both framings, 8 pilot worlds, 3 runs per world, GPT-5.6
# (docs/PILOT_MULTIAGENT.md, addendum 2026-11-19, horizon). Start, or resume after any interruption, with:
#   setsid nohup bash scripts/run_multiagent_h60.sh >> results/multiagent/logs/h60_driver.log 2>&1 < /dev/null &
# Safe to start at any time and any number of times:
#   * detached from the terminal, so a dropped connection or a closed session does not stop it
#   * one copy only (lock); a second copy exits at once
#   * every finished episode is on disk and is skipped, so it continues at the first episode not yet recorded;
#     an episode cut off mid-way is redone from its first round
#   * each arm's dollar cap is read from results/multiagent/logs/h60_cap__<arm>.txt and enforced by the run script
#     before every episode, counting episodes in flight, so the cap cannot be passed; an arm with no cap file is
#     not started
#   * ends by running the analysis fixed in the addendum (paper/scripts/stats_h60.py)
# Speed: the four arms run as four processes at once; within an arm LEM_WORKERS team episodes run as threads
# (default 4); within a team the three agents' calls of a round are made at the same time (shared_world.py,
# 2026-11-19). That is up to 4 x 4 x 3 = 48 calls in flight; 429s are retried with backoff by the client.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
MODEL=gpt-5.6-sol
LOGS=results/multiagent/logs
WORLDS=8; REPS=3; HORIZON=60
export LEM_WORKERS=${LEM_WORKERS:-4}
mkdir -p "$LOGS"
exec 9>"$LOGS/.h60_driver.lock"
flock -n 9 || { echo "$(date -u +%FT%TZ) h60: another copy is running"; exit 0; }
say() { echo "$(date -u +%FT%TZ) h60: $*"; }

flags() {
  local base=${1%_h60} extra=""
  base=${base%_alien}; [ "$base" != "${1%_h60}" ] && extra="--alien"
  case $base in
    solo)   echo "--arm solo $extra" ;;
    share)  echo "--arm share $extra" ;;
    *)      echo "UNKNOWN" ;;
  esac
}

have() {  # recorded episodes of this arm for this model (every world of this file is a 60-round world)
  local f=results/multiagent/$1__${MODEL}.jsonl
  [ -f "$f" ] || { echo 0; return; }
  $PY -c "import json;print(len({json.loads(l)['key'] for l in open('$f') if l.strip()}))"
}

run_arm() {
  local name=$1 f need; f=$(flags "$name")
  [ "$f" = UNKNOWN ] && { say "unknown arm $name"; return; }
  case $name in solo*) need=$((WORLDS * 3 * REPS));; *) need=$((WORLDS * REPS));; esac
  local spendf=results/multiagent/spend__${name}__${MODEL}.json capf=$LOGS/h60_cap__${name}.txt
  [ -f "$capf" ] || { say "$name: no cap file, not started"; return; }
  exec 8>"$LOGS/.h60_${name}.lock"
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
    $PY experiments/shared_world.py $f --model "$MODEL" --horizon "$HORIZON" --worlds "$WORLDS" --reps "$REPS" \
        --cap "$cap" --workers "$LEM_WORKERS"
    sleep 20
  done
  say "$name gave up after 6 attempts"
}

say "start (model $MODEL, horizon $HORIZON, worlds $WORLDS, reps $REPS, workers $LEM_WORKERS)"
for a in solo_h60 share_h60 solo_alien_h60 share_alien_h60; do
  run_arm "$a" >> "$LOGS/h60_${a}.log" 2>&1 &
done
wait
say "runs finished; analysis"
$PY paper/scripts/stats_h60.py >> "$LOGS/h60_analysis.log" 2>&1 && say "analysis written" || say "analysis FAILED, see $LOGS/h60_analysis.log"
say "DONE"
