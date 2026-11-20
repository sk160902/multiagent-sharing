"""Single source of truth for every behavioural metric in the paper.

Phase 0 found the same names computed three different ways across
`train_grpo.evaluate`, `frozen_model.py` and `llm_agent.py` (AUDIT §3.7).
Everything now routes through this module, and `tests/test_metrics.py` pins each
definition against a hand-computed case.

Two definitions changed from the pilot, both by explicit user decision on
2026-09-08 (DECISIONS.md), both *before* any confirmatory data was seen:

  * `pct_optimum` (co-primary outcome) is now the mean profit over the last
    `TAIL_WINDOW` rounds divided by the global optimum. The pilot used the
    episode *maximum*, which pays a policy that touches the optimum once in
    round 3 and then wanders off exactly what it pays one that ends there.
    The episode-max reading is kept as `pct_optimum_max` (secondary) so the
    pilot's Table 9 column remains reproducible.
  * `near_optimum` likewise gains a last-window variant. The episode-max form
    is retained under its original name for continuity with Table 9.

Metrics take an `Episode`, which is deliberately a plain data holder rather than
a live `LemonadeEnv`: the same code must run over rollouts replayed from JSONL
months later, when no `World` object exists any more.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

CONTINUOUS = ("sugar", "lemon", "price")
ACTION_KEYS = ("location", "sugar", "lemon", "color", "price")

# Window used by `pct_optimum`, `near_optimum_final` and `stayed_away`.
# Pre-registered; do not change after the confirmatory sweep starts (brief §3).
TAIL_WINDOW = 5


@dataclass
class Episode:
    """One rolled-out episode, detached from the environment that produced it.

    `anchor_profit` is the profit of the previous manager's strategy on this
    world. It is the baseline the H5 "valley" is measured against: an agent has
    taken the dip when it has accepted rounds below this number.
    """

    profits: list[float]
    actions: list[dict]
    anchor_action: dict
    gmax: float
    best_location: str
    anchor_profit: float
    feedback_signals: list[dict | None] = field(default_factory=list)
    parse_ok: list[bool] = field(default_factory=list)
    # Max profit achievable ANYWHERE at the anchor location -- not the anchor
    # action's profit. This is the ceiling of the trap, known exactly from the
    # world generator, and it is what `escaped` is measured against (PREREG v2,
    # user decision 2026-09-09).
    anchor_ceiling: float | None = None

    @property
    def anchor_location(self) -> str:
        return self.anchor_action["location"]

    @property
    def horizon(self) -> int:
        return len(self.profits)


def from_env(env, parse_ok: list[bool] | None = None) -> Episode:
    """Build an `Episode` from a live `LemonadeEnv` that has been rolled out."""
    _, gmax = env.world.global_optimum()
    anchor_loc = env.world.default_action["location"]
    return Episode(
        anchor_ceiling=env.world.locations[anchor_loc].max_profit,
        profits=[h.profit for h in env.history],
        actions=[dict(h.action) for h in env.history],
        anchor_action=dict(env.world.default_action),
        gmax=gmax,
        best_location=env.world.best_location(),
        anchor_profit=_anchor_profit(env.world),
        feedback_signals=[h.feedback_signal for h in env.history],
        parse_ok=list(parse_ok) if parse_ok is not None else [],
    )


def _anchor_profit(world) -> float:
    from env.lemonade_env import profit
    return profit(world, world.default_action)


# ---------------------------------------------------------------------------
# Outcome metrics
# ---------------------------------------------------------------------------
def pct_optimum(ep: Episode, window: int = TAIL_WINDOW) -> float:
    """CO-PRIMARY. Mean profit over the last `window` rounds, as a fraction of
    the global optimum. This is what Ederer-Manso's contracts actually pay."""
    tail = ep.profits[-window:]
    return (sum(tail) / len(tail)) / ep.gmax


def pct_optimum_max(ep: Episode) -> float:
    """SECONDARY. The pilot's `best_frac`: episode-maximum profit / optimum.
    Retained only so Table 9 stays reproducible."""
    return max(ep.profits) / ep.gmax


