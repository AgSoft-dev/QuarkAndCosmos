"""
"Golden" trajectories: the Python ⇄ Kotlin sync contract (see todo.md §4.3,
docs/physics-spec.md and docs/decisions/ADR-0005-golden-trajectories.md).

For each level ported to the Android runtime, a few launches simulated by
this engine (the reference) are recorded: Quarky's position at every step,
outcome, Photons and contacts. The JUnit test in `android/core-physics`
replays the same launches and requires the same positions within 1e-6.

Launches kept per level (deterministic, taken from the validator grid):
  - `hint`: the reference solution shipped in the level;
  - the first winning launch that misses at least one Photon;
  - the first lost launch (one bounce too many);
  - the first timeout, if any.
"""
import json
import os

from ..core.simulate import simulate
from ..solver.validator import _grids, param_combos
from .levels import read_level

# Levels whose handlers the Android runtime ports (tunnel: wall, barrier,
# mirror). Extend together with the Kotlin port.
GOLDEN_LEVELS = ("quantique_tunnel_1", "quantique_tunnel_2", "quantique_tunnel_3")


def _case(level, params):
    r = simulate(level, params, record_trail=True)
    return {
        "params": params,
        "success": r.success,
        "reason": r.reason,
        "steps": r.steps,
        "photons": sorted(r.photons_collected),
        "contacts": [list(c) for c in r.contacts],
        "trail": [list(p) for p in r.trail],
    }


def golden_for(level: dict) -> dict:
    """Golden launches of a level (see the module docstring)."""
    picks = [("hint", level["hint"]["params"])]
    wanted = {"partial_win": None, "lost": None, "timeout": None}
    for params in param_combos(*_grids(level)):
        r = simulate(level, params)
        if r.success and len(r.photons_collected) < len(level.get("photons", [])):
            kind = "partial_win"
        elif r.reason.startswith("lost"):
            kind = "lost"
        elif r.reason == "timeout":
            kind = "timeout"
        else:
            continue
        if wanted[kind] is None:
            wanted[kind] = params
        if all(v is not None for v in wanted.values()):
            break
    picks += [(k, v) for k, v in wanted.items() if v is not None]
    return {
        "level_id": level["id"],
        "cases": [dict(name=name, **_case(level, params)) for name, params in picks],
    }


def write_goldens(levels_dir: str, out_dir: str) -> list:
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for name in GOLDEN_LEVELS:
        level = read_level(os.path.join(levels_dir, f"{name}.json"))
        path = os.path.join(out_dir, f"{name}.golden.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(golden_for(level), f, ensure_ascii=False)
            f.write("\n")
        paths.append(path)
    return paths
