"""Shared-workspace agents in the lemonade world (exploratory pilot; see docs/PILOT_MULTIAGENT.md).

k identical agents play the same world, each running its own stand, and post what they tried and what it earned to
one shared board. This is the minimal test-time communication setting of Park et al. (arXiv 2609.21032) placed in an
environment whose verifier misranks progress: the route to the best strategy pays less than the recommended default
until the recipe is fixed.

Reuses, unchanged: the API client, cost accounting and spend cap of evaluation/frontier_sweep.py, the prompt of
agents/llm_agent.build_messages, the strict parser, the environment and analysis/metrics.py. The board is appended to
the user message by this file, so no paper code is modified.

    .venv/bin/python experiments/shared_world.py --arm share --worlds 8 --cap 40
    .venv/bin/python experiments/shared_world.py --arm share --horizon 60 --reps 3 --cap 140   # 60-round game

Writes results/multiagent/<arm>__<model>.jsonl, one record per episode (one agent in one team), and a spend file.
Re-running skips episodes already in the file, so an interrupted run resumes.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import pathlib
import sys
import threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.llm_agent import build_messages, parse_action  # noqa: E402
from analysis import metrics as M  # noqa: E402
from env.lemonade_env import LemonadeEnv  # noqa: E402
from env.world_generator import load_world_set, world_id  # noqa: E402
from evaluation.frontier_sweep import Client, MODELS, Spend, cost, load_cache  # noqa: E402

OUT = ROOT / "results" / "multiagent"
WORLDS = ROOT / "data" / "worlds_main.json"
HORIZON = 20
PROMPT, LABEL, HINT = "neutral", "semantic", True      # the paper's main cell
LETTER = True                                          # the previous manager's letter is shown


def setup_suffix(label, hint, letter):
    """What to append to the arm name so a rerun under a different setup gets its own file.

    The resume cache keys on model, arm, world, repeat and agent, so two setups sharing an
    arm name would silently skip each other's episodes and land in one file. Anything that
    differs from the paper's main cell therefore earns a suffix.
    """
    if label == "alien" and not letter:
        return "_alien"                  # the advisor's alien version: A-E labels, no letter
    parts = [] if label == "semantic" else [label]
    # the hint is a sentence inside the letter, so with no letter there is no hint to name
    parts += (([] if hint else ["nohint"]) if letter else ["noletter"])
    return ("_" + "-".join(parts)) if parts else ""

BOARD_INTRO = ("Shared notes board. You and {others} other stand owners run your own stands in the same town and post "
               "what you tried and what it earned. Everything below is a measured result, not an opinion.")
PROTOCOL = (
    "\nHow to use the board: pick an approach that is different from the ones already claimed above. Adopt another "
    "owner's approach only after their posted result is clearly better than yours, and when you do, keep one "
    "deliberate variation of your own rather than copying it exactly.")


def board_text(posts, k, protocol):
    """The shared board as the agents see it: every agent's action and profit, most recent last."""
    if not posts:
        body = "No results posted yet."
    else:
        body = "\n".join(posts)
    out = BOARD_INTRO.format(others=k - 1) + "\n" + body
    return out + (PROTOCOL if protocol else "")


def post_line(agent, rnd, action, profit):
    return (f"owner {agent}, round {rnd}: location={action['location']}, sugar={action['sugar']}, "
            f"lemon={action['lemon']}, colour={action['color']}, price={action['price']} -> earned {profit:.1f}")


def with_board(msgs, text):
    """Append the board to the user turn; the system prompt is left exactly as the paper's."""
    out = [dict(m) for m in msgs]
    out[-1]["content"] = out[-1]["content"] + "\n\n" + text
    return out


