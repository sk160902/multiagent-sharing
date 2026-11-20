"""Label conditions: the same environment, described three different ways.

Brief §10.4 / H4. On the paper-exact world a naive semantic guess ("sell at a
school, very sweet, barely sour, pink, cheap") scores 191 of 200 with zero
exploration, so a high score under lemonade labels is not by itself evidence of
search. Three vocabularies separate prior knowledge from learned strategy:

  semantic    the lemonade labels the pilot used -- priors point the right way
  neutral     abstract dials and sites -- no useful priors either way
  misleading  lemonade labels permuted so priors point the WRONG way

**The environment is untouched.** Only rendering and parsing change, and every
behavioural measure reads the action dicts, not the text, so metrics remain
directly comparable across conditions. `tests/test_vocab.py` pins that the
semantic vocabulary reproduces the pilot's prompt byte for byte.

Feedback is re-rendered from the structured `feedback_signal` rather than from
the environment's own English, which is what lets the phrasing change without
touching `lemonade_env`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from env.lemonade_env import COLORS, CONTINUOUS

NEUTRAL_V1_SITE_NAMES = ("site A", "site B", "site C", "site D", "site E", "site F")
NEUTRAL_VENUE_NAMES = ("venue A", "venue B", "venue C", "venue D", "venue E", "venue F")
# The alien vocabulary names the five decision variables A-E, in the order the prompt lists
# them, so A is the categorical "location", B, C and E are the three numbers and D is the
# two-valued one. Values of A and D are numbered inside their own letter.
ALIEN_A_NAMES = ("A1", "A2", "A3", "A4", "A5", "A6")


@dataclass(frozen=True)
class Vocabulary:
    name: str
    domain: str                     # "lemonade stand"
    unit: str                       # "francs"
    feedback_source: str            # "customer"
    var_display: dict               # sugar -> "sugar"
    color_display: dict             # green -> "green"
    # direction phrases, keyed by (displayed var, +1 = value is too high)
    phrase_high: dict
    phrase_low: dict
    happy: str
    location_display: dict = field(default_factory=dict)
    # Every word the prompt templates use that depends on the vocabulary. Defaults are the
    # lemonade wording, so the semantic rendering is byte-identical to the pilot's.
    loc_word: str = "location"            # JSON key and prose for a location
    color_key: str = "color"              # JSON key for the categorical variable
    recipe_word: str = "recipe"
    org_word: str = "business"            # "business" is also a location name, hence a word
    domain_word: str = "stand"
    letter_intro: str = "A letter from the previous manager:"
    ran_sentence: str = "I ran this stand for years. My best setup was"
    config_noun: str = "product configuration"
    fb_noun: str = "customer comment"
    gain_word: str = "profit"
    no_signal_text: str = ""              # feedback when a round has no signal
    location_names: tuple = ()            # display names for abstract vocabularies, in world order

    # -- helpers ---------------------------------------------------------
    def loc_out(self, loc: str) -> str:
        return self.location_display.get(loc, loc)

    def loc_in(self, shown: str) -> str | None:
        for real, disp in self.location_display.items():
            if disp.lower().replace(" ", "_") == shown.lower().replace(" ", "_"):
                return real
        return None

    def var_out(self, var: str) -> str:
        return self.var_display[var]

    def var_in(self, shown: str) -> str | None:
        for real, disp in self.var_display.items():
            if disp.lower() == str(shown).lower():
                return real
        return None

    def color_out(self, c: str) -> str:
        return self.color_display[c]

    def color_in(self, shown: str) -> str | None:
        for real, disp in self.color_display.items():
            if disp.lower() == str(shown).lower():
                return real
        return None

    def feedback_text(self, signal: dict | None) -> str:
        """Re-render one round's feedback in this vocabulary."""
        if signal is None:
            return self.no_signal_text or f"{self.feedback_source.capitalize()}s bought lemonade."
        var = signal["var"]
        d = signal.get("direction", 0)
        if d == 0:
            return self.happy.format(var=self.var_out(var))
        tbl = self.phrase_high if d > 0 else self.phrase_low
        return tbl[var].format(var=self.var_out(var))


