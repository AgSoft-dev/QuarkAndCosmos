"""
Solvability validator: exhaustive search (discretised grid) over the launch
parameter space declared by the level (`param_space`), to check that at
least one combination reaches the target, and to compute the best reference
solution (Photons collected) used for 3-star scoring (see the
gameplay-mechanics skill).

Photon placement and the 1-2-3 star distribution live in stars.py (ray
tracing).
"""
import itertools
from dataclasses import dataclass, field

from ..core.simulate import TAP_MIN_TIME, simulate, taps_ordered
from .stars import star_profile


@dataclass
class Solution:
    params: dict
    photons: int
    photon_ids: list = field(default_factory=list)
    contacts: list = field(default_factory=list)


def uses_mechanic(level: dict, contacts) -> bool:
    """
    True if a launch's contacts contain, in order, every (obstacle, event)
    of `must_contact` (e.g. [["s1", "bounce"], ["s2", "wave"]] = particle
    bounce on s1 THEN wave crossing of s2). A successful launch that fails
    this is a bypass: the level is solved without the mechanic it is meant
    to teach.
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
    raise ValueError(f"unknown param_space type: {spec['type']}")


def _grids(level):
    param_space = level["param_space"]
    keys = list(param_space.keys())
    grids = [_grid_values(param_space[k]) for k in keys]
    for i, key in enumerate(keys):
        if key.startswith("tap_time"):
            # A tap before TAP_MIN_TIME is a disguised pre-launch setting (see
            # simulate.TAP_MIN_TIME): it is not part of the playable space.
            grids[i] = [t for t in grids[i] if t >= TAP_MIN_TIME]
    return keys, grids


def param_combos(keys, grids):
    """Grid launches (successive taps in order, see taps_ordered)."""
    for combo in itertools.product(*grids):
        params = dict(zip(keys, combo))
        if taps_ordered(params):
            yield params


def grid_size(level: dict) -> int:
    return sum(1 for _ in param_combos(*_grids(level)))


def solve(level: dict, max_solutions=200):
    """max_solutions=None: exhaustive sweep (needed for the tolerance)."""
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
    Solvability report + best solution (3-star reference).

    `tolerance` = share of the parameter grid that reaches the target;
    `three_star_tolerance` = share that reaches it with every Photon. A
    measure of a level's "brittleness" (a level solvable with only 2
    combinations is technically valid but unplayable).
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
        # successful launches that bypass the mechanic (see uses_mechanic);
        # must be 0 for a shipped level
        "bypass_solutions": sum(1 for s in solutions if not uses_mechanic(level, s.contacts)),
        "star_profile": star_profile(level) if solutions else None,
    }
