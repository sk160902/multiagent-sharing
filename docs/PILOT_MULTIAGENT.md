# Pilot: shared-workspace agents in the lemonade world (exploratory, written before running)

**Status: exploratory pilot. Not pre-registered, not confirmatory, and unable to change any claim in the ICLR
submission.** Written 2026-09-30, before any episode is run, so the arms and metrics are fixed in advance.

## Question

Park et al. (arXiv 2609.21032, *Scaling Discovery through Test-Time Communication*) show that k agents sharing a
workspace beat the best of k independent agents when an agent-accessible verifier ranks partial progress correctly,
and that the advantage disappears where feedback cannot rank intermediate solutions. They leave open what happens
when feedback is available but *misleading about direction*.

Our world is that case. Profit per round is an honest verifier of the present and a liar about the future: the route
to the best strategy (200 per round) passes through a valley (33.8) that scores far below the recommended default
(86.5). An agent that adopts whatever currently scores best will never cross. March (1991) predicts that mutual
learning of this kind raises short-run performance and lowers long-run performance.

**Hypothesis (directional, stated now):** sharing verified profits makes a team converge on the recommended default
faster than independent agents, so team@k <= best@k here, the opposite of the paper's headline result. The mechanism
is herding on the current leader's score, and it should be visible as reduced diversity of locations tried.

## Design

Identical agents, same model, same world, one shared board, no roles and no orchestrator (their minimal setting).
Each agent runs its own stand in its own copy of the world: profits are not coupled, so every number stays comparable
with the single-agent results already in the paper. Rounds are lockstep, and an agent choosing round t sees the board
as it stood at the end of round t-1.

Arms, all at the paper's main cell (neutral prompt, semantic labels, hint on, horizon 20):

| arm | k | board | protocol |
|---|---|---|---|
| `solo` | 1 | none | the existing single-agent setting; k independent runs give best@k |
| `share` | 3 | every agent's action and profit each round | "you may use what others found" |
| `share_protocol` | 3 | the same board | their anti-herding rules: claim a distinct approach, adopt a peer's only on clearly better evidence, and keep one variation after adopting |

## Metrics, fixed before running

Per agent, the paper's existing definitions (analysis/metrics.py): `left_anchor_ever`, `escaped`, `pct_optimum`
(mean of the last five rounds), `parse_ok`.

Per team, and for best@k computed over k independent solo runs on the same world:
1. **team best** and **team mean** share of the optimum, and escape.
2. **Diversity:** distinct locations tried by the team over the episode, and the round at which the team's set of
   locations stops growing.
3. **Herding:** share of agent-rounds whose chosen location equals the location of the board's current
   highest-earning entry.
4. **Time to first leave:** first round in which any agent leaves the default location.

## Scale and cost

Pilot: 8 validation worlds (never test worlds), one repeat, GPT-5.6 as the cheapest unsaturated model
(median $0.13 per single-agent episode; it leaves the default in 84.4% of episodes and escapes in 39.1%, so it has
room to move in both directions). That is 24 solo + 24 + 24 agent-episodes, roughly $15 at the observed rate, against
$320 remaining under the project's $550 cap. The run refuses to start an episode that would exceed a cap passed on
the command line.

Widening to a second model, more worlds or larger k is a separate decision taken after the pilot's numbers exist.

## What would change the conclusion

If `share` beats `solo` on crossing, the hypothesis is wrong and the paper's result extends to misleading verifiers.
If `share` is worse and `share_protocol` recovers, the anti-herding rules are doing the work, which is a statement
about their protocol rather than about communication. With 8 worlds nothing here is a significance test; it decides
whether a full study is worth pre-registering.

## Addendum, 2026-10-02: four arms added after the first three ran

Added at the user's suggestion, after seeing that the first teams converged by round 1 and ended identical.

| arm | board visible from | turn order |
|---|---|---|
| `share_from3`, `share_from6`, `share_from11` | round 3, 6, 11 | simultaneous |
| `share_staggered` | round 1 | one agent at a time, rotating, each seeing this round's earlier results |

Results are posted from round 1 in every arm, so a delayed board opens carrying the private history. The staggered arm
is not a like-for-like comparison with the simultaneous arms: its later movers decide on strictly fresher information.
Metrics and worlds are unchanged.

## Addendum, 2026-10-12: periodic board and a Meta-Harness-style protocol search

Added at a collaborator's suggestion. User-approved API budget for both: $125.

**Periodic board** (`share_at6-11-16`, `experiments/shared_world.py --share-at 6,11,16`): the board is visible only in
rounds 6, 11 and 16, private otherwise; agents post every round, so each opening shows the full history. Pilot worlds
val[:8], one team each, $3.88.

