"""Lemonade stand environment from Ederer & Manso (2012), Appendix A.2.

The paper specifies the reward landscape completely, so the base configuration
here is a faithful reimplementation rather than a redesign. Two fidelity
anchors are asserted in tests/test_env.py:

    * the action space has exactly 6,181,806 combinations (paper, sec 2.2)
    * the previous manager's strategy yields 86.5 francs ("about 90", app. A.1)

`World` carries the landscape parameters so that world_generator.py can emit
randomised variants without touching this module.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

Location = str
Color = Literal["green", "pink"]

# Choice grids (paper, appendix A.2)
GRID = tuple(round(0.1 * i, 1) for i in range(101))  # 0.0 .. 10.0 step 0.1
COLORS: tuple[Color, ...] = ("green", "pink")
CONTINUOUS = ("sugar", "lemon", "price")

# The previous manager's letter (appendix A.1)
DEFAULT_ACTION = {
    "location": "business",
    "sugar": 3.0,
    "lemon": 7.0,
    "color": "green",
    "price": 8.2,
}


@dataclass(frozen=True)
class LocationSpec:
    """Optimal product mix and penalty slopes for one location."""

    sugar: float
    lemon: float
    color: Color
    price: float
    max_profit: float
    pen_sugar: float
    pen_lemon: float
    pen_color: float
    pen_price: float

    def optimum(self) -> dict:
        return {"sugar": self.sugar, "lemon": self.lemon,
                "color": self.color, "price": self.price}

    def penalty(self, var: str) -> float:
        return getattr(self, f"pen_{var}")


@dataclass(frozen=True)
class World:
    """A complete reward landscape: one LocationSpec per location."""

    locations: dict[Location, LocationSpec]
    default_action: dict = field(default_factory=lambda: dict(DEFAULT_ACTION))
    name: str = "ederer_manso_2012"

    @property
    def location_names(self) -> list[Location]:
        return list(self.locations)

    def best_location(self) -> Location:
        return max(self.locations, key=lambda k: self.locations[k].max_profit)

    def global_optimum(self) -> tuple[dict, float]:
        loc = self.best_location()
        action = {"location": loc, **self.locations[loc].optimum()}
        return action, self.locations[loc].max_profit


# ---------------------------------------------------------------------------
# Paper-exact landscape (appendix A.2, both tables)
# ---------------------------------------------------------------------------
EDERER_MANSO = World(
    locations={
        "business": LocationSpec(1.5, 7.5, "green", 7.5, 100, 5, 5, 20, 5),
        "school":   LocationSpec(9.5, 1.5, "pink",  2.5, 200, 6, 6, 60, 6),
        "stadium":  LocationSpec(5.5, 5.5, "green", 7.5,  60, 0.5, 0.5, 0.5, 0.5),
    }
)


def profit(world: World, action: dict) -> float:
    """Linear penalty function with a floor at zero (appendix A.2).

    Losses are impossible for the subject, per the paper, so the floor is part
    of the specification rather than a numerical guard.
    """
    spec = world.locations[action["location"]]
    pen = (
        spec.pen_sugar * abs(action["sugar"] - spec.sugar)
        + spec.pen_lemon * abs(action["lemon"] - spec.lemon)
        + spec.pen_price * abs(action["price"] - spec.price)
        + spec.pen_color * (0.0 if action["color"] == spec.color else 1.0)
    )
    return max(0.0, spec.max_profit - pen)


def n_combinations(world: World) -> int:
    return len(world.locations) * len(GRID) ** 3 * len(COLORS)


# ---------------------------------------------------------------------------
# Customer feedback (paper, sec 2.2 and footnote 10)
# ---------------------------------------------------------------------------
_PHRASE = {
    ("sugar", +1): "too sweet",
    ("sugar", -1): "not sweet enough",
    ("lemon", +1): "too sour",
    ("lemon", -1): "not sour enough",
    ("price", +1): "too expensive",
    ("price", -1): "too cheap",
}


def customer_feedback(world: World, action: dict, rng: random.Random) -> tuple[str, dict | None]:
    """One randomly chosen continuous variable yields binary directional feedback.

    Informative only for the location the subject actually sold at, which is
    what makes exploration costly: feedback gathered at one location says
    nothing about another. Colour never receives feedback, so the 60-franc
    colour penalty at the school must be discovered by trying it.
    """
    var = rng.choice(CONTINUOUS)
    spec = world.locations[action["location"]]
    target = getattr(spec, var)
    delta = action[var] - target
    if abs(delta) < 1e-9:
        return (f"Customers at this location seem happy with the {var}.",
                {"var": var, "direction": 0})
    sign = 1 if delta > 0 else -1
    return (f"Many of your customers at this location told you the lemonade is {_PHRASE[(var, sign)]}.",
            {"var": var, "direction": sign})


# ---------------------------------------------------------------------------
# Episode API
# ---------------------------------------------------------------------------
@dataclass
class StepResult:
    round: int
    action: dict
    profit: float
    feedback: str
    feedback_signal: dict | None


class LemonadeEnv:
    """20-period episode. Actions are full product configurations.

    The previous period's action is the default for the next period (paper,
    appendix A.1), so the agent is always anchored on its own last choice.
    """

    def __init__(self, world: World = EDERER_MANSO, horizon: int = 20,
                 seed: int | None = None, feedback_enabled: bool = True):
        self.world = world
        self.horizon = horizon
        self.feedback_enabled = feedback_enabled
        self.rng = random.Random(seed)
        self.reset()

    def reset(self) -> dict:
        self.t = 0
        self.current = dict(self.world.default_action)
        self.history: list[StepResult] = []
        return dict(self.current)

    @property
    def done(self) -> bool:
        return self.t >= self.horizon

    def step(self, action: dict | None = None) -> StepResult:
        if self.done:
            raise RuntimeError("episode already finished")
        act = dict(self.current) if action is None else dict(action)
        self._validate(act)
        p = profit(self.world, act)
        if self.feedback_enabled:
            text, signal = customer_feedback(self.world, act, self.rng)
        else:
            # ablation: profit only, no directional hint about any variable
            text, signal = "Customers bought lemonade.", None
        self.t += 1
        self.current = act
        res = StepResult(self.t, act, p, text, signal)
        self.history.append(res)
        return res

    def _validate(self, act: dict) -> None:
        if act["location"] not in self.world.locations:
            raise ValueError(f"unknown location {act['location']!r}")
        if act["color"] not in COLORS:
            raise ValueError(f"unknown color {act['color']!r}")
        for var in CONTINUOUS:
            v = float(act[var])
            if not (0.0 <= v <= 10.0):
                raise ValueError(f"{var}={v} outside [0, 10]")
            act[var] = round(v, 1)

    # -- reward functions passed to the optimiser (not shown to the agent) --
    def profits(self) -> list[float]:
        return [h.profit for h in self.history]


def reward_immediate(profits: list[float]) -> float:
    """Analogue of the paper's pay-for-performance contract (all 20 periods)."""
    return sum(profits) / len(profits)


def reward_deferred(profits: list[float]) -> float:
    """Analogue of the paper's exploration contract (last 10 periods)."""
    half = len(profits) // 2
    tail = profits[half:]
    return sum(tail) / len(tail)


def reward_terminal(profits: list[float]) -> float:
    return profits[-1]


REWARDS = {
    "immediate": reward_immediate,
    "deferred": reward_deferred,
    "terminal": reward_terminal,
}
