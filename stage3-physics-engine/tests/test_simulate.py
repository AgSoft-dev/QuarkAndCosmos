"""Règles de base de la boucle de simulation (cf. engine/simulate.py)."""
import pytest

from engine import vec
from engine.simulate import TAP_MIN_TIME, simulate
from engine.validator import _grids


def _level(obstacles, concept="spin", target=(5.0, 5.0)):
    # Cible hors de la boîte : on observe la trajectoire, pas la réussite.
    return {
        "concept": concept,
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": target[0], "y": target[1], "r": 0.05},
        "obstacles": obstacles,
        "photons": [],
    }


def test_pole_deflects_once_per_contact():
    # Avant correctif, la déviation était ré-appliquée à chaque pas passé
    # dans le rayon du pôle (déviation totale = N * kick).
    pole = {"id": "pole", "type": "pole", "x": 0.4, "y": 0.5, "r": 0.06, "pole": "+", "kick_deg": -30}
    res = simulate(_level([pole]), {"angle_deg": 0, "power": 0.5, "spin_up": True}, record_trail=True)
    trail = res.trail
    after = vec.sub(trail[60], trail[59])
    assert vec.angle_of(after) == pytest.approx(-30, abs=1e-6)


def test_taps_before_min_time_are_not_searched():
    level = _level([])
    level["param_space"] = {"tap_time": {"type": "range", "min": 0.0, "max": 0.5, "step": 0.05}}
    _, grids = _grids(level)
    assert min(grids[0]) >= TAP_MIN_TIME