**Protocol search** (`experiments/protocol_search.py`, protocols in `experiments/protocols/`, results in
`results/multiagent_search/`). Search worlds val[8:16]; pilot worlds val[:8] only for the final check; test never
touched. Objective, chosen by the user before the search: mean over episodes of the sum of profits over rounds 1-20 as
a share of the most the world allows. A protocol may change the board's content, visibility and turn order and add
generic instructions; it sees only posted actions and profits, never world parameters, and the paper's system prompt
is unchanged. Proposer: Claude Code, reading every candidate's code, scores and per-round board/output traces. 4 seeds
(the pilot arms `share`, `share_staggered`, `share_from11`, and the periodic schedule), 8 proposed candidates over 3
iterations, then fresh-seed repeats (`--rep 1`) of the leaders and of one ablation. Search spend $85.55.

## Addendum, 2026-11-04: repeat runs of four conditions (written before any repeat was run)

**Why.** With one run per world, a paired test over the 8 worlds finds the drop in distinct settings and the gain in
summed earnings reliable, and the drop in the team's best round not reliable (all sharing arms against solo: -8.6 points,
95% CI -24.7 to 7.6 with the letter; -5.1, CI -28.3 to 18.1 in the alien framing). The periodic board beats solo in the
alien framing by one world of eight. Repeats are the direct way to find out which of these hold.

**Budget.** User go-ahead on 2026-11-04 for repeat runs. Recorded API spend before this addendum is $476.17 of the $550
cap (results/frontier $289.10, results/multiagent $101.51, results/multiagent_search $85.55), so $73.83 is left. Per-arm
allowances sum to $72.00, enforced by `--cap`: solo 4.2, share 7.6, share_from6 11.6, share_at6-11-16 8.2, solo_alien
7.0, share_alien 12.8, share_from6_alien 12.0, share_at6-11-16_alien 8.6. All nine conditions do not fit in what is left.

**Design.** Conditions `solo`, `share`, `share_from6`, `share_at6-11-16`, each with the letter and in the alien framing,
on the same pilot worlds val[:8], GPT-5.6 (gpt-5.6-sol), k=3, horizon 20, prompt and flags unchanged. Two more runs per
world (`--reps 3`, keys with repeat 1 and 2), so three runs per world in all. Repeat 1 is completed for every world
before repeat 2 starts. Launcher: `scripts/run_multiagent_reps.sh`. The first-run files are copied to
`results/multiagent/backup_before_reps_2026-11-04/`; new episodes are appended, nothing is overwritten.

**One code change, made before the runs.** `shared_world.py` built the environment seed from the world and the agent
only, so a repeat would have reused the first run's customer-feedback draws. The seed now adds `7919 * rep`. Repeat 0 is
unchanged, so the existing episodes are still reproducible from the same seeds.

**Analysis, fixed now.**
- Unit: the world. A world's value for a condition is the mean over its completed keyed runs (repeat 0, 1, 2). Records
  that repeat an existing key (the accidental second pass of `solo`, `share`, `share_protocol` on 2026-09-30) stay
  excluded, as in `paper/scripts/table_multiagent_dvs.py`.
- Measures, unchanged: `best_peak`, `sum_pct`, `unique`, and the share of runs whose best round is at the best location
  (`best_peak` above 60, since no other location pays more than 56.3% of the optimum).
- Contrasts, within a framing: each of the three sharing conditions minus solo, and the mean of the three minus solo.
  The same four contrasts with the two framings averaged per world.
- Test: exact two-sided sign-flip test over the 8 worlds, with a 95% t interval on the 8 world-level differences.
- No stopping or extension that depends on the results. If a cap stops an arm early, the worlds it did not reach keep the
  runs they have and that is reported.
- Also reported: the same contrasts on repeat 0 alone and on repeats 1 and 2 alone, so the reader sees whether the first
  run and the new runs agree.

**Amendment, 2026-11-05 01:15 UTC, made on cost alone before any outcome was analysed.** After 32 of 384 new episodes
the measured cost projects to about $77 for the full design, above the $72.00 allowed. Episodes cost more than the first
run suggested (solo about $0.15 an episode, sharing teams $0.53 to $0.84). The total allowed stays $72.00. To keep the
baseline complete, `share_from6` and `share_from6_alien` stop after repeat 1 (two runs per world), and what they leave
unspent is moved, in this order, to `solo`, `solo_alien`, `share`, `share_alien`, `share_at6-11-16`,
`share_at6-11-16_alien` so those reach three runs per world. The analysis plan above is unchanged; a world's value is
still the mean over the runs it has.

## Addendum, 2026-11-05: a second run of the other five conditions (written before any of these ran)