def near_optimum(ep: Episode, frac: float = 0.9) -> bool:
    """SECONDARY, pilot definition: did any single round reach `frac` of optimum."""
    return max(ep.profits) >= frac * ep.gmax


def near_optimum_final(ep: Episode, frac: float = 0.9,
                       window: int = TAIL_WINDOW) -> bool:
    """SECONDARY. The last-window analogue of `near_optimum`."""
    return pct_optimum(ep, window) >= frac


def tail_profit(ep: Episode) -> float:
    """Mean profit over the second half of the episode. Identical to
    `lemonade_env.reward_deferred`; kept because Table 9 reports it."""
    half = ep.horizon // 2
    tail = ep.profits[half:]
    return sum(tail) / len(tail)


# ---------------------------------------------------------------------------
# Escape metrics
# ---------------------------------------------------------------------------
def escaped(ep: Episode, window: int = TAIL_WINDOW) -> bool | None:
    """CO-PRIMARY escape measure (PREREG v2). Did the agent get out of the trap?

    True when mean profit over the last `window` rounds exceeds **the anchor
    location's ceiling** -- the best profit obtainable anywhere at the starting
    location. That ceiling is known exactly from the world generator, so this is
    a statement about the landscape rather than about the agent's own history.

    Why this replaced `stayed_away` as the escape measure: under a prompt that
    *instructs* the agent to try other locations, `stayed_away` is satisfied by
    wandering. Simply being elsewhere is not escaping a trap; out-earning
    everything the trap could ever have paid is. It is also the literal reading
    of Ederer-Manso's question, and it cannot be gamed by an instruction.

    Returns None when the ceiling is unknown (an Episode replayed from a log
    written before this field existed).
    """
    if ep.anchor_ceiling is None:
        return None
    tail = ep.profits[-window:]
    return (sum(tail) / len(tail)) > ep.anchor_ceiling


def directive_compliance(ep: Episode, first_n: int = 5,
                         min_other: int = 2) -> bool:
    """SECONDARY (PREREG v2). Did the agent actually follow the instruction?

    True when at least `min_other` locations other than the anchor are tried
    within the first `first_n` rounds -- exactly what `explore_directed` asks
    for. Expected to **fall** under the immediate reward, which pays for mean
    profit and so pays for disobeying, and to **hold** under the terminal
    reward. That divergence is the H2 figure.
    """
    head = ep.actions[:first_n]
    return len({a["location"] for a in head} - {ep.anchor_location}) >= min_other


def stayed_away(ep: Episode, window: int = TAIL_WINDOW) -> bool:
    """CO-PRIMARY (episode level). The agent is somewhere other than the
    previous manager's location for every one of the last `window` rounds.

    Note what this does NOT require: it says nothing about the middle of the
    episode. An agent that leaves in round 1 and one that leaves in round 18
    both count. That is deliberate -- the hypothesis is about where the policy
    ends up, and `first_location_change_round` carries the timing separately.
    """
    return all(a["location"] != ep.anchor_location for a in ep.actions[-window:])


def left_anchor_ever(ep: Episode) -> bool:
    return any(a["location"] != ep.anchor_location for a in ep.actions)


def left_anchor_by(ep: Episode, rounds: int = 5) -> bool:
    """Did the agent try another location within the first `rounds` rounds.

    This is the quantity the Phase 1.5 seed-rate sweep maximises: GRPO cannot
    reinforce an escape that never appears in a group (brief §4.1).
    """
    return any(a["location"] != ep.anchor_location for a in ep.actions[:rounds])


def reached_best_location(ep: Episode) -> bool:
    return any(a["location"] == ep.best_location for a in ep.actions)


def first_location_change_round(ep: Episode) -> int | None:
    """1-indexed round of the first action at a non-anchor location, else None."""
    for i, a in enumerate(ep.actions):
        if a["location"] != ep.anchor_location:
            return i + 1
    return None