def run_team(client, world, wid, rep, k, share, protocol, seed0, share_from=1, stagger=False, share_at=None,
             label=LABEL, hint=HINT, letter=LETTER, horizon=HORIZON):
    """One team episode: k agents, lockstep rounds, one shared board.

    k = 1 and share = False is the solo arm. `share_from` is the first round in which the board is visible: earlier
    rounds are private, so each agent explores alone before anyone can copy. Results are posted from round 1 either
    way, so the board that opens at `share_from` already carries the private history. `share_at`, when given, replaces
    `share_from`: the board is visible only in those rounds (e.g. 6, 11, 16), and private in every other round.

    `horizon` is the number of rounds the agents are told they have and play (20 in every arm of the paper; 60 in the
    horizon addendum of 2026-11-19). A round's prompt says "Round r of {horizon}", so a longer game is a different
    arm with its own result file, never a continuation of a shorter one.

    In the simultaneous setting the k agents of a round choose from the same board and cannot see each other's
    choice for that round, so their API calls are independent and are made at the same time (2026-11-19, for speed;
    the prompts, seeds, posting order and records are exactly what the sequential loop produced). The staggered
    setting keeps the sequential loop, since each mover there sees the earlier movers' results from this round.
    """
    envs = []
    for i in range(k):
        e = LemonadeEnv(world=world, horizon=horizon, seed=seed0 + 97 * i)
        e.reset()
        envs.append(e)
    posts, raw, oks = [], [[] for _ in range(k)], [[] for _ in range(k)]
    usage_tot = [{"input": 0, "output": 0, "reasoning": 0, "cached_input": 0, "refusals": 0} for _ in range(k)]
    dollars, params_used = 0.0, None
    board_leader = []          # the location of the best posted result at the time of each choice, for herding
    copied = [0] * k

    def ask(i, text_now, visible):
        msgs = build_messages(world, PROMPT, envs[i].history, horizon, label=label, hint=hint, letter=letter)
        if visible:
            msgs = with_board(msgs, text_now)
        return client.generate(msgs)

    def take(i, reply, best_loc):
        nonlocal dollars, params_used
        text, usage, params_used = reply
        for key in usage_tot[i]:
            usage_tot[i][key] += usage.get(key, 0)
        dollars += cost(client.model, usage)
        fallback = envs[i].history[-1].action if envs[i].history else world.default_action
        act, ok = parse_action(text, world, fallback, label=label)
        raw[i].append(text[-400:])
        oks[i].append(bool(ok))
        if best_loc is not None and act["location"] == best_loc:
            copied[i] += 1
        return act

    for rnd in range(1, horizon + 1):
        chosen = [None] * k
        visible = share and (rnd in share_at if share_at else rnd >= share_from)
        # simultaneous (default): everyone chooses from the board as it stood at the end of the previous round.
        # staggered: agents move one at a time in a rotating order, each seeing what earlier movers did this round.
        order = [(rnd - 1 + i) % k for i in range(k)] if stagger else list(range(k))
        text_now = board_text(posts, k, protocol) if visible else None
        best_loc = leader_location(posts) if (posts and visible) else None
        board_leader.append(best_loc)
        if stagger:
            for i in order:
                if visible:                                  # refresh for each mover
                    text_now = board_text(posts, k, protocol)
                    best_loc = leader_location(posts) if posts else None
                act = take(i, ask(i, text_now, visible), best_loc)
                chosen[i] = act
                res = envs[i].step(act)                      # play and post immediately, so the next mover sees it
                if share:
                    posts.append(post_line(i + 1, rnd, act, res.profit))
        else:
            if k == 1:
                replies = [ask(0, text_now, visible)]
            else:
                with cf.ThreadPoolExecutor(k) as ex:
                    replies = list(ex.map(lambda i: ask(i, text_now, visible), order))
            for i, reply in zip(order, replies):             # agent order, as before
                chosen[i] = take(i, reply, best_loc)
            for i in range(k):
                res = envs[i].step(chosen[i])
                if share:
                    posts.append(post_line(i + 1, rnd, chosen[i], res.profit))
    recs = []
    for i in range(k):
        ep = M.from_env(envs[i], parse_ok=oks[i])
        recs.append({"arm": arm_name(share, protocol, share_from, stagger, share_at) +
                            setup_suffix(label, hint, letter) + horizon_suffix(horizon), "share_from": share_from,
                     "stagger": stagger, "share_at": list(share_at) if share_at else None,
                     "model": client.model, "world_id": wid, "repeat": rep, "k": k, "agent": i + 1,
                     "horizon": horizon, "prompt": PROMPT, "label": label, "hint": hint, "letter": letter,
                     "usage": usage_tot[i], "parse_ok": oks[i], "raw_tail": raw[i][-3:],
                     "actions": [dict(h.action) for h in envs[i].history],
                     "profits": [round(h.profit, 4) for h in envs[i].history],
                     "copied_leader_rounds": copied[i], "board_leader_locations": board_leader,
                     "metrics": M.episode_metrics(ep), "params_used": params_used})
    return recs, dollars


