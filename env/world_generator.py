"""Randomised reward landscapes.

Training on a single world teaches the recipe (school + pink + sweet + cheap);
the point of randomising is to force the model to learn an exploration
*procedure* instead. The invariant that must survive randomisation is not
"the optimum moves" -- that alone makes "always try another location" a
sufficient heuristic -- but:

    reaching the global optimum requires coordinated change in >= 3 variables
    away from the anchor, and every single-variable move from the anchor loses.

`check_invariant` enforces exactly that, and `sample_worlds` rejects draws
that fail it.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import random

from .lemonade_env import (COLORS, CONTINUOUS, GRID, EDERER_MANSO, LocationSpec,
                           World, profit)

LOCATION_POOL = ("business", "school", "stadium", "park", "beach", "office_park")


def _snap(x: float) -> float:
    return round(min(10.0, max(0.0, round(x, 1))), 1)


def harden(world: World, scale: float, location: str | None = None) -> World:
    """Steepen the penalty slopes at `location` (default: the best one).

    Widening the gap between the global optimum's ceiling and the width of its
    basin is the knob that stops blind random search from succeeding, without
    changing the qualitative structure the paper describes.
    """
    loc = location or world.best_location()
    specs = dict(world.locations)
    s = specs[loc]
    specs[loc] = LocationSpec(
        s.sugar, s.lemon, s.color, s.price, s.max_profit,
        s.pen_sugar * scale, s.pen_lemon * scale,
        s.pen_color * scale, s.pen_price * scale,
    )
    return World(locations=specs, default_action=dict(world.default_action),
                 name=f"{world.name}_hard{scale:g}")


def check_invariant(world: World, min_coordinated: int = 3) -> tuple[bool, str]:
    """Verify the anchor is a genuine trap and the optimum needs coordination."""
    anchor = dict(world.default_action)
    base = profit(world, anchor)

    # 1. Every single-variable move from the anchor must fail to reach the
    #    global region (otherwise greedy hill-climbing solves the task).
    best_single = base
    for var, vals in (("location", world.location_names), ("color", COLORS),
                      *[(v, GRID) for v in CONTINUOUS]):
        for v in vals:
            a = dict(anchor)
            a[var] = v
            best_single = max(best_single, profit(world, a))

    _, gmax = world.global_optimum()
    if best_single >= 0.9 * gmax:
        return False, f"single-variable move reaches {best_single:.1f} of {gmax:.1f}"

    # 2. Moving only the location must strictly hurt -- this is the valley.
    gloc = world.best_location()
    moved = dict(anchor)
    moved["location"] = gloc
    if profit(world, moved) >= base:
        return False, (f"moving to {gloc} alone does not hurt "
                       f"({profit(world, moved):.1f} >= {base:.1f})")

    # 3. The optimum must differ from the anchor in >= min_coordinated vars.
    gopt, _ = world.global_optimum()
    diff = sum(1 for k in ("location", "color", *CONTINUOUS)
               if gopt[k] != anchor[k])
    if diff < min_coordinated:
        return False, f"optimum differs in only {diff} variables"

    # 4. The anchor must be a decent local optimum, not obviously bad.
    if base < 0.3 * gmax:
        return False, f"anchor too weak ({base:.1f} vs {gmax:.1f})"

    # 5. Greedy must stay trapped even after perfecting the recipe where it
    #    starts. Checking only the anchor action is not enough: if the anchor
    #    location's own peak happens to sit near another location's optimum,
    #    coordinate ascent can hop out one variable at a time.
    anchor_loc = anchor["location"]
    peak = {"location": anchor_loc, **world.locations[anchor_loc].optimum()}
    peak_p = profit(world, peak)
    for other in world.location_names:
        if other == anchor_loc:
            continue
        if profit(world, dict(peak, location=other)) >= peak_p:
            return False, f"greedy escapes from the {anchor_loc} peak to {other}"

    return True, "ok"


def sample_world(rng: random.Random, n_locations: int = 3,
                 harden_scale: float = 1.0, max_tries: int = 200) -> World:
    """Draw a random landscape satisfying the invariant."""
    for _ in range(max_tries):
        names = rng.sample(LOCATION_POOL, n_locations)
        anchor_loc, global_loc = names[0], names[1]

        specs: dict[str, LocationSpec] = {}
        maxima = {anchor_loc: rng.uniform(90, 110), global_loc: rng.uniform(180, 220)}
        for n in names[2:]:
            maxima[n] = rng.uniform(50, 75)

        for n in names:
            is_global = n == global_loc
            slope = rng.uniform(5, 7) if n in (anchor_loc, global_loc) else rng.uniform(0.4, 1.0)
            if is_global:
                slope *= harden_scale
            col_pen = (rng.uniform(50, 70) if is_global else
                       rng.uniform(15, 25) if n == anchor_loc else rng.uniform(0.4, 1.0))
            if is_global:
                col_pen *= harden_scale
            specs[n] = LocationSpec(
                sugar=_snap(rng.uniform(0, 10)), lemon=_snap(rng.uniform(0, 10)),
                color=rng.choice(COLORS), price=_snap(rng.uniform(0, 10)),
                max_profit=round(maxima[n], 1),
                pen_sugar=slope, pen_lemon=slope, pen_color=col_pen, pen_price=slope,
            )

        # Anchor sits near -- but not on -- the anchor location's optimum, the
        # way the previous manager's letter describes a good-but-imperfect mix.
        a = specs[anchor_loc]
        anchor = {
            "location": anchor_loc,
            "sugar": _snap(a.sugar + rng.uniform(-2, 2)),
            "lemon": _snap(a.lemon + rng.uniform(-2, 2)),
            "color": a.color,
            "price": _snap(a.price + rng.uniform(-1.5, 1.5)),
        }
        world = World(locations=specs, default_action=anchor,
                      name=f"w{rng.randrange(10**9):09d}")
        ok, _ = check_invariant(world)
        if ok:
            return world
    raise RuntimeError("could not sample a world satisfying the invariant")


def sample_worlds(n: int, seed: int, **kw) -> list[World]:
    rng = random.Random(seed)
    return [sample_world(rng, **kw) for _ in range(n)]


# ---------------------------------------------------------------------------
# World identity, persistence and splits
# ---------------------------------------------------------------------------
def world_to_dict(world: World) -> dict:
    """Canonical, order-stable serialisation of a world's *content*.

    `name` is excluded on purpose: it carries a random suffix, so including it
    would make every draw trivially unique and defeat the disjointness check
    that `make_splits` relies on. Two worlds with the same landscape are the
    same world however they were drawn.
    """
    return {
        "default_action": {k: world.default_action[k] for k in sorted(world.default_action)},
        "locations": {
            n: {
                "sugar": s.sugar, "lemon": s.lemon, "color": s.color,
                "price": s.price, "max_profit": s.max_profit,
                "pen_sugar": s.pen_sugar, "pen_lemon": s.pen_lemon,
                "pen_color": s.pen_color, "pen_price": s.pen_price,
            }
            for n, s in sorted(world.locations.items())
        },
    }


def world_from_dict(d: dict, name: str = "loaded") -> World:
    return World(
        locations={n: LocationSpec(**spec) for n, spec in d["locations"].items()},
        default_action=dict(d["default_action"]),
        name=name,
    )


def world_id(world: World) -> str:
    """Stable 16-hex-char content hash. This is the `world_id` logged with every
    rollout, and the key that makes train/val/test disjointness auditable after
    the fact rather than merely asserted (AUDIT §3.4)."""
    blob = json.dumps(world_to_dict(world), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def make_splits(n_train: int = 200, n_val: int = 50, n_test: int = 50,
                seed: int = 0, **kw) -> dict[str, list[World]]:
    """Train/val/test worlds, disjoint **by construction**.

    The old `splits()` drew each partition from its own seed and trusted the RNG
    streams not to collide. Phase 0 checked and they happened not to -- but that
    was luck, not a guarantee, and brief §3 rule 3 needs a guarantee. Here a
    single stream fills train, then val, then test, and any draw whose content
    hash has already been used is discarded and redrawn.
    """
    rng = random.Random(seed)
    seen: set[str] = set()
    out: dict[str, list[World]] = {}
    for part, n in (("train", n_train), ("val", n_val), ("test", n_test)):
        got: list[World] = []
        guard = 0
        while len(got) < n:
            guard += 1
            if guard > 100 * max(n, 1) + 1000:
                raise RuntimeError(f"could not draw {n} distinct worlds for {part}")
            w = sample_world(rng, **kw)
            wid = world_id(w)
            if wid in seen:
                continue
            seen.add(wid)
            got.append(w)
        out[part] = got
    return out


def splits(n_train: int = 200, n_val: int = 50, n_test: int = 50,
           seed: int = 0, **kw) -> dict[str, list[World]]:
    """Deprecated alias for `make_splits`. Kept so nothing silently breaks; the
    old three-independent-seeds behaviour is gone."""
    return make_splits(n_train, n_val, n_test, seed, **kw)


def save_world_set(worlds: dict[str, list[World]], path, meta: dict | None = None) -> dict:
    """Write a split to disk with its invariant receipts.

    The receipt matters: a reviewer asking "were the reported worlds really
    traps?" gets an answer from the file, without re-running the generator and
    hoping the RNG still behaves the same way three library versions later.
    """
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"meta": dict(meta or {}), "splits": {}}
    for part, ws in worlds.items():
        rows = []
        for w in ws:
            ok, why = check_invariant(w)
            gopt, gmax = w.global_optimum()
            rows.append({
                "world_id": world_id(w),
                "name": w.name,
                "world": world_to_dict(w),
                "invariant_ok": ok,
                "invariant_detail": why,
                "anchor_profit": profit(w, w.default_action),
                "global_optimum_action": gopt,
                "global_optimum_profit": gmax,
                "best_location": w.best_location(),
            })
        payload["splits"][part] = rows
    ids = {p: {r["world_id"] for r in rs} for p, rs in payload["splits"].items()}
    payload["meta"]["counts"] = {p: len(rs) for p, rs in payload["splits"].items()}
    payload["meta"]["all_invariants_ok"] = all(
        r["invariant_ok"] for rs in payload["splits"].values() for r in rs)
    payload["meta"]["pairwise_overlap"] = {
        f"{a}|{b}": len(ids[a] & ids[b])
        for i, a in enumerate(ids) for b in list(ids)[i + 1:]
    }
    path.write_text(json.dumps(payload, indent=2))
    return payload["meta"]


def load_world_set(path) -> dict[str, list[World]]:
    payload = json.loads(pathlib.Path(path).read_text())
    return {
        part: [world_from_dict(r["world"], name=r["name"]) for r in rows]
        for part, rows in payload["splits"].items()
    }
