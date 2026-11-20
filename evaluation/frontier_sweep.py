"""Frozen closed-weight frontier models on the lemonade task. H3 for frontier models.

User program 2026-09-12 (item 0b). Grid, per model:
    prompt {neutral, explore_directed} x label {semantic, neutral, misleading} x hint {on, off}
Horizon 20, T 0.7 / top_p 0.9 where the API accepts them, 64 episodes per cell, TEST worlds.
Reported per cell: leave rate, escape (PREREG v2), % of optimum, directive compliance,
parse failure.

Safety and cost rules this file enforces:
  * API keys are read from `working_apis/` inside this process only. They are never
    printed, logged, written to a cache record, or placed in a config snapshot. (Reading
    them in-process is the stricter form of "load into the environment at launch": it
    keeps them out of Slurm's recorded job environment too.)
  * Every episode is cached as one JSONL line keyed by (model, prompt, label, hint,
    world_id, repeat). A restarted sweep skips completed keys, so a preemption or
    walltime kill never pays for the same episode twice.
  * Spend is metered from the usage each API reports, priced at list rates, and the
    sweep refuses to start an episode once the cap would be exceeded.
  * Sampling parameters an API rejects are dropped for that model and the parameters
    ACTUALLY used are recorded in every record -- nothing is silently different.

    python evaluation/frontier_sweep.py estimate            # measured-token pilot -> spend estimate
    python evaluation/frontier_sweep.py run --cap 250       # the sweep
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import pathlib
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from agents.llm_agent import build_messages, parse_action
from analysis import metrics as M
from env.lemonade_env import LemonadeEnv
from env.lemonade_env import EDERER_MANSO
from env.world_generator import load_world_set, world_id

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "frontier"
KEYDIR = ROOT / "working_apis"

# Chosen 2026-09-08 from each provider's live model list and pricing docs (DECISIONS.md).
# `params` are the sampling parameters each API was VERIFIED to accept on 2026-09-12. The
# user asked for T 0.7 / top_p 0.9 "where the API allows":
#   gpt-5.6-sol    rejects temperature != 1 and rejects top_p      -> provider default
#   claude-opus-5  "temperature is deprecated", "top_p is deprecated" -> provider default
#   gemini-3.1-pro accepts both                                     -> T 0.7, top_p 0.9
# Every episode record carries the params actually sent.
MODELS = {
    "gpt-5.6-sol": {"provider": "openai", "key": "api_key.txt", "in": 4.00, "out": 20.00,
                    "cached_in": 0.40, "params": {}},
    "claude-opus-5": {"provider": "anthropic", "key": "api_key_anthropic_ucb.txt", "in": 5.00,
                      "out": 25.00, "cached_in": 0.50, "params": {}},
    # Added 2026-11-17: claude-opus-5 refuses the alien prompt and the shared board (category "cyber",
    # DECISIONS 2026-09-12 and PILOT_MULTIAGENT addendum 2026-11-17), so other Anthropic models are
    # candidates for the second-model replication. Prices from the Anthropic price list on 2026-11-17.
    "claude-opus-5-5": {"provider": "anthropic", "key": "api_key_anthropic_ucb.txt", "in": 4.00,
                        "out": 20.00, "cached_in": 0.40, "params": {}},
    "claude-sonnet-5-5": {"provider": "anthropic", "key": "api_key_anthropic_ucb.txt", "in": 2.00,
                          "out": 10.00, "cached_in": 0.20, "params": {}},
    "claude-sonnet-5": {"provider": "anthropic", "key": "api_key_anthropic_ucb.txt", "in": 2.00,
                        "out": 10.00, "cached_in": 0.20, "params": {}},
    "claude-opus-4-8": {"provider": "anthropic", "key": "api_key_anthropic_ucb.txt", "in": 5.00,
                        "out": 25.00, "cached_in": 0.50, "params": {}},
    # api_key_gemini.txt returned HTTP 429 "exceeded your current quota ... billing" on
    # 2026-09-12; the other three Gemini keys work.
    "gemini-3.1-pro-preview": {"provider": "google", "key": "api_key_gemini_2.txt", "in": 2.00,
                               "out": 12.00, "cached_in": 0.20,
                               # top_p 0.9 for EVERY Gemini cell, so its label and world conditions differ
                               # only in the condition (DECISIONS 2026-09-13). The local model samples at
                               # 0.95; cross-model comparisons already differ in sampling (GPT and Claude
                               # run at provider default). Each episode records what it was sent.
                               "params": {"temperature": 0.7, "top_p": 0.9}},
    # Added 2026-10-21 so the multi-agent pilot can be iterated in minutes instead of half
    # an hour (advisor, 12 Oct: switch to a light, low-latency model, scale up later). Same
    # generation as the Pro entry above, so a speed or quality comparison between them is
    # not also a comparison of model generations. Prices are the paid-tier standard rates
    # from ai.google.dev/gemini-api/docs/pricing read on 2026-10-21, where the Pro rates on
    # that page match the Pro entry above. gemini-2.5-flash-lite is cheaper still
    # (0.10 / 0.40 / 0.01) if cost rather than latency becomes the binding constraint.
    "gemini-3.1-flash-lite": {"provider": "google", "key": "api_key_gemini_2.txt", "in": 0.25,
                              "out": 1.50, "cached_in": 0.025,
                              "params": {"temperature": 0.7, "top_p": 0.9}},
}
PROMPTS = ("neutral", "explore_directed")
LABELS = ("semantic", "neutral", "misleading")
HINTS = (True, False)
HORIZON = 20
TEMP, TOP_P = 0.7, 0.9
MAX_OUT = 4096          # room for a reasoning model's hidden tokens plus the JSON answer

_SECRET = re.compile(r"(sk-[A-Za-z0-9_\-]{8,}|AIza[A-Za-z0-9_\-]{10,})")


def scrub(s) -> str:
    return _SECRET.sub("<redacted>", str(s))[:500]


# ---------------------------------------------------------------------------
# Provider clients -- stdlib only, keys never leave this module's memory
# ---------------------------------------------------------------------------
class Client:
    def __init__(self, model: str):
        self.model = model
        self.spec = MODELS[model]
        self.provider = self.spec["provider"]
        self._key = (KEYDIR / self.spec["key"]).read_text().strip()
        # verified-accepted sampling params; still pruned if an API later rejects one
        self.params = dict(self.spec["params"])
        self._lock = threading.Lock()

    def _post(self, url, body, headers, timeout=300):
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"content-type": "application/json", **headers})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())

    def _call_once(self, system, user, params):
        if self.provider == "openai":
            body = {"model": self.model, "max_completion_tokens": MAX_OUT,
                    "messages": [{"role": "system", "content": system},
                                 {"role": "user", "content": user}], **params}
            d = self._post("https://api.openai.com/v1/chat/completions", body,
                           {"Authorization": f"Bearer {self._key}"})
            u = d.get("usage", {})
            msg = d["choices"][0]["message"]
            return (msg.get("content") or "",
                    {"refusals": int(bool(msg.get("refusal"))
                                     or d["choices"][0].get("finish_reason") == "content_filter"),
                     "input": u.get("prompt_tokens", 0),
                     "output": u.get("completion_tokens", 0),
                     "reasoning": (u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0),
                     "cached_input": (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0)})
        if self.provider == "anthropic":
            body = {"model": self.model, "max_tokens": MAX_OUT, "system": system,
                    "messages": [{"role": "user", "content": user}], **params}
            d = self._post("https://api.anthropic.com/v1/messages", body,
                           {"x-api-key": self._key, "anthropic-version": "2023-06-01"})
            u = d.get("usage", {})
            text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
            # A provider safety block returns no text. Counted separately so it is never
            # mistaken for a formatting failure by the model.
            return (text, {"input": u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                                    + u.get("cache_creation_input_tokens", 0),
                           "output": u.get("output_tokens", 0), "reasoning": 0,
                           "cached_input": u.get("cache_read_input_tokens", 0),
                           "refusals": int(d.get("stop_reason") == "refusal")})
        gp = {"maxOutputTokens": MAX_OUT}
        if "temperature" in params:
            gp["temperature"] = params["temperature"]
        if "top_p" in params:
            gp["topP"] = params["top_p"]
        body = {"systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": gp}
        d = self._post(f"https://generativelanguage.googleapis.com/v1beta/models/"
                       f"{self.model}:generateContent?key={self._key}", body, {})
        u = d.get("usageMetadata", {})
        cands = d.get("candidates") or [{}]
        parts = (cands[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        blocked = (cands[0].get("finishReason") in {"SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII"}
                   or bool((d.get("promptFeedback") or {}).get("blockReason")))
        return (text, {"refusals": int(blocked), "input": u.get("promptTokenCount", 0),
                       "output": u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0),
                       "reasoning": u.get("thoughtsTokenCount", 0),
                       "cached_input": u.get("cachedContentTokenCount", 0)})

    def generate(self, messages, max_retries=8):
        system = next(m["content"] for m in messages if m["role"] == "system")
        user = next(m["content"] for m in messages if m["role"] == "user")
        delay = 5.0
        for attempt in range(max_retries):
            with self._lock:
                params = dict(self.params)
            try:
                text, usage = self._call_once(system, user, params)
                return text, usage, params
            except urllib.error.HTTPError as e:
                msg = ""
                try:
                    msg = e.read().decode()
                except Exception:
                    pass
                low = msg.lower()
                if e.code == 400 and params and any(p in low for p in ("temperature", "top_p", "topp", "top-p", "sampling")):
                    # drop the rejected parameter(s) for this model, permanently, and record it
                    with self._lock:
                        if "top_p" in low or "topp" in low or "top-p" in low or ("both" in low and "top_p" in self.params):
                            self.params.pop("top_p", None)
                        elif "temperature" in low:
                            self.params.pop("temperature", None)
                        else:
                            self.params.clear()
                    continue
                if e.code == 429 and any(w in low for w in ("quota", "billing", "insufficient")):
                    # Out of credit is not a rate limit. Backing off would stall the sweep
                    # for hours on a call that can never succeed -- which is exactly what
                    # hung the first smoke test.
                    raise RuntimeError(f"{self.model}: account quota/billing exhausted: "
                                       f"{scrub(msg)[:200]}") from None
                if e.code in (408, 409, 429, 500, 502, 503, 504, 529):
                    time.sleep(delay * (1 + random.random()))
                    delay = min(delay * 2, 120)
                    continue
                raise RuntimeError(f"{self.model} HTTP {e.code}: {scrub(msg)}") from None
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                time.sleep(delay * (1 + random.random()))
                delay = min(delay * 2, 120)
        raise RuntimeError(f"{self.model}: gave up after {max_retries} attempts")


def cost(model, usage) -> float:
    s = MODELS[model]
    cached = usage.get("cached_input", 0)
    fresh = max(0, usage.get("input", 0) - cached)
    return (fresh * s["in"] + cached * s["cached_in"] + usage.get("output", 0) * s["out"]) / 1e6


# ---------------------------------------------------------------------------
# Episodes, cache and spend
# ---------------------------------------------------------------------------
def cell_key(model, prompt, label, hint):
    return f"{model}__{prompt}__{label}__hint{'on' if hint else 'off'}"


def episode_key(model, prompt, label, hint, wid, rep):
    return f"{cell_key(model, prompt, label, hint)}__{wid}__r{rep}"


class Spend:
    def __init__(self, path, cap):
        self.path, self.cap = path, cap
        self.lock = threading.Lock()
        self.total = 0.0
        self.by_cell = {}
        if path.exists():
            d = json.loads(path.read_text())
            self.total, self.by_cell = d.get("total", 0.0), d.get("by_cell", {})

    def add(self, cell, dollars):
        with self.lock:
            self.total += dollars
            self.by_cell[cell] = self.by_cell.get(cell, 0.0) + dollars
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"total": self.total, "by_cell": self.by_cell,
                                       "cap": self.cap}, indent=1))
            tmp.replace(self.path)

    def room(self, need):
        with self.lock:
            return self.cap is None or self.total + need <= self.cap


def load_cache(path) -> dict:
    done = {}
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                r = json.loads(line)
                done[r["key"]] = r
            except Exception:
                continue
    return done


def run_episode(client, prompt, label, hint, world, wid, rep, seed):
    env = LemonadeEnv(world=world, horizon=HORIZON, seed=seed)
    env.reset()
    raw, oks, usage_tot, calls = [], [], {"input": 0, "output": 0, "reasoning": 0, "cached_input": 0,
                                   "refusals": 0}, 0
    params_used = None
    dollars = 0.0
    for _ in range(HORIZON):
        msgs = build_messages(world, prompt, env.history, HORIZON, label=label, hint=hint)
        text, usage, params_used = client.generate(msgs)
        calls += 1
        for k in usage_tot:
            usage_tot[k] += usage.get(k, 0)
        dollars += cost(client.model, usage)
        fallback = env.history[-1].action if env.history else world.default_action
        act, ok = parse_action(text, world, fallback, label=label)
        raw.append(text[-600:])
        oks.append(bool(ok))
        env.step(act)
    ep = M.from_env(env, parse_ok=oks)
    return {"key": episode_key(client.model, prompt, label, hint, wid, rep),
            "model": client.model, "prompt": prompt, "label": label, "hint": hint,
            "world_id": wid, "repeat": rep, "horizon": HORIZON,
            "params_used": params_used, "usage": usage_tot, "calls": calls,
            "dollars": dollars, "raw_outputs": raw, "parse_ok": oks,
            "actions": [dict(h.action) for h in env.history],
            "profits": [round(h.profit, 4) for h in env.history],
            "metrics": M.episode_metrics(ep)}


def plan(worlds, episodes):
    """The (world, repeat) schedule for one cell: cycle the test worlds."""
    return [(worlds[i % len(worlds)], i // len(worlds)) for i in range(episodes)]


def run_cell(client, prompt, label, hint, worlds, episodes, cache_path, spend, workers,
             est_per_episode):
    cell = cache_path.stem.removeprefix("cell__")      # includes a __published suffix
    done = load_cache(cache_path)
    todo = []
    for i, (w, rep) in enumerate(plan(worlds, episodes)):
        wid = world_id(w)
        if episode_key(client.model, prompt, label, hint, wid, rep) not in done:
            todo.append((w, wid, rep, 7_000_000 + 1000 * i))
    if not todo:
        return "complete (cached)"
    lock = threading.Lock()
    stopped = False
    with open(cache_path, "a", buffering=1) as f, cf.ThreadPoolExecutor(workers) as pool:
        futs = {}
        for w, wid, rep, seed in todo:
            if not spend.room(est_per_episode):
                stopped = True
                break
            futs[pool.submit(run_episode, client, prompt, label, hint, w, wid, rep, seed)] = wid
        for fut in cf.as_completed(futs):
            try:
                rec = fut.result()
            except Exception as e:                           # noqa: BLE001
                print(f"  [{cell}] episode failed: {scrub(e)}", flush=True)
                continue
            with lock:
                f.write(json.dumps(rec) + "\n")
            spend.add(cell, rec["dollars"])
    return "stopped at cap" if stopped else "complete"


# ---------------------------------------------------------------------------
def cells(drop_hint_off=False, drop_misleading=False):
    for m in MODELS:
        for p in PROMPTS:
            for lab in LABELS:
                if drop_misleading and lab == "misleading":
                    continue
                for h in HINTS:
                    if drop_hint_off and not h:
                        continue
                    yield m, p, lab, h


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["estimate", "run"])
    ap.add_argument("--episodes", type=int, default=64)
    ap.add_argument("--pilot-episodes", type=int, default=2)
    ap.add_argument("--cap", type=float, default=250.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--drop-hint-off", action="store_true")
    ap.add_argument("--drop-misleading", action="store_true")
    ap.add_argument("--cells", default="",
                    help="explicit comma list of prompt:label cells (hint on), replacing the grid")
    ap.add_argument("--split", default="test", choices=["test", "published"],
                    help="published = the paper-exact Ederer-Manso world, for the human comparison")
    ap.add_argument("--skip-cells", default="",
                    help="comma-separated cell keys not to run (e.g. a cell a provider's "
                         "safety filter blocks, so further episodes would buy refusals)")
    ap.add_argument("--spend-file", default="spend.json",
                    help="per-process spend ledger under results/frontier/, so parallel "
                         "per-model processes each enforce their own hard sub-cap")
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    test = load_world_set(ROOT / "data" / "worlds_main.json")["test"]
    models = [m for m in a.models.split(",") if m]

    if a.mode == "estimate":
        # A measured-token pilot on the costliest-looking cell per model: the longest
        # prompt (explore_directed, semantic, hint on). Real usage, real reasoning tokens.
        est = {}
        spend = Spend(OUT / "pilot_spend.json", cap=None)
        for m in models:
            cl = Client(m)
            cache = OUT / f"pilot__{cell_key(m, 'explore_directed', 'semantic', True)}.jsonl"
            run_cell(cl, "explore_directed", "semantic", True, test, a.pilot_episodes, cache,
                     spend, workers=a.pilot_episodes, est_per_episode=0.0)
            recs = list(load_cache(cache).values())
            if not recs:
                est[m] = {"error": "pilot produced no episodes"}
                continue
            n = len(recs)
            est[m] = {"pilot_episodes": n,
                      "input_per_episode": sum(r["usage"]["input"] for r in recs) / n,
                      "output_per_episode": sum(r["usage"]["output"] for r in recs) / n,
                      "reasoning_per_episode": sum(r["usage"]["reasoning"] for r in recs) / n,
                      "cached_input_per_episode": sum(r["usage"]["cached_input"] for r in recs) / n,
                      "dollars_per_episode": sum(r["dollars"] for r in recs) / n,
                      "params_used": recs[-1]["params_used"],
                      "parse_failure": 1 - sum(sum(r["parse_ok"]) for r in recs) / sum(len(r["parse_ok"]) for r in recs),
                      "seconds_per_episode": None}
        (OUT / "estimate.json").write_text(json.dumps(est, indent=1))
        print(json.dumps(est, indent=1))
        return

    spend = Spend(OUT / a.spend_file, cap=a.cap)
    est = json.loads((OUT / "estimate.json").read_text()) if (OUT / "estimate.json").exists() else {}
    grid = ([(m, *c.split(":"), True) for m in models for c in a.cells.split(",")] if a.cells
            else list(cells(a.drop_hint_off, a.drop_misleading)))
    pool = [EDERER_MANSO] if a.split == "published" else test
    suffix = "__published" if a.split == "published" else ""
    for m, p, lab, h in grid:
        if m not in models or cell_key(m, p, lab, h) in a.skip_cells.split(","):
            continue
        cl = Client(m)
        per_ep = (est.get(m) or {}).get("dollars_per_episode", 0.0) or 0.0
        key = cell_key(m, p, lab, h) + suffix
        cache = OUT / f"cell__{key}.jsonl"
        t0 = time.time()
        status = run_cell(cl, p, lab, h, pool, a.episodes, cache, spend, a.workers, per_ep)
        print(f"{key}: {status}  cell ${spend.by_cell.get(key, 0):.2f}"
              f"  total ${spend.total:.2f}/{a.cap}  [{time.time() - t0:.0f}s]", flush=True)
        if status == "stopped at cap":
            print("SPEND CAP REACHED -- stopping the sweep", flush=True)
            break


if __name__ == "__main__":
    main()