**Why.** The write-up reports nine conditions in two framings. Four are being repeated under the addendum above. The
user's aim is to know whether every reported result holds on a rerun, so the other five get a second run too.

**Budget.** User raised the API cap to $610 on 2026-11-05. Allowances, enforced by `--cap`, sum to $61.80:
share_from3 6.4, share_from11 5.8, share_from16 4.9, share_protocol 8.4, share_staggered 5.6, share_from3_alien 6.4,
share_from11_alien 5.7, share_from16_alien 4.6, share_protocol_alien 8.4, share_staggered_alien 5.6. With the $72.00
of the first block the total allowed is $133.80 against $133.83 left under the cap. Money an arm leaves unspent may be
moved to an arm that stopped short of its planned runs; the total does not rise.

**Design.** `share_from3`, `share_from11`, `share_from16`, `share_protocol`, `share_staggered`, with the letter and in
the alien framing, same worlds val[:8], same model, k, horizon, prompt and flags as their first run. One more run per
world (`--reps 2`, repeat 1), with the repeat's own environment seeds. Launcher: `scripts/run_multiagent_reps2.sh`.
First-run files copied to `results/multiagent/backup_before_reps_2026-11-04/`.

**Analysis, fixed now.** Same unit, measures, test and interval as the addendum above. Contrasts within a framing: each
of the eight sharing conditions minus solo, and the mean of the eight minus solo; the same with the two framings
averaged per world. A world's value is the mean over the keyed runs it has (solo and two sharing conditions will have
three, the rest two), and the accidental duplicate records of 2026-09-30 stay excluded. Reported alongside: the same
contrasts on the first run alone and on the new runs alone, and for each condition and measure whether the new runs
fall on the same side of solo as the first run did.

**Process note, 2026-11-05 01:35 UTC.** The first launch was tied to the session that started it and stopped when that
session ended at about 01:30 UTC, with 17 arms mid-episode. Recorded episodes were kept; the episodes in flight were
lost and are redone. Their API calls were paid for but are in no spend file, at most one episode per arm, so an estimated
$6 and at most $12. To keep the real total under $610, $8 of the $133.80 allowed is held back. Relaunched detached with
`scripts/run_multiagent_repN.sh` in two phases, on cost alone and before any outcome was analysed: first every arm
completes repeat 1, then what is left pays for repeat 2 of solo, solo_alien, share, share_alien, share_at6-11-16 and
share_at6-11-16_alien, in that order of priority. `share_from6` and `share_from6_alien` stay at two runs per world.
Both phases and the final analysis are run by `scripts/run_multiagent_reps_driver.sh`, started detached at 01:44 UTC. It
holds a lock, skips every recorded episode, computes the phase B caps once from recorded cost and stores them in
`results/multiagent/logs/phaseB_caps.json`, so starting it again after any interruption continues where it stopped.

**Process note, 2026-11-05 01:55 UTC: worker threads.** At the user's request the remaining episodes run several at a
time. `shared_world.py` gained `--workers` (default 1, or `$LEM_WORKERS`): the team episodes of one arm run as threads of
one process. Nothing an episode does changes, since episodes share no state and keep their seeds. The cap check, the
spend file and the results file sit under one lock, and an episode starts only if the cap still holds with every
episode in flight paid for, so the cap cannot be passed. Checked offline with a stand-in for the API (parallelism,
skipping, cap, resume, no duplicate keys). The copy before this change is
`results/multiagent/backup_before_reps_2026-11-04/shared_world.py.before_workers`. Running arms were stopped at the
moment they recorded an episode (`scripts/handoff_to_workers.sh`) and restarted with four workers; the driver was
restarted with `LEM_WORKERS=4`. Made on speed alone, before any outcome was analysed.

## Addendum, 2026-11-17: sixteen new worlds for the periodic board against working alone, alien framing (written before any of these ran)

**Why.** On the eight pilot worlds the periodic board (`share_at6-11-16_alien`) is +2.9 points above working alone on
`best_peak` [-12.7, +18.5], p=0.70, the whole gap being one extra world-run at the best location (20 of 24 against 19 of
24). A collaborator's review (14 Nov) said the right fix is to run more rather than leave it open. The test is paired over
worlds, so with eight worlds the smallest attainable p is 0.0078 whatever the number of repeats; more worlds is what
tightens it. Agreed with the user on 2026-11-17: working alone and this one condition, alien framing, on 16 more worlds.

**Worlds.** `val[16:32]` of `data/worlds_main.json`, never used by any arm before: `val[:8]` are the pilot worlds and
`val[8:16]` were the protocol search's worlds (addendum 2026-10-12), where the periodic schedule served as a seed, so they
are skipped to keep the new worlds untouched by anything involving this condition. Test worlds are never used.

