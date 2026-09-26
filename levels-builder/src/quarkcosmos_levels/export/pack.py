"""
The beta pack manifest: `content/levels/quantique/pack.json` lists the levels
the closed test ships — one per concept, difficulty BETA_DIFFICULTY, in play
order (user decision 2026-09-26, todo.md §0) — with each file's SHA-256, so
the app and CI can check they ship exactly the validated files.
"""
import hashlib
import json
import os

from .. import paths
from ..concepts import ALL_CONCEPTS

# The beta ships the "discover" layout of each concept (gameplay-mechanics:
# one level per concept, little or no intra-concept ramp).
BETA_DIFFICULTY = 1
PACK_FILE = "pack.json"


def pack_manifest(levels_dir=None, world: str = "quantique") -> dict:
    levels_dir = str(levels_dir or paths.LEVELS_DIR)
    levels = []
    for concept_id in ALL_CONCEPTS:
        name = f"{world}_{concept_id}_{BETA_DIFFICULTY}.json"
        with open(os.path.join(levels_dir, name), "rb") as f:
            raw = f.read()
        level = json.loads(raw)
        levels.append({
            "id": level["id"],
            "concept": concept_id,
            "file": name,
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    schema = json.loads(open(os.path.join(levels_dir, levels[0]["file"]), encoding="utf-8").read())["schema_version"]
    return {"world": world, "scope": "beta", "schema_version": schema, "levels": levels}


def write_pack(levels_dir=None, world: str = "quantique") -> str:
    levels_dir = str(levels_dir or paths.LEVELS_DIR)
    path = os.path.join(levels_dir, PACK_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pack_manifest(levels_dir, world), f, ensure_ascii=False, indent=2)
        f.write("\n")
    return path
