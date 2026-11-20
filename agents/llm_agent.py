"""Frozen-LLM agent for the lemonade stand.

The model sees the previous manager's letter (so anchoring is measurable), the
full round-by-round history, and one of several instruction conditions. It is
never told the optimum.

Rollouts are stepped in lockstep across a batch of episodes -- every episode
generates its round-t action in one batched forward pass -- because 20
sequential rounds per episode is otherwise dominated by generation latency.
"""
from __future__ import annotations

import json
import re

from agents.vocab import for_world
from env.lemonade_env import COLORS, CONTINUOUS

# Instruction framings.
#
# ELIGIBLE conditions may be used as the common training prompt: they are
# identical across arms and say nothing about how profit is rewarded, weighted
# or paid. REFERENCE conditions reveal the reward structure and exist only as
# comparison rows -- adopting one would tell the model which arm it is in, which
# is exactly what brief §4.1 forbids.
ELIGIBLE = ("neutral", "explore_ok", "explore_directed", "reflect", "fewshot")
REFERENCE = ("every_round", "protected", "final_only")

CONDITIONS = {
    # -- reference only: each states how profit is scored ------------------
    "every_round": "Your goal is to maximise profit on EVERY round, including the early ones.",
    "protected": ("You have a protected experimentation period: rounds 1-{half} do not "
                  "count towards your score. Use them to experiment. From round {half1} "
                  "onward, maximise profit."),
    "final_only": "Only your FINAL round's profit counts towards your score. Earlier rounds do not.",

    # -- eligible: task framing only, silent about the reward --------------
    "neutral": "Your goal is to maximise the overall performance of the {org_word}.",
    "explore_ok": ("Your goal is to maximise the overall performance of the {org_word}. "
                   "It is acceptable to try other {loc_word}s early and to adapt the "
                   "{recipe_word} to them."),
    "explore_directed": ("Your goal is to maximise the overall performance of the "
                         "{org_word}. Try at least two other {loc_word}s within the "
                         "first five rounds, adapting the {recipe_word} to each one."),
    "reflect": ("Your goal is to maximise the overall performance of the {org_word}. "
                "Before answering, write one short sentence stating what you have "
                "learned so far and what you will test next. Then give the JSON."),
    "fewshot": ("Your goal is to maximise the overall performance of the {org_word}. "
                "Below is a transcript from a different {domain_word}, for reference."),
}

# Rendered through a `Vocabulary` (agents/vocab.py) so the same environment can
# be described with lemonade labels, abstract dials, or permuted lemonade labels.
# The semantic vocabulary reproduces the pilot's wording byte for byte; that is
# pinned by tests/test_vocab.py against tests/fixtures/prompt_baseline.json.
SYSTEM = (
    "You run a {domain} for {horizon} rounds. Each round you choose a full "
    "{config_noun} and observe the {gain_word} plus a {fb_noun}.\n\n"
    "Choices:\n"
    "  {v_loc}: one of {locations}\n"
    "  {v_sugar}:    a number 0.0-10.0 (one decimal)\n"
    "  {v_lemon}:    a number 0.0-10.0 (one decimal)\n"
    "  {v_color}:    {c_a} or {c_b}\n"
    "  {v_price}:    a number 0.0-10.0 (one decimal)\n\n"
    "{letter_block}"
    "{condition}\n\n"
    "Reply with ONLY a JSON object, no other text:\n"
    '{{"{v_loc}": "...", "{v_sugar}": 0.0, "{v_lemon}": 0.0, "{v_color}": "...", "{v_price}": 0.0}}'
)

# The previous manager's letter carries an explicit strategy hint ("Other
# locations may need a very different recipe"). Brief §1.4 requires it to be a
# separate on/off factor, so it is a separate sentence rather than baked in.
HINT = (" I tried many {recipe_word}s at that {loc_word} but never tried a "
        "different {loc_word}. Other {loc_word}s may need a very different "
        "{recipe_word}.")

_JSON = re.compile(r"\{[^{}]*\}", re.S)


def history_lines(history, v):
    """Render a round-by-round history in vocabulary `v`.

    Shared by the live prompt and by the few-shot demonstration, so a demo can
    never drift out of the format the model is actually asked to continue.
    """
    out = []
    for h in history:
        a = h.action
        out.append(
            f"  round {h.round:2d}: {v.loc_word}={v.loc_out(a['location'])}, "
            f"{v.var_out('sugar')}={a['sugar']}, "
            f"{v.var_out('lemon')}={a['lemon']}, "
            f"{v.color_key}={v.color_out(a['color'])}, "
            f"{v.var_out('price')}={a['price']} "
            f"-> {v.gain_word} {h.profit:.1f}. {v.feedback_text(h.feedback_signal)}")
    return out


