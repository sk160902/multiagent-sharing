# Teams That Share Explore Less

Code, data and paper source for *Teams That Share Explore Less: Information Sharing among LLM Agents Searching for a Hidden
Optimum* (Krishnan, Park and Nagaraj, 2026).

Teams of three LLM agents play a reimplementation of the Ederer and Manso lemonade-stand game, each running its
own stand in the same hidden world, under conditions that differ only in when a shared board of every teammate's
setups and profits is visible. The paper's result is that sharing cuts the number of distinct setups a team tries
roughly in half, raises what the team earns over the game, and never raises the best single round it finds.

## Layout

```
env/                 the game: profit landscape, episode loop, randomised worlds and the trap invariant
agents/              prompt rendering (lemonade and alien framings) and the strict action parser
analysis/metrics.py  every behavioural measure, computed from the action and profit traces
evaluation/frontier_sweep.py   API clients (OpenAI, Anthropic, Google), cost accounting, spend cap
experiments/shared_world.py    the multi-agent experiment: k agents, lockstep rounds, one shared board
scripts/             launchers for each block of runs (detached, resumable, per-arm dollar caps)
paper/scripts/       the fixed analyses and the table generator for the paper
data/worlds_main.json          the world set; the pilot worlds are val[:8], the extension worlds val[16:32]
results/multiagent/  one JSONL record per agent-episode for every condition, spend files, statistics output;
                     alien_board_leak_2026-11-20/ holds the alien sharing runs made before the board was
                     rendered in the alien vocabulary (kept for the record, not analysed; see its README)
docs/PILOT_MULTIAGENT.md       the pre-registration document: design, metrics and analysis fixed before each run
arxiv/lemonade_sharing_arxiv/  LaTeX source of the paper; every number is a generated macro
```

## Reproducing the paper's numbers

Everything in the paper is regenerated from `results/multiagent/*.jsonl` by scripts that take no arguments.
Python 3.8 or later with `numpy` is enough; the two figure scripts also need `matplotlib` 3.5 or later.

```bash
python3 paper/scripts/stats_multiagent_reps.py      # nine conditions, both framings, 8 worlds -> stats_reps.{json,md}
python3 paper/scripts/writeup_numbers_multiagent.py # per-world tables, reach rates, agreement -> writeup_numbers.json
python3 paper/scripts/run_means_multiagent.py       # per-run condition means and their spread -> writeup_run_means.json
python3 paper/scripts/stats_worlds24.py             # periodic board vs alone on 24 worlds, alien framing
python3 paper/scripts/stats_worlds24.py lemonade    # the same in the lemonade framing
python3 paper/scripts/stats_claude.py               # three conditions on Claude Opus 5.5 beside GPT-5.6
python3 paper/scripts/stats_h60.py                  # 60-round games
python3 paper/scripts/arxiv_sharing_tables.py       # writes arxiv/lemonade_sharing_arxiv/tables/*.tex and numbers.tex
python3 paper/scripts/fig_multiagent_reps.py        # fig_sharing_intervals.png
python3 paper/scripts/fig_multiagent_timing_runs.py # fig_sharing_timing_runs.png
```

The statistics are paired over worlds: a world's value is the mean over its runs, the contrast is a sharing
condition minus working alone within each world, and the test is the exact two-sided sign-flip permutation test
over worlds with a 95% t interval. Unit, contrasts and measures were fixed in `docs/PILOT_MULTIAGENT.md` before
the runs they cover.

## Running the experiment

`experiments/shared_world.py` plays one arm. It reads API keys from a `working_apis/` folder at the repository
root (not included): `api_key.txt` for OpenAI, `api_key_anthropic_ucb.txt` for Anthropic, `api_key_gemini_2.txt`
for Google. It writes one record per agent-episode to `results/multiagent/<arm>__<model>.jsonl` and a spend
file, skips every episode already recorded, and refuses to start an episode that would pass the dollar cap
given on the command line.

```bash
python3 experiments/shared_world.py --arm solo  --worlds 8 --reps 3 --cap 15
python3 experiments/shared_world.py --arm share --worlds 8 --reps 3 --cap 40
python3 experiments/shared_world.py --arm share --share-at 6,11,16 --alien --worlds 8 --reps 3 --cap 40
python3 experiments/shared_world.py --arm share --horizon 60 --worlds 8 --reps 3 --cap 140
```

`--alien` selects the alien framing (variables A to E, no letter). `--share-from N` opens the board at round N,
`--share-at 6,11,16` shows it only in those rounds, `--stagger` moves agents one at a time, `--arm share_protocol`
adds the stay-different instruction, `--horizon 60` plays a 60-round game under its own arm name. The launchers
in `scripts/` run the blocks reported in the paper detached and resumable, with per-arm caps read from
`results/multiagent/logs/`.

## Record format

Each line of a results file is one agent in one team episode: the arm, model, world id, repeat, agent index,
the 20 (or 60) actions and profits, parse flags, token usage, the board leader's location at each round, how
often the agent chose that location, and the per-episode metrics of `analysis/metrics.py`. The key
`model|arm|world|repeat|agent` makes every record unique and lets a stopped run resume.

## Citation

```
@article{krishnan2026teams,
  title   = {Teams That Share Explore Less: Information Sharing among LLM Agents Searching for a Hidden Optimum},
  author  = {Krishnan, Shreyas and Park, Jongho and Nagaraj, Abhishek},
  year    = {2026},
  note    = {arXiv preprint}
}
```