**Design.** `solo_alien` and `share_at6-11-16_alien`, GPT-5.6 (gpt-5.6-sol), k=3, horizon 20, prompt and flags unchanged
from the pilot, two runs per world (`--reps 2`, repeats 0 and 1) with the per-repeat environment seeds. Launcher:
`scripts/run_multiagent_worlds24.sh` (detached, one copy, resumable, caps enforced per episode by the run script).
One code change made before the runs: `experiments/shared_world.py` gained `--world-offset` so a run can start at
`val[16]`; the copy before the change is `results/multiagent/backup_before_reps_2026-11-04/shared_world.py.before_offset`.
New episodes are appended to the arms' existing result files, keyed by world; nothing is overwritten.

**Budget.** Measured on the repeat runs: solo about $0.21 per agent-episode, periodic-board teams about $0.76 per
team-episode. Two runs per world on 16 worlds is 96 agent-episodes plus 32 team-episodes, about $44. Caps per arm are
set in `results/multiagent/logs/w24_cap__<arm>.txt` as the arm's current spend-file total plus its allowance, once the
user names the allowance; they are recorded in DECISIONS.md with the amount.

**Analysis, fixed now** (`paper/scripts/stats_worlds24.py`). Unit: the world; a world's value is the mean over its
completed keyed runs (three on the pilot worlds, two on the new ones). Contrast: periodic board minus working alone,
paired within world, on `best_peak`, `sum_pct`, `unique` and `reached_best`. Exact two-sided sign-flip test over the
worlds and a 95% t interval. Reported for the 16 new worlds alone, the 8 pilot worlds alone, and all 24. The primary
result is `best_peak` on all 24 worlds. No stopping or extension that depends on the results; if a cap stops an arm
early, the worlds it reached are analysed and that is reported.

**Amendment, 2026-11-17, before launch.** The user asked for three runs per world on the new 16 worlds, matching the
pilot worlds, so `--reps 3` (repeats 0, 1, 2): 144 agent-episodes of working alone and 48 team-episodes of the periodic
board, about $66 at the measured rates. Allowance $70, raising the project cap from $610 to $680: working alone $32,
periodic board $38, written to `results/multiagent/logs/w24_cap__<arm>.txt` as the spend-file total plus the allowance.
Analysis unchanged except that every world now has three runs.

## Addendum, 2026-11-17: Claude Opus 5 replication of three conditions, both framings (written before any of these ran)

**Why.** A collaborator's review (14 Nov) said he would only read the per-world patterns with confidence if the same
trends hold on Claude, having seen GPT-5.6 and Claude behave differently elsewhere. User approved on 2026-11-17.

**Design.** `claude-opus-5` (Anthropic API, key file `working_apis/api_key_anthropic_ucb.txt`, already used for the
single-agent frontier sweep), pilot worlds `val[:8]`, k=3, horizon 20, prompt and flags unchanged. Conditions `solo`,
`share`, `share_at6-11-16`, each with the letter and in the alien framing (six arms), two runs per world (`--reps 2`).
Result and spend files are the model-suffixed ones (`<arm>__claude-opus-5.jsonl`), so nothing of the GPT runs is touched.
Launcher: `scripts/run_multiagent_claude.sh` (detached, one copy, resumable, caps enforced per episode).

**Budget.** Estimated from GPT token counts at Claude prices ($5/M in, $25/M out): solo about $0.25 per agent-episode,
sharing teams about $1.00 per team-episode; the design is 96 agent-episodes of solo and 64 team-episodes of sharing over both
framings, in total about $88. User approved $100, raising the project cap from $680 to $780. Caps per arm, in
`results/multiagent/logs/claude_cap__<arm>.txt`: solo 14, share 18, share_at6-11-16 18, in each framing ($100 in all).
If a cap stops an arm early, the worlds it completed are analysed and that is reported.

**Analysis, fixed now** (`paper/scripts/stats_claude.py`). Unit: the world, mean over its completed runs. Contrasts, within
a framing: `share` minus `solo` and `share_at6-11-16` minus `solo`, on `best_peak`, `sum_pct`, `unique`, `reached_best`;
exact two-sided sign-flip test over the 8 worlds and 95% t interval; the same on the GPT-5.6 runs of the same three
conditions for side-by-side comparison. The question is whether the signs match GPT-5.6: fewer distinct setups and higher
cumulative earnings under sharing, lower max under sharing all along, and the periodic board level with solo. No stopping
or extension that depends on the results.

