"""Count recorded episodes of one arm on the 16 extension worlds (val[16:32]). Used by the 24-world launchers.

    python3 scripts/count_new_worlds.py <arm> <model>
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from env.world_generator import load_world_set, world_id  # noqa: E402

arm, model = sys.argv[1], sys.argv[2]
new = {world_id(w) for w in load_world_set(ROOT / "data" / "worlds_main.json")["val"][16:32]}
f = ROOT / "results" / "multiagent" / f"{arm}__{model}.jsonl"
keys = set()
if f.exists():
    for line in f.open():
        if line.strip():
            r = json.loads(line)
            if r["world_id"] in new:
                keys.add(r["key"])
print(len(keys))
