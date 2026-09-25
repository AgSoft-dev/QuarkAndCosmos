"""
Validateur de solvabilité : recherche exhaustive (grille discrétisée) sur
l'espace des paramètres de lancer déclaré par le niveau (`param_space`),
pour vérifier qu'au moins une combinaison atteint la cible, et calculer la
meilleure solution de référence (nombre de Photons collectés) utilisée pour
la notation à 3 étoiles (cf. skill gameplay-mechanics).

Le placement des Photons et la distribution 1-2-3 étoiles vivent dans
stars.py (lancer de rayons).
"""
import itertools
from dataclasses import dataclass, field

from .simulate import TAP_MIN_TIME, simulate, taps_ordered
from .stars import star_profile


@dataclass
class Solution:
    params: dict
    photons: int
    photon_ids: list = field(default_factory=list)
    contacts: list = field(default_factory=list)


def uses_mechanic(level: dict, contacts) -> bool:
    """
    Vrai si les contacts d'un lancer contiennent, dans l'ordre, chaque
    (obstacle, événement) de `must_contact` (ex : [["s1", "bounce"],
    ["s2", "wave"]] = rebond en particule sur s1 PUIS traversée en onde de
    s2). Un lancer réussi qui ne le vérifie pas est un contournement : le
    niveau se résout sans la mécanique qu'il est censé enseigner.
    """
    required = [tuple(c) for c in level.get("must_contact", [])]
    it = iter(tuple(c) for c in contacts)
    return all(any(c == req for c in it) for req in required)


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


def _grids(level):
    param_space = level["param_space"]
    keys = list(param_space.keys())
    grids = [_grid_values(param_space[k]) for k in keys]
    for i, key in enumerate(keys):
        if key.startswith("tap_time"):
            # Un tap avant TAP_MIN_TIME est un réglage pré-tir déguisé (cf.
            # simulate.TAP_MIN_TIME) : il ne fait pas partie de l'espace jouable.
            grids[i] = [t for t in grids[i] if t >= TAP_MIN_TIME]
    return keys, grids


def param_combos(keys, grids):
    """Lancers de la grille (taps successifs dans l'ordre, cf. taps_ordered)."""
    for combo in itertools.product(*grids):
        params = dict(zip(keys, combo))
        if taps_ordered(params):
            yield params


def grid_size(level: dict) -> int:
    return sum(1 for _ in param_combos(*_grids(level)))


def solve(level: dict, max_solutions=200):
    """max_solutions=None : parcours exhaustif (nécessaire pour la tolérance)."""
    keys, grids = _grids(level)

    solutions = []
    total_photons = len(level.get("photons", []))

    for params in param_combos(keys, grids):
        result = simulate(level, params)
        if result.success:
            solutions.append(Solution(
                params=params,
                photons=len(result.photons_collected),
                photon_ids=sorted(result.photons_collected),
                contacts=result.contacts,
            ))
            if (max_solutions is not None and len(solutions) >= max_solutions
                    and any(s.photons == total_photons for s in solutions)):
                break

    solutions.sort(key=lambda s: -s.photons)
    return solutions


def validate(level: dict) -> dict:
    """
    Rapport de solvabilité + meilleure solution (référence 3 étoiles).

    `tolerance` = part de la grille de paramètres qui atteint la cible ;
    `three_star_tolerance` = part qui atteint la cible avec tous les
    Photons. Mesure de "fragilité" d'un niveau (un niveau solvable sur 2
    combinaisons seulement est techniquement valide mais injouable).
    """
    solutions = solve(level, max_solutions=None)
    total_photons = len(level.get("photons", []))
    size = grid_size(level)
    best = solutions[0] if solutions else None
    full = sum(1 for s in solutions if s.photons == total_photons)
    return {
        "solvable": len(solutions) > 0,
        "solutions_found": len(solutions),
        "grid_size": size,
        "tolerance": round(len(solutions) / size, 4) if size else 0.0,
        "three_star_tolerance": round(full / size, 4) if size and total_photons else 0.0,
        "total_photons": total_photons,
        "best_solution": None if best is None else {
            "params": best.params,
            "photons_collected": best.photons,
            "photon_ids": best.photon_ids,
        },
        "max_photons_reachable": max((s.photons for s in solutions), default=0),
        # lancers réussis qui contournent la mécanique (cf. uses_mechanic) ;
        # doit valoir 0 pour un niveau publié
        "bypass_solutions": sum(1 for s in solutions if not uses_mechanic(level, s.contacts)),
        "star_profile": star_profile(level) if solutions else None,
    }