def _semantic() -> Vocabulary:
    """Reproduces the pilot's wording exactly (pinned by tests)."""
    return Vocabulary(
        name="semantic", domain="lemonade stand", unit="francs",
        feedback_source="customer",
        var_display={"sugar": "sugar", "lemon": "lemon", "price": "price"},
        color_display={"green": "green", "pink": "pink"},
        phrase_high={
            "sugar": "Many of your customers at this location told you the lemonade is too sweet.",
            "lemon": "Many of your customers at this location told you the lemonade is too sour.",
            "price": "Many of your customers at this location told you the lemonade is too expensive.",
        },
        phrase_low={
            "sugar": "Many of your customers at this location told you the lemonade is not sweet enough.",
            "lemon": "Many of your customers at this location told you the lemonade is not sour enough.",
            "price": "Many of your customers at this location told you the lemonade is too cheap.",
        },
        happy="Customers at this location seem happy with the {var}.",
    )


def _neutral() -> Vocabulary:
    """An abstract scoring exercise: venues, numbered settings, a variant, points.

    Adopted 2026-09-12 (docs/DECISIONS.md), replacing `neutral_v1`. The v1 wording -- a
    "production process" run by an "operator" choosing a "site", "dials" and a "mode" from
    "sensor readings" -- reads like industrial-control-system operation, and claude-opus-5's
    safety filter refused it (stop_reason "refusal", category cyber). These words were chosen
    to carry no domain at all: no industry, no equipment, no security connotation, no lemonade.
    """
    return Vocabulary(
        name="neutral", domain="scoring exercise", unit="points",
        feedback_source="feedback",
        var_display={"sugar": "setting 1", "lemon": "setting 2", "price": "setting 3"},
        color_display={"green": "variant X", "pink": "variant Y"},
        phrase_high={v: "Feedback at this venue: {var} is higher than ideal." for v in CONTINUOUS},
        phrase_low={v: "Feedback at this venue: {var} is lower than ideal." for v in CONTINUOUS},
        happy="Feedback at this venue: {var} is about right.",
        loc_word="venue", color_key="variant", recipe_word="configuration",
        org_word="exercise", domain_word="exercise",
        letter_intro="A note from the previous player:",
        ran_sentence="I played this exercise for many rounds. My best choice was",
        config_noun="configuration", fb_noun="feedback line", gain_word="points",
        no_signal_text="The round completed.", location_names=NEUTRAL_VENUE_NAMES,
    )


def _neutral_v1() -> Vocabulary:
    """RETIRED 2026-09-12. Kept only so records produced with it can be re-rendered exactly.
    Not in LABEL_CONDITIONS; nothing new runs with it. See `_neutral`."""
    return Vocabulary(
        name="neutral_v1", domain="production process", unit="units",
        feedback_source="sensor",
        var_display={"sugar": "dial 1", "lemon": "dial 2", "price": "dial 3"},
        color_display={"green": "mode X", "pink": "mode Y"},
        phrase_high={v: "Readings at this site indicate {var} is above its target."
                     for v in CONTINUOUS},
        phrase_low={v: "Readings at this site indicate {var} is below its target."
                    for v in CONTINUOUS},
        happy="Readings at this site indicate {var} is at its target.",
        loc_word="site", color_key="mode", recipe_word="setting", org_word="operation",
        domain_word="process", letter_intro="A note from the previous operator:",
        ran_sentence="I ran this process for years. My best setup was",
        config_noun="process configuration", fb_noun="sensor reading",
        no_signal_text="The run completed.", location_names=NEUTRAL_V1_SITE_NAMES,
    )


