"""
Validateur de solvabilité : recherche exhaustive (grille discrétisée) sur
l'espace des paramètres de lancer déclaré par le niveau (`param_space`),
pour vérifier qu'au moins une combinaison atteint la cible, et calculer la
meilleure solution de référence (nombre de Photons collectés) utilisée pour
la notation à 3 étoiles (cf. skill gameplay-mechanics).
"""
import itertools
from dataclasses import dataclass, field

from .simulate import simulate


@dataclass
class Solution:
    params: dict
    photons: int
    photon_ids: list = field(default_factory=list)


def _grid_values(spec):
    if spec["type"] == "choice":
        return list(spec["values"])
    if spec["type"] == "range":
        vals = []
        v = spec["min"]
        while v <= spec["max"] + 1e-9:
            vals.append(round(v, 4))
            v += spec["step"]
        return vals
    raise ValueError(f"param_space type inconnu: {spec['type']}")


def solve(level: dict, max_solutions: int = 200):
    param_space = level["param_space"]
    keys = list(param_space.keys())
    grids = [_grid_values(param_space[k]) for k in keys]

    solutions = []
    total_photons = len(level.get("photons", []))

    for combo in itertools.product(*grids):
        params = dict(zip(keys, combo))
        result = simulate(level, params)
        if result.success:
            solutions.append(Solution(
                params=params,
                photons=len(result.photons_collected),
                photon_ids=sorted(result.photons_collected),
            ))
            if len(solutions) >= max_solutions and any(s.photons == total_photons for s in solutions):
                break

    solutions.sort(key=lambda s: -s.photons)
    return solutions


def validate(level: dict) -> dict:
    """Retourne un rapport de solvabilité + la meilleure solution (référence 3 étoiles)."""
    solutions = solve(level)
    total_photons = len(level.get("photons", []))
    best = solutions[0] if solutions else None
    return {
        "solvable": len(solutions) > 0,
        "solutions_found": len(solutions),
        "total_photons": total_photons,
        "best_solution": None if best is None else {
            "params": best.params,
            "photons_collected": best.photons,
            "photon_ids": best.photon_ids,
        },
        "max_photons_reachable": max((s.photons for s in solutions), default=0),
    }
