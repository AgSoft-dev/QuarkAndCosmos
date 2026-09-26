"""
Concept `quantification` — Energy quantisation (reuses the tunnel barrier as a notch filter). Plugin of the concept registry (concepts/__init__.py):
the default handler, the obstacle types it owns, and the level template of each
difficulty (1 discover → 2 sequence → 3 chain, see the gameplay-mechanics skill).
"""
from .common import barrier, door_wall, seg
from .handlers import wall_reflect

CONCEPT = "quantification"
# Key of the Codex line in content/codex/<lang>/quantique.json.
CODEX_KEY = "quantification"


# Default handler of the concept's obstacles, and the obstacle types it owns.
DEFAULT_HANDLER = wall_reflect
HANDLERS = {}


QUANTA = [0.3, 0.45, 0.6, 0.75, 0.9]


def _level_1():
    # Oscillating element (see gameplay-mechanics), same principle as the
    # tunnel: the barrier's threshold varies over time, on top of the
    # launcher's fixed energy notches (the two variables combine).
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.85, "y": 0.5, "r": 0.05},
        "obstacles": [
            {"id": "barrier", "type": "barrier", "x": 0.45, "y": 0.5, "r": 0.05,
             "energy_threshold": 0.65,
             "threshold_motion": {"amplitude": 0.45, "period": 0.2, "phase": 1.2}},
        ],
        "must_contact": [["barrier", "pass"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -3, "max": 3, "step": 1},
            "power": {"type": "choice", "values": [0.2, 0.4, 0.6, 0.8, 1.0]},
        },
    }


def _level_2():
    # The launcher only has 5 energy notches. Two barriers in series with
    # oscillating thresholds: each notch gives a different speed AND arrival
    # instants: only two notches (0.45 and 0.9) hit a trough at both barriers.
    # (Pending the "lock tuned to one notch" redesign — [GATE] in todo.md.)
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.88, "y": 0.5, "r": 0.05},
        "obstacles": [
            barrier("b1", 0.36, 0.4, 0.36, 0.6, base=0.6, amplitude=0.4, period=0.7, phase=0.0),
            barrier("b2", 0.64, 0.4, 0.64, 0.6, base=0.6, amplitude=0.4, period=0.7, phase=0.8),
        ] + door_wall("w1", 0.36, 0.4, 0.6) + door_wall("w2", 0.64, 0.4, 0.6),
        "must_contact": [["b1", "pass"], ["b2", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "choice", "values": QUANTA},
        },
    }


def _level_3():
    # Three barriers, one after a mirror: the right notch must hit a trough
    # three times in a row: only one notch (0.45) does. You can't "dose":
    # you have to choose.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.6, "y": 0.16, "r": 0.06},
        "obstacles": [
            barrier("b1", 0.3, 0.71, 0.3, 0.89, base=0.6, amplitude=0.4, period=0.7, phase=0.0),
            barrier("b2", 0.44, 0.71, 0.44, 0.89, base=0.6, amplitude=0.4, period=0.7, phase=3.6),
            seg("m", "mirror", 0.53, 0.87, 0.67, 0.73),
            barrier("b3", 0.51, 0.45, 0.69, 0.45, base=0.6, amplitude=0.4, period=0.7, phase=0.8),
            seg("ceilL", "wall", 0.44, 0.45, 0.51, 0.45),
            seg("ceilR", "wall", 0.69, 0.45, 1.05, 0.45),
        ] + door_wall("w1", 0.3, 0.71, 0.89) + door_wall("w2", 0.44, 0.71, 0.89),
        "must_contact": [["b1", "pass"], ["b2", "pass"], ["m", "bounce"], ["b3", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "choice", "values": QUANTA},
        },
    }


def build(difficulty: int) -> dict:
    """Level template (layout, `must_contact`, `param_space`) before Photon placement."""
    return {1: _level_1, 2: _level_2, 3: _level_3}[difficulty]()


def param_space(difficulty: int) -> dict:
    """Public setting ranges of the level's dials (shipped in the level file)."""
    return build(difficulty)["param_space"]
