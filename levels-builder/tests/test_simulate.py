"""Base rules of the simulation loop (see core/simulate.py)."""
import pytest

from quarkcosmos_levels.core import vec
from quarkcosmos_levels.core.simulate import TAP_MIN_TIME, simulate, taps_ordered
from quarkcosmos_levels.solver.validator import _grids


def _level(obstacles, concept="spin", target=(5.0, 5.0)):
    # Target outside the box: we watch the trajectory, not the success.
    return {
        "concept": concept,
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": target[0], "y": target[1], "r": 0.05},
        "obstacles": obstacles,
        "photons": [],
    }


def test_magnet_deflects_once_per_contact():
    # Before the fix, the deflection was re-applied at every step spent
    # inside the pole's radius (total deflection = N * kick).
    magnet = {"id": "magnet", "type": "magnet", "x": 0.4, "y": 0.5, "r": 0.06, "up_deg": -90, "kick_deg": 30}
    res = simulate(_level([magnet]), {"angle_deg": 0, "power": 0.5, "spin_up": True}, record_trail=True)
    trail = res.trail
    after = vec.sub(trail[60], trail[59])
    assert vec.angle_of(after) == pytest.approx(-30, abs=1e-6)


def test_taps_before_min_time_are_not_searched():
    level = _level([])
    level["param_space"] = {"tap_time": {"type": "range", "min": 0.0, "max": 0.5, "step": 0.05}}
    _, grids = _grids(level)
    assert min(grids[0]) >= TAP_MIN_TIME


# --- superposition: two ghost copies, the tap measures ----------------------

def _superposition(detector_xy, target=(0.85, 0.55), wall_bounces=0):
    level = _level([
        # splitter at -45°: a rising Quarky goes on upwards (transmitted
        # copy) and leaves to the right (reflected copy)
        {"id": "S", "type": "splitter", "x": 0.4, "y": 0.55, "length": 0.34, "angle_deg": -45.0},
        {"id": "D", "type": "detector", "x": detector_xy[0], "y": detector_xy[1], "length": 0.06, "angle_deg": 90.0},
    ], concept="superposition", target=target)
    level["launcher"] = {"x": 0.4, "y": 0.9}
    level["max_wall_bounces"] = wall_bounces
    return level


def test_measure_keeps_copy_nearest_detector():
    # detector on the right: the measurement keeps the reflected copy, which reaches the target
    res = simulate(_superposition((0.72, 0.33)), {"angle_deg": -90, "power": 0.6, "tap_time": 0.8})
    assert res.success
    assert res.contacts == [("S", "reflect"), ("D", "measure")]


def test_measure_can_keep_the_other_copy():
    # detector at the top: the measurement keeps the transmitted copy, which misses the target
    res = simulate(_superposition((0.4, 0.1)), {"angle_deg": -90, "power": 0.6, "tap_time": 0.8})
    assert not res.success


def test_target_ignores_unmeasured_copies():
    # without a tap, the reflected copy passes through the target without reaching it
    res = simulate(_superposition((0.72, 0.33), wall_bounces=5), {"angle_deg": -90, "power": 0.6})
    assert not res.success


def test_copy_crash_before_measure_is_decoherence():
    # tap too late: the transmitted copy crashes on the ceiling before the measurement
    res = simulate(_superposition((0.72, 0.33)), {"angle_deg": -90, "power": 0.6, "tap_time": 2.5})
    assert res.reason == "lost:decoherence"


def test_second_tap_must_follow_first():
    assert taps_ordered({"tap_time": 0.4, "tap_time_2": 0.9})
    assert not taps_ordered({"tap_time": 0.9, "tap_time_2": 0.4})
