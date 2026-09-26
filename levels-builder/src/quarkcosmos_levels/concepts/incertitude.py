"""
Concept `incertitude` — Heisenberg uncertainty principle (no obstacle of its own: box walls only). Plugin of the concept registry (concepts/__init__.py):
the default handler, the obstacle types it owns, and the level template of each
difficulty (1 discover → 2 sequence → 3 chain, see the gameplay-mechanics skill).
"""
from .common import door_wall
from .handlers import wall_reflect

CONCEPT = "incertitude"
# Key of the Codex line in content/codex/<lang>/quantique.json.
CODEX_KEY = "incertitude"


# Default handler of the concept's obstacles, and the obstacle types it owns.
DEFAULT_HANDLER = wall_reflect
HANDLERS = {}


# Continuous dial (slider): with notches, speed and arrival time would be
# discrete too and the moving target would become a lottery.
PRECISIONS = {"type": "range", "min": 0.3, "max": 1.0, "step": 0.05}


def _level_1():
    # Oscillating element (see gameplay-mechanics): the target drifts
    # slightly — it combines with the existing precision/speed trade-off
    # (aiming right is no longer enough, you must also arrive at the right
    # moment).
    return {
        "launcher": {"x": 0.1, "y": 0.6},
        "target": {"x": 0.85, "y": 0.5, "r": 0.03, "motion": {"axis": "y", "amplitude": 0.02, "period": 0.8}},
        "obstacles": [],
        "param_space": {
            "angle_deg": {"type": "range", "min": -15, "max": 5, "step": 0.5},
            "precision": {"type": "choice", "values": [0.3, 0.5, 0.7, 0.8, 0.9, 1.0]},
        },
    }


def _level_2():
    # Dilemma: a narrow slit needs precise aim (high dial)... which slows
    # Quarky down, while the target behind the slit drifts. An imprecise dial
    # is fast but only aims in big steps: find the trade-off that clears the
    # slit AND arrives at the right moment.
    return {
        "launcher": {"x": 0.1, "y": 0.6},
        "target": {"x": 0.85, "y": 0.39, "r": 0.05,
                   "motion": {"axis": "y", "amplitude": 0.04, "period": 1.1}},
        "obstacles": door_wall("slit", 0.45, 0.465, 0.535),
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -30, "max": 5, "step": 0.5},
            "precision": PRECISIONS,
        },
    }


def _level_3():
    # Two aligned slits (tighter opening) and a faster-drifting target: the
    # precision/speed trade-off gets tighter.
    return {
        "launcher": {"x": 0.1, "y": 0.7},
        "target": {"x": 0.88, "y": 0.33, "r": 0.04,
                   "motion": {"axis": "y", "amplitude": 0.07, "period": 0.8}},
        "obstacles": door_wall("slit1", 0.35, 0.535, 0.625) + door_wall("slit2", 0.6, 0.42, 0.51),
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -35, "max": 5, "step": 0.5},
            "precision": PRECISIONS,
        },
    }


def build(difficulty: int) -> dict:
    """Level template (layout, `must_contact`, `param_space`) before Photon placement."""
    return {1: _level_1, 2: _level_2, 3: _level_3}[difficulty]()


def param_space(difficulty: int) -> dict:
    """Public setting ranges of the level's dials (shipped in the level file)."""
    return build(difficulty)["param_space"]