def vars_changed_at_first_move(ep: Episode) -> int | None:
    """How many of the five variables changed on the round the agent first moved.

    A move that changes only the location keeps a recipe tuned for the old one
    and lands in the valley; a move that changes the recipe too is a different
    -- and much better informed -- kind of exploration. H5 needs to tell them
    apart.
    """
    r = first_location_change_round(ep)
    if r is None:
        return None
    new = ep.actions[r - 1]
    prev = ep.actions[r - 2] if r >= 2 else ep.anchor_action
    return sum(new[k] != prev[k] for k in ACTION_KEYS)


# ---------------------------------------------------------------------------
# Breadth metrics (H2)
# ---------------------------------------------------------------------------
def distinct_actions(ep: Episode) -> int:
    return len({tuple(sorted(a.items())) for a in ep.actions})


def distinct_locations(ep: Episode) -> int:
    return len({a["location"] for a in ep.actions})


def action_entropy(ep: Episode) -> float:
    """Shannon entropy (nats) of the distribution over distinct full actions.

    `distinct_actions` alone cannot separate a policy that plays 15 actions once
    each from one that plays 2 actions and repeats the first 14 times but is
    credited with 15 -- entropy can.
    """
    counts: dict[tuple, int] = {}
    for a in ep.actions:
        k = tuple(sorted(a.items()))
        counts[k] = counts.get(k, 0) + 1
    n = len(ep.actions)
    return -sum((c / n) * math.log(c / n) for c in counts.values())


# ---------------------------------------------------------------------------
# Mechanism metrics (H5 -- the valley)
# ---------------------------------------------------------------------------
def dip(ep: Episode) -> dict:
    """The valley: does the agent accept profit below the anchor's before rising?

    Ederer-Manso's whole point is that the superior strategy is reachable only
    through a region of worse payoffs. Measured against `anchor_profit`, the
    profit the agent could have banked every round by doing nothing.

    Returns:
      depth            largest shortfall below the anchor's profit (0 if never below)
      round            1-indexed round of that largest shortfall (None if never)
      rounds_below     how many rounds were spent below the anchor's profit
      exceeded_round   first round strictly above the anchor's profit after a dip
      dip_precedes_escape  the deepest dip happened at or before the first move
    """
    below = [(i + 1, ep.anchor_profit - p)
             for i, p in enumerate(ep.profits) if p < ep.anchor_profit]
    if not below:
        return {"depth": 0.0, "round": None, "rounds_below": 0,
                "exceeded_round": None, "dip_precedes_escape": False}
    r_deep, depth = max(below, key=lambda t: t[1])
    exceeded = None
    for i, p in enumerate(ep.profits):
        if i + 1 > r_deep and p > ep.anchor_profit:
            exceeded = i + 1
            break
    move = first_location_change_round(ep)
    return {"depth": depth, "round": r_deep, "rounds_below": len(below),
            "exceeded_round": exceeded,
            "dip_precedes_escape": move is not None and r_deep <= move}


# ---------------------------------------------------------------------------
# Process metrics
# ---------------------------------------------------------------------------
def feedback_adherence(ep: Episode) -> tuple[float | None, int]:
    """Fraction of directional hints the agent then moved the right way.

    Only counted where the agent stayed put, because feedback is
    location-specific. Same definition as `llm_agent.feedback_adherence`;
    reimplemented here against `Episode` so it works on replayed rollouts.
    """
    hits = total = 0
    for i in range(len(ep.actions) - 1):
        sig = ep.feedback_signals[i] if i < len(ep.feedback_signals) else None
        if not sig or sig.get("direction", 0) == 0:
            continue
        prev, nxt = ep.actions[i], ep.actions[i + 1]
        if nxt["location"] != prev["location"]:
            continue
        v = sig["var"]
        delta = nxt[v] - prev[v]
        if abs(delta) < 1e-9:
            continue
        total += 1
        if (delta < 0) == (sig["direction"] > 0):
            hits += 1
    return ((hits / total) if total else None), total


