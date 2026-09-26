"""
Trajectoires « golden » : le contrat de synchronisation Python ⇄ Kotlin
(cf. todo.md §4.3 et docs/physics-spec.md).

Pour chaque niveau porté dans le runtime Android, on enregistre quelques
lancers simulés par ce moteur (la référence) : position de Quarky à chaque
pas, issue, Photons et contacts. Le test JUnit de `android/core-physics`
rejoue les mêmes lancers et exige les mêmes positions à 1e-6 près.

Lancers retenus par niveau (déterministes, tirés de la grille du validateur) :
  - `hint` : la solution de référence livrée dans le niveau ;
  - le premier lancer gagnant qui rate au moins un Photon ;
  - le premier lancer perdu (rebond de trop) ;
  - le premier timeout, s'il existe.
"""
import json
import os

from .export import read_level
from .simulate import simulate
from .validator import _grids, param_combos

# Niveaux dont le runtime Android porte les handlers (tunnel : wall,
# barrier, mirror). À étendre en même temps que le port Kotlin.
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
    """Lancers golden d'un niveau (cf. docstring du module)."""
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