**Process note, 2026-11-17 06:30 UTC: Claude run stopped after about ten minutes.** The first recorded `share_alien` teams had
`refusals: 20` and `parse_ok` all false: Claude Opus 5 returned `stop_reason: "refusal"`, category "cyber", on every
round, so the episodes played the fallback action and are not Claude's behaviour. The whole Claude driver was stopped
(process group killed; resumable). Diagnostic single calls (about $0.03): the alien prompt is refused every time even
with no board; the lemonade prompt with the board attached is refused on most calls (2 of 3 with posts, 1 of 1 with an
empty board); the lemonade prompt without a board is answered. This is the refusal already recorded on 2026-09-12
(DECISIONS.md), now shown to cover the alien framing and the shared board. Spend before the stop: `share_alien` $1.42
(two refused teams), `solo` $0.35 (two good episodes), diagnostics about $0.03. The refused records stay in
`share_alien__claude-opus-5.jsonl`; any analysis must drop episodes whose `refusals` count is non-zero. The remaining
Claude caps are untouched. Whether to continue with another model is the user's decision.

**Amendment, 2026-11-17 06:34 UTC, before relaunch: model changed to claude-opus-5-5.** Single diagnostic calls on four
other Anthropic models (claude-opus-5-5, claude-sonnet-5-5, claude-sonnet-5, claude-opus-4-8; alien prompt, lemonade
prompt with board, alien prompt with board, two calls each, $0.08 in all) were all answered; only claude-opus-5 refuses.
User chose claude-opus-5-5 ($4 in / $20 out per million tokens, the current Opus). Design, worlds, runs and analysis
unchanged; result files are `<arm>__claude-opus-5-5.jsonl`. Caps rewritten so that the Claude total, including the
$1.77 spent on claude-opus-5 and $0.11 of diagnostics, stays within the approved $100: solo 13.50, share 17.50,
share_at6-11-16 17.50 in each framing ($97.00). The claude-opus-5 records stay on disk and are not analysed.

## Addendum, 2026-11-19: sixty-round games, sharing all along against working alone, both framings (written before any of these ran)

**Why.** The write-up says the trade is between earning more along the way and finding less at the end. A
collaborator's comment (14 Nov) on that sentence: this is the cost of exploration, and with much more than 20 rounds it
may not be a trade-off at all. Two ways that could happen, both only visible with a longer game: the lone agents, who
explore more and find the best location late, out-earn the sharing teams once the discovery has time to pay (cumulative);
or the sharing teams, given time, also leave the recommended location and the ceiling gap closes (max). Every existing
run stops at round 20 and every prompt says "Round r of 20", so no existing episode can be continued: an agent that
believed round 20 was the last played its last rounds accordingly. A 60-round game is a new arm. Agreed with the user on
2026-11-19: this run first, on the 8 pilot worlds, and its result decides the horizon at which the 16-world lemonade
extension (the "iffy argument" thread) is run.

**Design.** `solo` and `share` (sharing all along), each with the letter and in the alien framing, GPT-5.6 (gpt-5.6-sol),
k=3, **horizon 60**, pilot worlds `val[:8]`, three runs per world (`--reps 3`, repeats 0, 1, 2, the per-repeat environment
seeds unchanged). Prompt, flags and everything else unchanged except the horizon, which enters the prompt only through
"for 60 rounds" in the system message and "Round r of 60" in the user message (the midpoint markers `half`/`half1` are
not used by the neutral condition). Arms and files: `solo_h60`, `share_h60`, `solo_alien_h60`, `share_alien_h60`, each
`<arm>__gpt-5.6-sol.jsonl` with its own spend file; nothing existing is touched. Launcher:
`scripts/run_multiagent_h60.sh` (detached, one copy, resumable, caps enforced per episode by the run script).

**Code changes made before the runs** (`experiments/shared_world.py`; the copy before them is
`results/multiagent/backup_before_reps_2026-11-04/shared_world.py.before_horizon`):
1. `--horizon` (default 20). Any other value appends `_h<horizon>` to the arm name, so a 60-round episode can never land
   in, or be skipped because of, a 20-round file. The record's `horizon` field carries the value.
2. The first-episode cost guess used by the cap check is scaled by (horizon/20)^2, since every round's prompt carries the
   whole history; after the first episode the measured cost takes over, as before.
3. Speed, at the user's request: in the simultaneous setting the k agents of a round choose from the same board and cannot
   see each other's choice for that round, so their API calls are now made at the same time (threads) instead of one after
   another. Prompts, seeds, parsing, posting order, `copied_leader_rounds` and the records are exactly what the sequential
   loop produced; only the wall-clock changes. The staggered setting keeps the sequential loop. This applies to every arm
   from now on, including any resumed 20-round arm, and changes no outcome.
