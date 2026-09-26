"""
Export a level to JSON, as two files:

- `content/levels/quantique/<name>.json` — **shipped in the game**: geometry,
  objects, Photons, public setting ranges (`param_space`, for the UI dials)
  and `hint` (the reference solution's parameters, for the "first segment"
  hint offered after 5 failures). No player-facing text: the Codex lines live
  in `content/codex/<lang>/quantique.json`, keyed by concept.
- `levels-builder/meta/<name>.meta.json` — **dev only**: everything the
  validator computes (solvability, tolerances, bypasses, full reference
  solution, star profile) + `must_contact`, which is only used to validate.

`read_level` joins the two back together (see its docstring), so
`validate content/levels/quantique/<name>.json` works as before.
See docs/level-schema.md for the field reference.
"""
import json
import os
import sys

from .. import paths
from ..core.simulate import MAX_WALL_BOUNCES
from ..solver.validator import validate

# Version of the JSON format consumed by the game. Bump it on every
# incompatible change (renamed/removed field, changed meaning) so the client
# can refuse a pack it cannot read.
# v2: shipped level / dev meta split, `hint` replaces `reference_solution` in
# the shipped file, `max_wall_bounces` always explicit.
# v3: `codex_text` removed (player-facing text moved to content/codex/<lang>/).
# v4: approved concept fixes (ADR-0008): barrier `thickness`/`thickness_motion`
# (no energy_threshold), `rungs` + `lock` + Photon `rung`, `cone` + precision,
# `magnet` (Stern–Gerlach), `crystal` + gate `pair`, `slit` grating; polygon shapes.
SCHEMA_VERSION = 4

# Fields of the shipped level, in this order (readable diffs). A level field
# unknown here is appended at the end rather than silently dropped.
SHIPPED_KEYS = (
    "id", "scale", "concept", "difficulty",
    "launcher", "target", "rungs", "cone", "obstacles", "photons",
    "max_wall_bounces", "param_space",
)
# Level fields used only by the validator: never shipped to the game.
DEV_ONLY_KEYS = ("must_contact",)


def build_export_payloads(level: dict) -> tuple:
    """(shipped level, dev meta) for a generated level."""
    report = validate(level)
    # schema_version first in both files, and always the current engine's
    # (even when re-exporting a level read from an older JSON).
    level = {k: v for k, v in level.items() if k not in ("schema_version", "codex_text")}
    # Default resolved here: the game doesn't need to know the engine's.
    level.setdefault("max_wall_bounces", MAX_WALL_BOUNCES)

    shipped = {"schema_version": SCHEMA_VERSION}
    for k in SHIPPED_KEYS:
        if k in level:
            shipped[k] = level[k]
    for k, v in level.items():
        if k not in shipped and k not in DEV_ONLY_KEYS:
            shipped[k] = v
    best = report["best_solution"]
    shipped["hint"] = None if best is None else {"params": best["params"]}

    meta = {
        "schema_version": SCHEMA_VERSION,
        "id": level.get("id"),
        "must_contact": level.get("must_contact", []),
        "solvable": report["solvable"],
        "reference_solution": best,
        "max_photons_reachable": report["max_photons_reachable"],
        "tolerance": report["tolerance"],
        "three_star_tolerance": report["three_star_tolerance"],
        "bypass_solutions": report["bypass_solutions"],
        "star_profile": report["star_profile"],
    }
    return shipped, meta


def meta_path_for(level_path) -> str:
    """Meta file of a level: `levels-builder/meta/<name>.meta.json` for the
    shipped pack, or a `meta/` folder next to the level for any other pack
    (e.g. a scratch export)."""
    folder, name = os.path.split(os.path.abspath(level_path))
    stem = name[:-len(".json")] if name.endswith(".json") else name
    shipped_pack = paths.LEVELS_DIR.is_dir() and os.path.isdir(folder) and os.path.samefile(folder, paths.LEVELS_DIR)
    meta_dir = str(paths.META_DIR) if shipped_pack else os.path.join(folder, "meta")
    return os.path.join(meta_dir, f"{stem}.meta.json")


def _dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_level(level: dict, path) -> tuple:
    """Write the shipped level to `path` and its meta (see meta_path_for);
    return (shipped, meta)."""
    shipped, meta = build_export_payloads(level)
    meta_path = meta_path_for(path)
    os.makedirs(os.path.dirname(meta_path) or ".", exist_ok=True)
    _dump(shipped, path)
    _dump(meta, meta_path)
    return shipped, meta


def read_level(path) -> dict:
    """
    Level ready for validate/solve: the shipped file + `must_contact` read
    from its meta (see meta_path_for). Without a meta (shipped pack alone),
    the level can still be simulated but `bypass_solutions` checks nothing:
    this is reported on stderr. An old v1 JSON (must_contact included) is read
    as is.
    """
    with open(path, "r", encoding="utf-8") as f:
        level = json.load(f)
    meta_path = meta_path_for(path)
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            level["must_contact"] = json.load(f).get("must_contact", [])
    elif "must_contact" not in level:
        print(f"[warning] {meta_path} missing: must_contact unknown, "
              "bypasses not checked", file=sys.stderr)
    return level
