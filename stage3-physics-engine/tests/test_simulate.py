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


# --- superposition : deux copies fantômes, le tap mesure -----------------

def _superposition(detector_xy, target=(0.85, 0.55), wall_bounces=0):
    level = _level([
        # lame à -45° : Quarky qui monte continue vers le haut (copie
        # transmise) et part vers la droite (copie réfléchie)
        {"id": "S", "type": "splitter", "x": 0.4, "y": 0.55, "length": 0.34, "angle_deg": -45.0},
        {"id": "D", "type": "detector", "x": detector_xy[0], "y": detector_xy[1], "length": 0.06, "angle_deg": 90.0},
    ], concept="superposition", target=target)
    level["launcher"] = {"x": 0.4, "y": 0.9}
    level["max_wall_bounces"] = wall_bounces
    return level


def test_measure_keeps_copy_nearest_detector():
    # détecteur à droite : la mesure garde la copie réfléchie, qui atteint la cible
    res = simulate(_superposition((0.72, 0.33)), {"angle_deg": -90, "power": 0.6, "tap_time": 0.8})
    assert res.success
    assert res.contacts == [("S", "reflect"), ("D", "measure")]


def test_measure_can_keep_the_other_copy():
    # détecteur en haut : la mesure garde la copie transmise, qui rate la cible
    res = simulate(_superposition((0.4, 0.1)), {"angle_deg": -90, "power": 0.6, "tap_time": 0.8})
    assert not res.success


def test_target_ignores_unmeasured_copies():
    # sans tap, la copie réfléchie traverse la cible sans l'atteindre
    res = simulate(_superposition((0.72, 0.33), wall_bounces=5), {"angle_deg": -90, "power": 0.6})
    assert not res.success


def test_copy_crash_before_measure_is_decoherence():
    # tap trop tard : la copie transmise s'écrase au plafond avant la mesure
    res = simulate(_superposition((0.72, 0.33)), {"angle_deg": -90, "power": 0.6, "tap_time": 2.5})
    assert res.reason == "lost:decoherence"


def test_second_tap_must_follow_first():
    from engine.simulate import taps_ordered
    assert taps_ordered({"tap_time": 0.4, "tap_time_2": 0.9})
    assert not taps_ordered({"tap_time": 0.9, "tap_time_2": 0.4})