Also for speed, the launcher runs the four arms as four processes with `LEM_WORKERS=4` team episodes each. Checked offline
before launch with a stub client (no API): the old and new loops give byte-identical records and the same set of prompts
on a 20-round sharing team and a solo episode; at horizon 60 a team plays 60 rounds, every system message says "for 60
rounds", the last user message says "Round 60 of 60", and the arm is `share_h60`. Cost: `cost()` in
`evaluation/frontier_sweep.py` would credit cached prompt tokens at a tenth of the price, but every recorded GPT-5.6
episode reports zero cached tokens, so no cache discount is assumed. No prompt was changed to improve caching.

**Budget.** Input tokens per episode grow with the square of the horizon (each round's prompt carries the whole history,
and the board grows three lines a round). Measured on the recorded 20-round GPT-5.6 episodes: solo 15.4k input and 4.0k
output tokens per agent-episode ($0.14), sharing 39.2k input and 4.8k output per agent-episode ($0.76 per team-episode),
alien framing within 10% of those. Fitting a fixed part of about 350 tokens, about 44 per history line and about 42 per
board line, a 60-round game is about 99k input per solo agent-episode and about 322k per sharing agent-episode (966k per
team-episode), with output three times the 20-round figure. At $4/M in and $20/M out, no cache hits: about $0.65 per solo
agent-episode and about $4.70 per team-episode. The design is 72 + 72 solo agent-episodes and 24 + 24 team-episodes:
about $320. Proposed allowance $400 (cap $780 -> $1,180), split solo_h60 $60, share_h60 $140, solo_alien_h60 $60,
share_alien_h60 $140. Caps are written to `results/multiagent/logs/h60_cap__<arm>.txt` and recorded in DECISIONS.md once
the user names the allowance; the launcher does not start an arm without its cap file. If a cap stops an arm early, the
worlds it completed are analysed and that is reported. Wall-clock, from the 20-round runs' call latency: a 60-round solo
episode is about 60 sequential calls, a team-episode about 60 rounds of three simultaneous calls; with four arms in
parallel and four episodes per arm the whole run should finish in a few hours rather than a day.

**Analysis, fixed now** (`paper/scripts/stats_h60.py`). Unit: the world; a world's value is the mean over its completed
runs. Contrast: `share` minus `solo` within a framing, paired within world, exact two-sided sign-flip test over the 8
worlds and a 95% t interval, on (a) the whole 60-round game: `best_peak`, `sum_pct`, `unique`, `reached_best`; (b) the
late window, rounds 21-60: the same measures, the direct test of the comment; (c) rounds 1-20 of the 60-round game beside
the existing 20-round runs, both the share-minus-solo contrast and, per arm, 60-round-game minus 20-round-game on the
same window, to show whether being told "of 60" changes early play. Output `results/multiagent/stats_h60.{json,md}`.

**Decision rule, fixed now** (either framing is enough):
- C1: `sum_pct` over 60 rounds, share minus solo, reverses sign (negative) -> change.
- C2: `sum_pct` over rounds 21-60, share minus solo, negative -> change.
- C3: `best_peak` over 60 rounds: in a framing whose 20-round gap is below -5 points, a 60-round gap above -5 points ->
  change (sharing catches up on the ceiling given time).
- C4: `unique` over 60 rounds, share minus solo, positive -> reported as a change, not expected.
"No change" is C1-C3 all holding the 20-round sign in both framings: the paper stays at 20 rounds, the 60-round result is
reported as a robustness paragraph, and the 16-world lemonade extension runs at 20 rounds. "Change" is any of C1-C3:
the paper's horizon moves to 60, the 16-world extension (and, later, the Claude replication) run at 60. With 8 worlds
the sign-flip test is coarse, so the rule is on direction and magnitude, not on p-values. No stopping or extension
that depends on the results while they are being collected.

**Approval, 2026-11-19, before launch.** User approved the $400 allowance (project cap $780 -> $1,180). Caps written as
proposed: solo_h60 60, share_h60 140, solo_alien_h60 60, share_alien_h60 140. Launched detached from the repo root with
`scripts/run_multiagent_h60.sh`, `LEM_WORKERS=4`.

**Process note, 2026-11-20 02:07 UTC: complete.** Launched 01:24 UTC, finished 02:06 UTC, 42 minutes. All four arms
complete (24 runs each), 11,520 of 11,520 rounds parsed, zero refusals, no cap stop. Spend $280.65 against the $320
estimate. Analysis written to `results/multiagent/stats_h60.{json,md}` by the launcher; the verdict by the rule above is
"change" (C3 in the lemonade framing, C2 in the alien framing). Numbers and reading in `docs/RESULTS.md`, entry
2026-11-20. What follows from the rule (the 16-world extension at 60 rounds, the Claude replication at 60) is new spend
and awaits the user's approval.