def _alien() -> Vocabulary:
    """Five decision variables called A to E, and nothing else.

    Asked for by the advisor on 12 Oct, following the setup of Billinger et al.: "you have
    been given 5 decision variables, A, B, C, D, E, for a business, and every combination is
    associated with a payoff; your job is to find the best combination". The instruction was
    to keep the world and its numbers exactly as they are and change only the labels, because
    labels are what a language model has priors about.

    This goes further than `neutral`, which still describes a scoring exercise held at venues
    with numbered settings and so still carries the shape of a place-and-recipe problem. Here
    there is no place and no recipe: A happens to be the variable with three values, and
    nothing in the wording says it is where the business is. `neutral` remains the paper's
    label condition for H4; this one exists for the multi-agent rerun.

    Normally paired with `letter=False`, since the advisor also asked for no recommended
    setup in the alien version.
    """
    return Vocabulary(
        name="alien", domain="business with five decision variables", unit="payoff",
        feedback_source="feedback",
        var_display={"sugar": "B", "lemon": "C", "price": "E"},
        color_display={"green": "D1", "pink": "D2"},
        phrase_high={v: "Feedback: at this value of A, {var} is higher than ideal."
                     for v in CONTINUOUS},
        phrase_low={v: "Feedback: at this value of A, {var} is lower than ideal."
                    for v in CONTINUOUS},
        happy="Feedback: at this value of A, {var} is about right.",
        loc_word="A", color_key="D", recipe_word="combination",
        org_word="business", domain_word="business",
        letter_intro="A note from whoever held this role before:",
        ran_sentence="I made this choice for many rounds. My best combination was",
        config_noun="combination", fb_noun="feedback line", gain_word="payoff",
        no_signal_text="The round completed.", location_names=ALIEN_A_NAMES,
    )


def _misleading() -> Vocabulary:
    """Lemonade labels permuted so the model's priors point the wrong way.

    `sugar` is displayed as "lemon" and vice versa, and the colours are swapped.
    A model that reasons from lemonade knowledge ("school, very sweet, pink")
    now steers itself away from the optimum; one that reads the feedback and
    searches is unaffected. The phrases follow the *displayed* label, so the
    text remains internally consistent -- it is the priors that mislead, not
    contradictory evidence.
    """
    sem = _semantic()
    return Vocabulary(
        name="misleading", domain="lemonade stand", unit="francs",
        feedback_source="customer",
        var_display={"sugar": "lemon", "lemon": "sugar", "price": "price"},
        color_display={"green": "pink", "pink": "green"},
        # keyed by the REAL variable, phrased with its DISPLAYED name
        phrase_high={
            "sugar": "Many of your customers at this location told you the lemonade is too sour.",
            "lemon": "Many of your customers at this location told you the lemonade is too sweet.",
            "price": "Many of your customers at this location told you the lemonade is too expensive.",
        },
        phrase_low={
            "sugar": "Many of your customers at this location told you the lemonade is not sour enough.",
            "lemon": "Many of your customers at this location told you the lemonade is not sweet enough.",
            "price": "Many of your customers at this location told you the lemonade is too cheap.",
        },
        happy=sem.happy,
    )


_BUILDERS = {"semantic": _semantic, "neutral": _neutral, "misleading": _misleading,
             "alien": _alien, "neutral_v1": _neutral_v1}
LABEL_CONDITIONS = ("semantic", "neutral", "misleading", "alien")   # neutral_v1 is retired


def for_world(name: str, world) -> Vocabulary:
    """A vocabulary bound to one world's location names.

    Abstract vocabularies relabel locations ("venue A/B/...") in the world's own order, so no
    information about which location is good leaks through the naming. Misleading
    keeps the lemonade location names but rotates them, so a model that believes
    "schools are good" is pointed at the wrong site.
    """
    v = _BUILDERS[name]()
    locs = list(world.location_names)
    if v.location_names:
        mapping = {l: v.location_names[i] for i, l in enumerate(locs)}
    elif name == "misleading":
        mapping = {l: locs[(i + 1) % len(locs)] for i, l in enumerate(locs)}
    else:
        mapping = {l: l for l in locs}
    return Vocabulary(**{**v.__dict__, "location_display": mapping})
