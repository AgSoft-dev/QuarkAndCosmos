"""
Validateur de solvabilité : recherche exhaustive (grille discrétisée) sur
l'espace des paramètres de lancer déclaré par le niveau (`param_space`),
pour vérifier qu'au moins une combinaison atteint la cible, et calculer la
meilleure solution de référence (nombre de Photons collectés) utilisée pour
la notation à 3 étoiles (cf. skill gameplay-mechanics).

Il place aussi les Photons (cf. gameplay-mechanics — "c'est lui qui
déterminera leur position définitive, pas un placement à la main") : le long
de la trajectoire de la solution la plus robuste du niveau.
"""
import copy
import itertools
from dataclasses import dataclass, field

from . import vec
from .simulate import TAP_MIN_TIME, simulate

PHOTONS_PER_LEVEL = 3
PHOTON_RADIUS = 0.03
# Positions des Photons le long de la trajectoire de référence (fraction du
# trajet lanceur -> cible). Les deux derniers tombent en général après
# l'obstacle du concept, donc sur la partie du trajet qui l'utilise.
PHOTON_FRACTIONS = (0.3, 0.55, 0.8)
# Marge libre minimale entre un Photon et un obstacle/la cible/le lanceur.
PHOTON_CLEARANCE = 0.02


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


def _grids(level):
    param_space = level["param_space"]
    keys = list(param_space.keys())
    grids = [_grid_values(param_space[k]) for k in keys]
    if "tap_time" in param_space:
        # Un tap avant TAP_MIN_TIME est un réglage pré-tir déguisé (cf.
        # simulate.TAP_MIN_TIME) : il ne fait pas partie de l'espace jouable.
        i = keys.index("tap_time")
        grids[i] = [t for t in grids[i] if t >= TAP_MIN_TIME]
    return keys, grids


def grid_size(level: dict) -> int:
    size = 1
    for g in _grids(level)[1]:
        size *= len(g)
    return size


def solve(level: dict, max_solutions=200):
    """max_solutions=None : parcours exhaustif (nécessaire pour la tolérance)."""
    keys, grids = _grids(level)

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
    }


def _most_robust(level, solutions):
    """Solution qui a le plus de voisines solvables dans la grille (écart
    d'au plus un cran sur chaque paramètre) : la plus éloignée des bords de
    la fenêtre de réussite, donc la plus sûre pour y poser des Photons."""
    keys, grids = _grids(level)
    index = [{v: i for i, v in enumerate(g)} for g in grids]
    points = [tuple(index[k][s.params[key]] for k, key in enumerate(keys)) for s in solutions]

    def neighbours(p):
        return sum(1 for q in points if max(abs(a - b) for a, b in zip(p, q)) <= 1)

    scores = [neighbours(p) for p in points]
    return solutions[scores.index(max(scores))]


def _clear_of_objects(level, pos, t, r):
    from .simulate import _oscillate
    for obs in level.get("obstacles", []):
        ox, oy = _oscillate(obs["x"], obs["y"], obs.get("motion"), t)
        if vec.dist(pos, (ox, oy)) < obs.get("r", 0.03) + r + PHOTON_CLEARANCE:
            return False
    tgt = level["target"]
    if vec.dist(pos, (tgt["x"], tgt["y"])) < tgt.get("r", 0.045) + r + PHOTON_CLEARANCE:
        return False
    lau = level["launcher"]
    return vec.dist(pos, (lau["x"], lau["y"])) >= 0.05 + r


def place_photons(level: dict) -> dict:
    """
    Retourne une copie du niveau avec PHOTONS_PER_LEVEL Photons posés sur la
    trajectoire de la solution la plus robuste, aux fractions
    PHOTON_FRACTIONS du trajet (décalées si elles tombent sur un objet).
    Lève ValueError si le niveau n'est pas solvable.
    """
    bare = copy.deepcopy(level)
    bare["photons"] = []
    solutions = solve(bare, max_solutions=None)
    if not solutions:
        raise ValueError(f"Niveau non solvable, impossible de placer les Photons: {level.get('id')}")
    anchor = _most_robust(bare, solutions)
    trail = simulate(bare, anchor.params, record_trail=True).trail

    from .simulate import DT
    photons = []
    used = set()
    for n, frac in enumerate(PHOTON_FRACTIONS, start=1):
        base = int(frac * (len(trail) - 1))
        # cherche l'indice libre le plus proche de la fraction visée
        for delta in sorted(range(-len(trail), len(trail)), key=abs):
            i = base + delta
            if 0 <= i < len(trail) and i not in used and all(abs(i - u) > 10 for u in used):
                if _clear_of_objects(bare, trail[i], (i + 1) * DT, PHOTON_RADIUS):
                    used.add(i)
                    x, y = trail[i]
                    photons.append({"id": f"p{n}", "x": round(x, 3), "y": round(y, 3), "r": PHOTON_RADIUS})
                    break
        else:
            raise ValueError(f"Aucune position libre pour le Photon p{n}: {level.get('id')}")

    placed = copy.deepcopy(level)
    placed["photons"] = photons
    return placed