**User decision, 2026-11-20, after reading the result.** The paper stays at 20 rounds and the 60-round runs are reported
as a horizon section (two conditions, both framings). Reasons: the C2 trigger in the alien framing is a 3-point
difference with a 40-point interval; the lemonade trigger moves the result in sharing's favour; and every other block
of the paper (nine conditions, per-world tables, the 24-world extension, the second model) is at 20 rounds. This is a
deviation from the rule above and is recorded as the user's call. The 16-world lemonade extension therefore runs at 20
rounds (next addendum).

## Addendum, 2026-11-19: sixteen new worlds for the periodic board against working alone, lemonade framing (written before any of these ran)

**Why.** The alien-framing extension of 2026-11-17 was scoped to the one cell a collaborator flagged. That leaves the
paper's recommended condition, the periodic board, on 24 worlds in one framing and 8 in the other, and the lemonade
periodic-board interval on the max runs from -21.7 to +10.5, which does not support "level with working alone". The
paper states every headline result as holding in both framings; the follow-up should too. Agreed with the user on
2026-11-20 (UTC; 2026-11-19 Pacific).

**Design.** Identical to the alien extension except for the framing: `solo` and `share_at6-11-16` with the letter,
GPT-5.6 (gpt-5.6-sol), k=3, horizon 20, prompt and flags unchanged, worlds `val[16:32]` (the same 16 as the alien
extension, so the two framings are compared on identical worlds), three runs per world (`--reps 3`), per-repeat
environment seeds. New episodes are appended to the arms' existing result files, keyed by world; nothing is overwritten.
Launcher: `scripts/run_multiagent_worlds24_lemonade.sh` (detached, one copy, resumable, caps enforced per episode; the
new-world episode count moved to `scripts/count_new_worlds.py` so the launcher has no inline Python). The parallel
agent calls of 2026-11-19 apply.

**Budget.** At the rates measured on the alien extension (solo $0.21 per agent-episode, periodic board $0.76 per
team-episode; lemonade episodes a few percent cheaper): 144 agent-episodes plus 48 team-episodes, about $66. User
approved $75 (project cap $1,180 -> $1,255): working alone $35, periodic board $40, written to
`results/multiagent/logs/w24lem_cap__<arm>.txt` as the arm's spend-file total plus the allowance (45.16 and 51.62). If a
cap stops an arm early, the worlds it completed are analysed and that is reported.

**Analysis, fixed now.** `paper/scripts/stats_worlds24.py lemonade`: the script of the alien extension with the framing
as an argument and nothing else changed, writing `results/multiagent/stats_worlds24_lemonade.{json,md}`. Unit: the
world; mean over its completed runs (three on every world). Contrast: periodic board minus working alone, paired within
world, on `best_peak`, `sum_pct`, `unique`, `reached_best`; exact two-sided sign-flip test and 95% t interval; reported
for the 16 new worlds, the 8 pilot worlds and all 24. The primary result is `best_peak` on all 24 worlds. Expected, from
the pilot worlds: level with working alone on the max, higher cumulative earnings, fewer distinct setups. No stopping or
extension that depends on the results.

**Process note, 2026-11-20 04:07 UTC: complete.** Launched 03:31 UTC, finished 04:06 UTC. Both arms complete on the 16
new worlds (144 solo agent-episodes, 48 periodic-board team-episodes), no cap stop. Spend $43.01 (solo $19.75, periodic
board $23.26) of the $75 approved; project total $1,025.72 of the $1,255 cap. Analysis written by the launcher to
`results/multiagent/stats_worlds24_lemonade.{json,md}`. Primary result, `best_peak` on all 24 worlds: periodic board
minus working alone -1.3 [-8.1, +5.4], p=0.68, 11 worlds up and 11 down; level, as in the alien framing (+0.6 [-4.6,
+5.7]). Numbers and reading in `docs/RESULTS.md`, entry 2026-11-20 (lemonade 24 worlds).

## Addendum, 2026-11-20: the shared board rendered in the agent's own vocabulary; every alien sharing arm rerun (written before any of these ran)