def anchoring(ep: Episode, first_n: int = 5) -> dict:
    head = ep.actions[:first_n]
    if not head:
        return {"same_location_rate": None, "identical_action_rate": None}
    same_loc = sum(a["location"] == ep.anchor_location for a in head) / len(head)
    same_all = sum(all(a[k] == ep.anchor_action[k] for k in ACTION_KEYS)
                   for a in head) / len(head)
    return {"same_location_rate": same_loc, "identical_action_rate": same_all}


def parse_failure_rate(ep: Episode) -> float | None:
    """Fraction of rounds where the model's output did not parse cleanly and the
    previous action was silently reused. Brief §3 requires this on every table."""
    if not ep.parse_ok:
        return None
    return 1.0 - (sum(bool(x) for x in ep.parse_ok) / len(ep.parse_ok))


# ---------------------------------------------------------------------------
# Roll-ups
# ---------------------------------------------------------------------------
def episode_metrics(ep: Episode) -> dict:
    """Every metric for one episode, flat, JSON-serialisable."""
    adh, adh_n = feedback_adherence(ep)
    d = dip(ep)
    anch = anchoring(ep)
    return {
        "pct_optimum": pct_optimum(ep),
        "pct_optimum_max": pct_optimum_max(ep),
        "near_optimum": near_optimum(ep),
        "near_optimum_final": near_optimum_final(ep),
        "tail_profit": tail_profit(ep),
        "escaped": escaped(ep),
        "directive_compliance": directive_compliance(ep),
        "stayed_away": stayed_away(ep),
        "left_anchor_ever": left_anchor_ever(ep),
        "left_anchor_by_r5": left_anchor_by(ep, 5),
        "reached_best_location": reached_best_location(ep),
        "first_location_change_round": first_location_change_round(ep),
        "vars_changed_at_first_move": vars_changed_at_first_move(ep),
        "distinct_actions": distinct_actions(ep),
        "distinct_locations": distinct_locations(ep),
        "action_entropy": action_entropy(ep),
        "dip_depth": d["depth"],
        "dip_round": d["round"],
        "rounds_below_anchor": d["rounds_below"],
        "dip_exceeded_round": d["exceeded_round"],
        "dip_precedes_escape": d["dip_precedes_escape"],
        "feedback_adherence": adh,
        "feedback_adherence_n": adh_n,
        "anchor_same_location_rate": anch["same_location_rate"],
        "anchor_identical_action_rate": anch["identical_action_rate"],
        "parse_failure_rate": parse_failure_rate(ep),
        "final_profit": ep.profits[-1],
        "anchor_profit": ep.anchor_profit,
        "anchor_ceiling": ep.anchor_ceiling,
        "gmax": ep.gmax,
    }


def aggregate(rows: list[dict]) -> dict:
    """Mean over episodes, skipping Nones. Booleans average to a rate.

    Every key keeps an `_n` companion so a mean over 3 usable values is never
    mistaken for a mean over 64 (this bit the pilot's feedback-adherence column).
    """
    out: dict = {}
    for k in rows[0] if rows else []:
        vals = [r[k] for r in rows if r.get(k) is not None]
        out[f"{k}_n"] = len(vals)
        if not vals:
            out[k] = None
        elif isinstance(vals[0], bool):
            out[k] = sum(bool(v) for v in vals) / len(vals)
        elif isinstance(vals[0], (int, float)):
            out[k] = sum(vals) / len(vals)
        else:
            out[k] = None
    return out


# ---------------------------------------------------------------------------
# Run-level outcome (the unit of replication -- brief §3 rule 1)
# ---------------------------------------------------------------------------
ESCAPE_THRESHOLD = 0.5


def run_escaped(episode_rows: list[dict], threshold: float = ESCAPE_THRESHOLD,
                key: str = "escaped") -> bool:
    """KEY SECONDARY (run level). A *run* escaped when `escaped` holds in at
    least `threshold` of its test episodes. Pre-registered at 0.5 (PREREG v2).

    `key` defaults to the v2 measure; pass "stayed_away" to reproduce the v1
    number for a run logged before the change.
    """
    vals = [bool(r[key]) for r in episode_rows if r.get(key) is not None]
    return bool(vals) and (sum(vals) / len(vals)) >= threshold