def leader_location(posts):
    """Where the best posted result so far was earned."""
    best = max(posts, key=lambda p: float(p.rsplit("earned ", 1)[1]))
    return best.split("location=", 1)[1].split(",", 1)[0]


def arm_name(share, protocol, share_from, stagger=False, share_at=None):
    """solo, share, share_protocol, e.g. share_from6 when the board opens at round 6, or share_at6-11-16 when it is
    visible only in rounds 6, 11 and 16."""
    if not share:
        return "solo"
    base = "share_protocol" if protocol else "share"
    if stagger:
        base += "_staggered"
    if share_at:
        return f"{base}_at" + "-".join(str(r) for r in sorted(share_at))
    return base if share_from <= 1 else f"{base}_from{share_from}"


def horizon_suffix(horizon):
    """`_h60` for a 60-round game; nothing at the paper's 20 rounds, so every existing file name is unchanged."""
    return "" if horizon == HORIZON else f"_h{horizon}"


def key(model, arm, wid, rep, agent):
    return f"{model}|{arm}|{wid}|{rep}|{agent}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["solo", "share", "share_protocol"])
    ap.add_argument("--share-from", type=int, default=1, help="first round in which the board is visible")
    ap.add_argument("--share-at", type=lambda v: tuple(int(x) for x in v.split(",")), default=None,
                    help="comma-separated rounds in which the board is visible, e.g. 6,11,16 (overrides --share-from)")
    ap.add_argument("--stagger", action="store_true",
                    help="agents move one at a time in a rotating order, each seeing this round's earlier results")
    ap.add_argument("--model", default="gpt-5.6-sol", choices=list(MODELS))
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--worlds", type=int, default=8)
    ap.add_argument("--world-offset", type=int, default=0,
                    help="skip this many worlds of the split first, e.g. --world-offset 16 --worlds 16 is val[16:32]")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--split", default="val", choices=["val", "train"])   # never the test split
    ap.add_argument("--label", default=LABEL, choices=["semantic", "neutral", "misleading", "alien"],
                    help="vocabulary the world is described in; alien names the five choices A-E")
    ap.add_argument("--no-hint", dest="hint", action="store_false",
                    help="drop the previous manager's 'try another location' sentence")
    ap.add_argument("--no-letter", dest="letter", action="store_false",
                    help="drop the previous manager's letter, so there is no recommended setup at all")
    ap.add_argument("--alien", action="store_true",
                    help="shorthand for --label alien --no-letter (advisor, 12 Oct)")
    ap.add_argument("--horizon", type=int, default=HORIZON,
                    help="rounds per game, told to the agents and played (default 20, the paper's). Any other value "
                         "adds _h<horizon> to the arm name, so its episodes go to their own file")
    ap.add_argument("--cap", type=float, required=True, help="dollars this run may add, refuses to start an episode past it")
    ap.add_argument("--workers", type=int, default=int(os.environ.get("LEM_WORKERS", "1")),
                    help="team episodes run at once, as threads of this one process (default 1, or $LEM_WORKERS). "
                         "Episodes do not interact, so this changes the wall-clock time and nothing else")
    a = ap.parse_args()
    if a.alien:
        a.label, a.letter = "alien", False

    OUT.mkdir(parents=True, exist_ok=True)
    pool = load_world_set(WORLDS)[a.split][a.world_offset:a.world_offset + a.worlds]
    client = Client(a.model)
    name = arm_name(a.arm != "solo", a.arm == "share_protocol", a.share_from, a.stagger, a.share_at) + \
        setup_suffix(a.label, a.hint, a.letter) + horizon_suffix(a.horizon)
    path = OUT / f"{name}__{a.model}.jsonl"
    spend = Spend(OUT / f"spend__{name}__{a.model}.json", a.cap)
    done = load_cache(path)
    k = 1 if a.arm == "solo" else a.k
    share = a.arm != "solo"
    protocol = a.arm == "share_protocol"
    # the solo arm needs k independent runs per world so that best@k is comparable with one team episode
    runs = [(w, rep, agent) for w in pool for rep in range(a.reps) for agent in (range(a.k) if a.arm == "solo" else [0])]

    # What one team episode is expected to add, used only to refuse starting an episode that
    # would cross the cap. The 0.15 was measured on gpt-5.6-sol, so it is scaled by the
    # model's output price; without that a cheap model would be refused at a sane cap.
    est = 0.15 * (k if share else 1) * MODELS[a.model]["out"] / MODELS["gpt-5.6-sol"]["out"]
    # Every round's prompt carries the whole history, so an episode's input tokens grow with the square of the
    # horizon; the first-episode guess is scaled the same way. After the first episode the measured cost takes over.
    est *= (a.horizon / HORIZON) ** 2
    # One process owns an arm; its episodes may run as threads. The lock covers the cap check, the spend file and
    # the results file, so the accounting is exact with any number of workers. `reserved` is money promised to
    # episodes in flight: an episode starts only if the cap still holds with every running episode paid for.
    lock, reserved, stop = threading.Lock(), [0.0], threading.Event()

    def one(w, rep, agent):
        wid = world_id(w)
        tag = f"{rep}.{agent}" if a.arm == "solo" else str(rep)
        with lock:
            if stop.is_set():
                return "skipped"
            # re-read the file each time: another copy may have written since this one started
            cache = load_cache(path)
            if key(a.model, name, wid, tag, 1) in cache:
                return "cached"
            need = est
            if a.workers > 1:      # with several in flight, reserve what an episode of this arm has really cost
                need = max(est, 1.25 * spend.total / max(1, len(cache) / (k if share else 1)))
            if spend.total + reserved[0] + need > a.cap:
                print(f"stopping: ${spend.total:.2f} spent, ${reserved[0]:.2f} in flight, cap ${a.cap}", flush=True)
                stop.set()
                return "cap"
            reserved[0] += need
        try:
            recs, dollars = _team(w, wid, tag, rep, agent)
        except Exception as e:     # one failed episode must not take the others down; the launcher retries it
            with lock:
                reserved[0] -= need
            print(f"{name} {wid} rep {tag}: FAILED {type(e).__name__}: {str(e)[:200]}", flush=True)
            return "failed"
        with lock:
            reserved[0] -= need
            spend.add(name, dollars)
            with path.open("a") as f:
                for r in recs:
                    r["key"] = key(a.model, name, wid, tag, r["agent"])
                    r["dollars_team"] = round(dollars, 4)
                    f.write(json.dumps(r) + "\n")
            m = [r["metrics"] for r in recs]
            print(f"{name} {wid} rep {tag}: left {[int(x['left_anchor_ever']) for x in m]} "
                  f"escaped {[int(bool(x['escaped'])) for x in m]} "
                  f"pct_opt {[round(x['pct_optimum'], 2) for x in m]} (${dollars:.2f}, total ${spend.total:.2f})", flush=True)
        return "done"

    def _team(w, wid, tag, rep, agent):
        return run_team(client, w, wid, tag, k, share, protocol, share_from=a.share_from, stagger=a.stagger,
                        share_at=a.share_at, label=a.label, hint=a.hint, letter=a.letter, horizon=a.horizon,
                        seed0=5_000_000 + 1000 * (int(hashlib.sha256(wid.encode()).hexdigest()[:8], 16) % 997) + 13 * agent
                              + 7919 * rep)   # a repeat gets its own environment seeds; rep 0 is unchanged

    if a.workers <= 1:
        for w, rep, agent in runs:
            if one(w, rep, agent) == "cap":
                break
    else:
        with cf.ThreadPoolExecutor(a.workers) as pool:
            results = list(pool.map(lambda t: one(*t), runs))
        if "failed" in results:
            print(f"{results.count('failed')} episode(s) failed and are left for the next attempt", flush=True)
    print(f"done: {name}, ${spend.total:.2f}")


if __name__ == "__main__":
    main()
