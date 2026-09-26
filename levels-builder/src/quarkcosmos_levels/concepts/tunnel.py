"""
Concept `tunnel` — Tunnel effect. Plugin of the concept registry (concepts/__init__.py):
the default handler, the obstacle types it owns, and the level template of each
difficulty (1 discover → 2 sequence → 3 chain, see the gameplay-mechanics skill).
"""
from ..core import vec
from .common import barrier, door_wall, seg
from .handlers import _bounce

CONCEPT = "tunnel"
# Key of the Codex line in content/codex/<lang>/quantique.json.
CODEX_KEY = "tunnel"


def tunnel_barrier(obstacle, pos, vel, params, state):
    """
    Deterministic tunnel crossing. The barrier is taller than any launch
    energy, so the particle never goes *over* it; `energy_threshold` is the
    tunnel threshold: the lowest speed at which it gets *through*. In real
    physics the crossing is a probability that rises with the energy and
    falls fast with the thickness; the game turns it into a sharp rule
    (ADR-0008, physics-pedagogy skill). Below the threshold it bounces like
    a classical wall.
    """
    if vec.mag(vel) >= obstacle.get("energy_threshold", 0.6):
        return vel, "pass"
    return _bounce(obstacle, pos, vel)


# Default handler of the concept's obstacles, and the obstacle types it owns.
DEFAULT_HANDLER = tunnel_barrier
HANDLERS = {"barrier": tunnel_barrier}


def _level_1():
    # Intro: a single barrier, a window in a wall (same vocabulary as
    # difficulties 2-3). Its threshold oscillates slowly and its peak (1.05)
    # exceeds max power: you need enough speed AND to arrive during a trough.
    # Immediate visual feedback: you pass or you bounce.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.86, "y": 0.5, "r": 0.05},
        "obstacles": [
            barrier("barrier", 0.5, 0.4, 0.5, 0.6, base=0.6, amplitude=0.45, period=1.0, phase=0.0),
        ] + door_wall("w", 0.5, 0.4, 0.6),
        "must_contact": [["barrier", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.3, "max": 0.95, "step": 0.05},
        },
    }


def _level_2():
    # Resonance: two barriers in series with oscillating thresholds (at the
    # peak even max power does not pass). The power sets both the speed AND
    # the two arrival instants: find a speed that hits a threshold trough at
    # both barriers.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.88, "y": 0.5, "r": 0.05},
        "obstacles": [
            barrier("b1", 0.38, 0.4, 0.38, 0.6, base=0.6, amplitude=0.4, period=0.8, phase=0.0),
            barrier("b2", 0.66, 0.4, 0.66, 0.6, base=0.6, amplitude=0.4, period=0.8, phase=2.2),
        ] + door_wall("w1", 0.38, 0.4, 0.6) + door_wall("w2", 0.66, 0.4, 0.6),
        "must_contact": [["b1", "pass"], ["b2", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.3, "max": 0.95, "step": 0.05},
        },
    }


def _level_3():
    # Barrier, mirror, barrier: cross b1, get sent up by the mirror, cross b2
    # (offset oscillating thresholds). The longer path between the two
    # barriers makes the resonance tighter. The threshold peak (0.98) exceeds
    # max power (0.95): brute force never works, you must hit a trough.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.6, "y": 0.16, "r": 0.04},
        "obstacles": [
            barrier("b1", 0.34, 0.71, 0.34, 0.89, base=0.6, amplitude=0.38, period=0.9, phase=1.5),
            seg("m", "mirror", 0.53, 0.87, 0.67, 0.73),
            barrier("b2", 0.51, 0.45, 0.69, 0.45, base=0.6, amplitude=0.38, period=0.9, phase=3.0),
            seg("ceilL", "wall", 0.34, 0.45, 0.51, 0.45),
            seg("ceilR", "wall", 0.69, 0.45, 1.05, 0.45),
        ] + door_wall("w1", 0.34, 0.71, 0.89),
        "must_contact": [["b1", "pass"], ["m", "bounce"], ["b2", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.3, "max": 0.95, "step": 0.05},
        },
    }


def build(difficulty: int) -> dict:
    """Level template (layout, `must_contact`, `param_space`) before Photon placement."""
    return {1: _level_1, 2: _level_2, 3: _level_3}[difficulty]()


def param_space(difficulty: int) -> dict:
    """Public setting ranges of the level's dials (shipped in the level file)."""
    return build(difficulty)["param_space"]