def build_messages(world, condition_key, history, horizon, label="semantic",
                   hint=True, demo_text=None, letter=True):
    """Render the prompt for one round.

    `label` selects the vocabulary (semantic / neutral / misleading); `hint`
    toggles the previous manager's explicit "try another location" sentence,
    which brief §1.4 requires be treated as its own factor.

    `letter=False` removes the previous manager's letter entirely, so the model is
    given no recommended setup to start from and nothing to anchor on. The rest of
    the prompt is unchanged and the world is unchanged: `world.default_action` still
    defines the anchor that the metrics measure departure from, it is simply never
    shown. Asked for by the advisor on 12 Oct for the alien setup, where the point is
    to raise the spread of where agents begin. With `letter=True` (the default) the
    rendered prompt is byte for byte what it was before this flag existed, which
    tests/test_vocab.py pins against tests/fixtures/prompt_baseline.json.
    """
    v = for_world(label, world)
    anchor = world.default_action
    from env.lemonade_env import profit as _p
    half = horizon // 2
    loc_word, recipe_word = v.loc_word, v.recipe_word
    cond = CONDITIONS[condition_key].format(
        half=half, half1=half + 1, org_word=v.org_word, loc_word=loc_word,
        recipe_word=recipe_word, domain_word=v.domain_word)
    if demo_text:
        cond = cond + "\n\n" + demo_text
    if letter:
        body = (
            f"{v.ran_sentence} {loc_word}={v.loc_out(anchor['location'])}, "
            f"{v.var_out('sugar')}={anchor['sugar']}, {v.var_out('lemon')}={anchor['lemon']}, "
            f"{v.color_key}={v.color_out(anchor['color'])}, {v.var_out('price')}={anchor['price']}, "
            f"which earned about {_p(world, anchor):.0f} {v.unit} per round."
        )
        if hint:
            body += HINT.format(loc_word=loc_word, recipe_word=recipe_word)
        letter_block = f'{v.letter_intro}\n  "{body}"\n\n'
    else:
        letter_block = ""

    sys_msg = SYSTEM.format(
        domain=v.domain, horizon=horizon, config_noun=v.config_noun, fb_noun=v.fb_noun,
        gain_word=v.gain_word,
        locations=", ".join(v.loc_out(l) for l in world.location_names),
        v_loc=loc_word, v_sugar=v.var_out("sugar"), v_lemon=v.var_out("lemon"),
        v_color=v.color_key, v_price=v.var_out("price"),
        c_a=v.color_out("green"), c_b=v.color_out("pink"),
        letter_block=letter_block, condition=cond)

    if not history:
        user = f"Round 1 of {horizon}. No rounds played yet. What is your choice?"
    else:
        lines = history_lines(history, v)
        user = ("History so far:\n" + "\n".join(lines) +
                f"\n\nRound {len(history) + 1} of {horizon}. What is your choice?")
    return [{"role": "system", "content": sys_msg}, {"role": "user", "content": user}]


def parse_action(text, world, fallback, label="semantic"):
    """Extract the JSON action. STRICT (2026-09-13, PREREG v4a): all-or-nothing.

    A turn is valid only if the output contains one JSON object whose location, colour and all three numbers are
    present and legal (location and colour in the vocabulary, each number finite and within 0.0-10.0). Anything else
    is an INVALID turn: nothing from it is applied, the previous action is repeated unchanged, and `ok` is False
    (logged as a parse failure). Before this change a valid location field was applied even when the rest failed, so
    a broken output could register as leaving the anchor, and out-of-range numbers were clamped into range and counted
    as valid (results/format_collapse.md, docs/DECISIONS.md 2026-09-13 04:30).

    Parsing goes through the same vocabulary as rendering, so a model answering in neutral labels ("venue B",
    "setting 1", "variant Y") produces the identical action dict a semantic answer would.
    """
    import math
    v = for_world(label, world)
    loc_key, col_key = v.loc_word, v.color_key
    invalid = (dict(fallback), False)

    m = _JSON.search(text or "")
    if not m:
        return invalid
    try:
        raw = json.loads(m.group(0))
    except Exception:
        return invalid
    if not isinstance(raw, dict):
        return invalid

    real_loc = v.loc_in(str(raw.get(loc_key, raw.get("location", ""))).strip())
    if real_loc not in world.locations:
        return invalid
    real_col = v.color_in(str(raw.get(col_key, raw.get("color", ""))).strip())
    if real_col not in COLORS:
        return invalid
    act = {"location": real_loc, "color": real_col}
    for real in CONTINUOUS:
        try:
            x = float(raw[v.var_out(real)])
        except Exception:
            return invalid
        if not math.isfinite(x) or x < 0.0 or x > 10.0:
            return invalid
        act[real] = round(x, 1)
    return act, True


# --------------------------------------------------------------------------
# Behavioural measurements -- these are the point of the frozen-model run
# --------------------------------------------------------------------------
def feedback_adherence(history):
    """Fraction of informative hints the model then moved the right way.

    This is the operational stand-in for `efficiency` in reward_contrast.py:
    an agent that acts on directional feedback climbs (efficiency -> 1), one
    that ignores it is effectively probing blind (efficiency -> 0).
    Only counted when the model stayed at the same location, since feedback
    is location-specific.
    """
    hits = total = 0
    for prev, nxt in zip(history, history[1:]):
        sig = prev.feedback_signal
        if not sig or sig["direction"] == 0:
            continue
        if nxt.action["location"] != prev.action["location"]:
            continue
        v = sig["var"]
        delta = nxt.action[v] - prev.action[v]
        if abs(delta) < 1e-9:
            continue
        total += 1
        # direction +1 means "too high" -> the model should decrease
        if (delta < 0) == (sig["direction"] > 0):
            hits += 1
    return (hits / total) if total else None, total


def anchoring(history, world, first_n=5):
    """How strongly the model sticks to the previous manager's advice early on."""
    anchor = world.default_action
    head = history[:first_n]
    if not head:
        return {}
    same_loc = sum(h.action["location"] == anchor["location"] for h in head) / len(head)
    same_all = sum(all(h.action[k] == anchor[k]
                       for k in ("location", "color", *CONTINUOUS)) for h in head) / len(head)
    return {"same_location_rate": same_loc, "identical_action_rate": same_all}
