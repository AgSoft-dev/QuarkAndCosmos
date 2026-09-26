"""
Concept `spin` — Quantum spin. Plugin of the concept registry (concepts/__init__.py):
the default handler, the obstacle types it owns, and the level template of each
difficulty (1 discover → 2 sequence → 3 chain, see the gameplay-mechanics skill).
"""
from ..core import vec
from ..core.simulate import TAP_MIN_TIME

CONCEPT = "spin"
# Key of the Codex line in content/codex/<lang>/quantique.json.
CODEX_KEY = "spin"


def spin_pole(obstacle, pos, vel, params, state):
    """
    Spin polarity (+/-) deciding whether the obstacle attracts or repels.
    Pre-launch setting (spin_up = starting polarity, see gameplay-mechanics)
    AND in-flight action: a tap (params["tap_time"]) flips the polarity once
    during the flight — two variables combine to aim for the right contact at
    the right instant.
    """
    spin_up = params.get("spin_up", True)
    if state.get("tapped", False):
        spin_up = not spin_up
    pole = obstacle.get("pole", "+")
    attract = (spin_up and pole == "+") or (not spin_up and pole == "-")
    kick = obstacle.get("kick_deg", 40)
    kick = kick if attract else -kick
    ang = vec.angle_of(vel) + kick
    return vec.from_angle(ang, vec.mag(vel)), "deflect"


# Default handler of the concept's obstacles, and the obstacle types it owns.
DEFAULT_HANDLER = spin_pole
HANDLERS = {"pole": spin_pole}


def _level_1():
    # Combines with the pre-launch setting (spin_up = starting polarity): a
    # tap during the flight (see gameplay-mechanics) flips the polarity once —
    # two variables instead of one to aim for the right contact.
    # Target placed on the "repelled" branch (downward deflection): either
    # start spin down, or start spin up and tap BEFORE touching the pole. The
    # deflection applies only once per contact (see simulate.py) — the old
    # target (0.867, 0.69) was only reached thanks to a deflection re-applied
    # at every step, and only within 1° of aim.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.72, "y": 0.84, "r": 0.05},
        "obstacles": [
            {"id": "pole", "type": "pole", "x": 0.4, "y": 0.42, "r": 0.06,
             "pole": "+", "kick_deg": -60},
        ],
        "must_contact": [["pole", "deflect"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -20, "max": 0, "step": 1},
            "power": {"type": "choice", "values": [0.5, 0.7]},
            "spin_up": {"type": "choice", "values": [True, False]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 0.8, "step": 0.05},
        },
    }


def _level_2():
    # Two "+" poles in series (cascaded Stern-Gerlach style), each deflecting
    # by 45°: spin up = attracted (upwards), spin down = repelled. To rise at
    # A then return to horizontal at B, start spin up and flip the spin
    # BETWEEN the two poles. The only combination.
    return {
        "launcher": {"x": 0.1, "y": 0.72},
        "target": {"x": 0.86, "y": 0.51, "r": 0.05},
        "obstacles": [
            {"id": "A", "type": "pole", "x": 0.36, "y": 0.72, "r": 0.06, "pole": "+", "kick_deg": -45},
            {"id": "B", "type": "pole", "x": 0.555, "y": 0.465, "r": 0.06, "pole": "+", "kick_deg": -45},
        ],
        "must_contact": [["A", "deflect"], ["B", "deflect"]],
        # no bank shots: touching a wall = particle lost
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -10, "max": 10, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "spin_up": {"type": "choice", "values": [True, False]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.4, "step": 0.05},
        },
    }


def _level_3():
    # Three poles with signs +, −, + (deflections 40°, 40°, 60°): the player
    # must READ each pole's sign. Rise at A (spin up, attracted by +), rise
    # again at B (pole −, must be attracted so spin down: flip between A and
    # B), then come back down at C (pole +, spin down = repelled). Pole C
    # oscillates: the power must also time the arrival.
    return {
        "launcher": {"x": 0.1, "y": 0.9},
        "target": {"x": 0.792, "y": 0.416, "r": 0.05},
        "obstacles": [
            {"id": "A", "type": "pole", "x": 0.32, "y": 0.9, "r": 0.06, "pole": "+", "kick_deg": -40},
            {"id": "B", "type": "pole", "x": 0.49, "y": 0.707, "r": 0.06, "pole": "-", "kick_deg": -40},
            {"id": "C", "type": "pole", "x": 0.492, "y": 0.47, "r": 0.06, "pole": "+", "kick_deg": -60,
             "motion": {"axis": "x", "amplitude": 0.05, "period": 1.2}},
        ],
        "must_contact": [["A", "deflect"], ["B", "deflect"], ["C", "deflect"]],
        # no bank shots: touching a wall = particle lost
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -10, "max": 10, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "spin_up": {"type": "choice", "values": [True, False]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.8, "step": 0.05},
        },
    }


def build(difficulty: int) -> dict:
    """Level template (layout, `must_contact`, `param_space`) before Photon placement."""
    return {1: _level_1, 2: _level_2, 3: _level_3}[difficulty]()


def param_space(difficulty: int) -> dict:
    """Public setting ranges of the level's dials (shipped in the level file)."""
    return build(difficulty)["param_space"]
