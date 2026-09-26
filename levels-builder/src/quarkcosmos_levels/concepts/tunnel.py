"""
Concept `tunnel` — Tunnel effect. Plugin of the concept registry (concepts/__init__.py):
the default handler, the obstacle types it owns, and the level template of each
difficulty (1 discover → 2 sequence → 3 chain, see the gameplay-mechanics skill).
"""
from ..core import vec
from .common import door_wall, seg
from .handlers import _bounce

CONCEPT = "tunnel"
# Key of the Codex line in content/codex/<lang>/quantique.json.
CODEX_KEY = "tunnel"


# Tunnel model (ADR-0008 follow-up, physics-pedagogy skill). Every barrier is
# taller than any launch energy (height V > max power), so Quarky never goes
# *over* it. Real transmission falls like exp(-2κd) with κ ∝ √(V − E): it drops
# fast with the thickness d and rises as the energy E nears V. The game makes
# it a sharp rule at a fixed transmission, √(V − E)·d ≤ K, i.e. Quarky gets
# through when its energy reaches the tunnel threshold E_t(d) = V − (K/d)².
# With V = 1.2 and K = 0.019: d = 0.02 → 0.30, 0.03 → 0.80, 0.04 → 0.97 (above
# max power: never crossed), so the thickness reads directly as difficulty.
TUNNEL_HEIGHT = 1.2
TUNNEL_K = 0.019


def tunnel_threshold(thickness, height=TUNNEL_HEIGHT):
    """Lowest energy (speed) that tunnels through a barrier of this thickness."""
    q = TUNNEL_K / thickness
    return height - q * q  # q * q, not ** 2: bit-identical in the Kotlin port


def tunnel_barrier(obstacle, pos, vel, params, state):
    """
    Deterministic tunnel crossing through a barrier of visible thickness
    (`thickness`, possibly breathing with `thickness_motion`): passes *through*
    if the speed reaches E_t(thickness), otherwise bounces like a classical
    wall. In real physics the crossing is a probability that falls fast with
    the thickness; the game turns it into a sharp rule (ADR-0008).
    """
    threshold = tunnel_threshold(obstacle["thickness"], obstacle.get("height", TUNNEL_HEIGHT))
    if vec.mag(vel) >= threshold:
        return vel, "pass"
    return _bounce(obstacle, pos, vel)


# Default handler of the concept's obstacles, and the obstacle types it owns.
DEFAULT_HANDLER = tunnel_barrier
HANDLERS = {"barrier": tunnel_barrier}


def _barrier(id_, x1, y1, x2, y2, thickness, amplitude=0.0, period=1.0, phase=0.0):
    """Flat tunnel barrier of visible thickness, optionally breathing."""
    extra = {"thickness": thickness}
    if amplitude:
        extra["thickness_motion"] = {"amplitude": amplitude, "period": period, "phase": phase}
    return seg(id_, "barrier", x1, y1, x2, y2, **extra)


def _level_1():
    # Discover (beta level): one window in a wall, split between a THICK
    # barrier (top, never crossed) and a THIN one (bottom) that breathes
    # slowly. Aim at the thin one and arrive while it is thin enough for your
    # energy: the thickness reads directly as "can I get through?".
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.86, "y": 0.6, "r": 0.05},
        "obstacles": [
            _barrier("thick", 0.5, 0.38, 0.5, 0.5, thickness=0.05),
            _barrier("thin", 0.5, 0.5, 0.5, 0.62, thickness=0.03, amplitude=0.012, period=1.0),
        ] + door_wall("w", 0.5, 0.38, 0.62),
        "must_contact": [["thin", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.3, "max": 0.95, "step": 0.05},
        },
    }


def _level_2():
    # Resonance: two breathing barriers in series (at their thickest even max
    # power does not get through). The power sets both the speed AND
    # the two arrival instants: find a speed that hits a threshold trough at
    # both barriers.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.88, "y": 0.5, "r": 0.05},
        "obstacles": [
            _barrier("b1", 0.38, 0.4, 0.38, 0.6, thickness=0.028, amplitude=0.013, period=0.8, phase=0.0),
            _barrier("b2", 0.66, 0.4, 0.66, 0.6, thickness=0.028, amplitude=0.013, period=0.8, phase=2.2),
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
    # (offset breathing). The longer path between the two barriers makes the
    # resonance tighter. At their thickest the barriers exceed max power:
    # brute force never works, you must arrive while they are thin.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.6, "y": 0.16, "r": 0.04},
        "obstacles": [
            _barrier("b1", 0.34, 0.71, 0.34, 0.89, thickness=0.03, amplitude=0.011, period=0.9, phase=1.5),
            seg("m", "mirror", 0.53, 0.87, 0.67, 0.73),
            _barrier("b2", 0.51, 0.45, 0.69, 0.45, thickness=0.03, amplitude=0.011, period=0.9, phase=3.0),
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