**The defect.** The shared board was rendered by `post_line` and `BOARD_INTRO` in `experiments/shared_world.py` with
the lemonade words and the raw action values in every framing: a post read `owner 1, round 1: location=stadium,
sugar=2.0, lemon=5.5, colour=green, price=3.5 -> earned 80.4` under a header describing the agents as stand owners in
the same town. The alien framing (added 2026-10-21) changed the system prompt, the history lines and the parser to the
A-E vocabulary but not the board. So in every alien sharing condition the agents saw the lemonade variable names, the
real location names and the real colour names on the board, while the alien working-alone condition, which has no
board, saw none of them. The confound was noticed on 2026-10-21 (RESULTS.md entry of that day, "a confound in the
labels"), recorded as a limitation, and not fixed. The paper's limitations paragraph then said the within-framing
contrasts were unaffected because the detail applied to every alien condition; that is false for the contrasts
against working alone. The user asked on 2026-11-20 for the fix and the rerun.

**The fix** (`experiments/shared_world.py`; the copy before the change is
`results/multiagent/backup_before_reps_2026-11-04/shared_world.py.before_board`, identical to the public release's
first commit). Posts are kept as structured records and rendered at display time through the same `Vocabulary` the
agent's prompt uses (`agents/vocab.for_world`). In the lemonade framing the rendering is the pilot's wording, byte for
byte. In the alien framing a post reads `operator 1, round 1: A=A1, B=2.0, C=5.5, D=D1, E=3.5 -> payoff 80.4`, the
header reads "You and 2 other operators each run a business of the same kind and post what you tried and what it
earned", and the stay-different instruction says "another operator's approach". The board leader used for the
herding metric is taken from the structured record, so `copied_leader_rounds` and `board_leader_locations` are
computed exactly as before. A guard now runs on every call in the alien framing and raises if any message contains a
lemonade word, a location name or a colour name (`assert_no_lemonade`); the alien system prompt's own phrase "a
business with five decision variables" is allowed, a location of that name as a value is not. Checked offline with a
stub client: lemonade sharing, staggered and protocol teams give records and prompts identical to the pre-fix code;
alien sharing, staggered and protocol teams send no prompt containing any forbidden word.

**What is rerun.** Every alien arm with a board, with the same worlds, repeats, models and horizons as the runs it
replaces, so that every analysis script and every table regenerates from the same file names:

| arm | model | worlds | runs | team-episodes |
|---|---|---|---|---|
| share_alien | gpt-5.6-sol | 8 | 3 | 24 |
| share_from3_alien, share_from6_alien, share_from11_alien, share_from16_alien | gpt-5.6-sol | 8 | 2 | 16 each |
| share_at6-11-16_alien | gpt-5.6-sol | 24 (pilot 8 and val[16:32]) | 3 | 72 |
| share_protocol_alien, share_staggered_alien | gpt-5.6-sol | 8 | 2 | 16 each |
| share_alien_h60 | gpt-5.6-sol, 60 rounds | 8 | 3 | 24 |
| share_alien, share_at6-11-16_alien | claude-opus-5-5 | 8 | 2 | 16 each |

Working alone in the alien framing has no board and is not rerun. Nothing in the lemonade framing is rerun. The
pre-fix alien sharing files and their spend files are moved, not deleted, to
`results/multiagent/alien_board_leak_2026-11-20/` with a README; they are not analysed. Launcher:
`scripts/run_multiagent_alien_board.sh` (detached, one copy, resumable, caps enforced per episode), which ends by
regenerating every analysis that reads an alien sharing arm.

**Budget.** At the measured rates ($0.76 per 20-round team-episode on GPT-5.6, about $1.00 on Claude, $4.20 per
60-round team-episode): 192 GPT team-episodes at 20 rounds ($146), 32 Claude team-episodes ($32), 24 GPT team-episodes
at 60 rounds ($101), about $280 in all. Caps, in `results/multiagent/logs/alienfix_cap__<arm>__<model>.txt`:
share_alien 25; each of from3, from6, from11, from16, protocol, staggered 18; share_at6-11-16_alien 70;
share_alien_h60 125; Claude share_alien 22 and share_at6-11-16_alien 22; $372 in all. Allowance $375 (project cap
$1,255 -> $1,630). If a cap stops an arm early, the worlds it completed are analysed and that is reported.

**Analysis.** Unchanged: the scripts, contrasts, tests and file names fixed in the earlier addenda
(`stats_multiagent_reps.py`, `writeup_numbers_multiagent.py`, `run_means_multiagent.py`, `stats_worlds24.py`,
`stats_claude.py`, `stats_h60.py`, `arxiv_sharing_tables.py`) run on the new files. No direction is pre-specified for
how the alien numbers move; whatever they are, they replace the pre-fix alien numbers in the paper, and the limitation
about the board's wording is removed from the paper as no longer true.

**Process note, 2026-11-20 08:43 UTC: complete.** Launched 08:05 UTC, all eleven arms complete by 08:43 UTC, no cap
stop, every analysis regenerated by the launcher. Spend $242.44 of the $375 allowance (GPT 20-round arms $121.66,
GPT 60-round arm $99.67, Claude $21.11); project total $1,268.16 of the $1,630 cap. Replay check over every recorded
alien sharing episode (216 team-episodes at the time, all 232 after the last arm finished): the rebuilt system prompts,
histories and complete boards contain no lemonade word, location name or colour name. Numbers and the reading in
`docs/RESULTS.md`, entry 2026-11-20 (alien board rerun, results).
