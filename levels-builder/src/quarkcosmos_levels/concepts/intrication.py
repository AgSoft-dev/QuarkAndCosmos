"""
Concept `intrication` — Quantum entanglement. Plugin of the concept registry (concepts/__init__.py):
the default handler, the obstacle types it owns, and the level template of each
difficulty (1 discover → 2 sequence → 3 chain, see the gameplay-mechanics skill).
"""
from ..core.simulate import TAP_MIN_TIME
from .common import door_wall, seg
from .handlers import _bounce

CONCEPT = "intrication"
# Key of the Codex line in content/codex/<lang>/quantique.json.
CODEX_KEY = "intrication"


def intrication_gate(obstacle, pos, vel, params, state):
    """
    Gate linked to an identical "witness" (see the gameplay-mechanics skill —
    "Action triggered in flight"): the player taps ONCE during the flight
    (instant = params["tap_time"], searched by the solver like any other
    parameter), which flips both objects — witness and gate — at the same
    instant. Before the tap: gate closed (blocks like a wall). After: open
    (lets through).
    """
    if state.get("tapped", False):
        return vel, "pass"
    return _bounce(obstacle, pos, vel)


def intrication_gate_anti(obstacle, pos, vel, params, state):
    """
    Anti-correlated partner of an entangled gate: open BEFORE the tap, closed
    after. The same gesture opens one gate and closes another — two entangled
    objects whose states are always opposite (a popularisation of the
    anti-correlated measurements of an entangled pair). It creates a tap
    window: this gate must be crossed BEFORE tapping.
    """
    if state.get("tapped", False):
        return _bounce(obstacle, pos, vel)
    return vel, "pass"


# Default handler of the concept's obstacles, and the obstacle types it owns.
DEFAULT_HANDLER = intrication_gate
HANDLERS = {"gate": intrication_gate, "gate_anti": intrication_gate_anti}


def _crystal(x=0.16, y=0.3):
    """The NEAR crystal of the entangled pair (never touched: the tap measures
    it). Its far partners are the gates whose `pair` is "crystal"."""
    return {"id": "crystal", "type": "crystal", "x": x, "y": y, "r": 0.03}


def _level_1():
    # Discover (beta level): tapping in flight measures the NEAR crystal; the
    # FAR gate, entangled with it, opens at the same instant (ADR-0008). Tap
    # before reaching the gate — once is all it takes, but only once.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.85, "y": 0.5, "r": 0.05},
        "obstacles": [
            _crystal(),
            seg("gate", "gate", 0.5, 0.42, 0.5, 0.58, pair="crystal"),
        ] + door_wall("w", 0.5, 0.42, 0.58),
        "must_contact": [["crystal", "measure"], ["gate", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "choice", "values": [0.5, 0.7]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.0, "step": 0.05},
        },
    }


def _level_2():
    # ANTI-correlated pair: gate A is open until the tap, gate B is closed
    # until the tap. A single gesture opens one and closes the other: cross
    # A, THEN tap, then cross B.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.88, "y": 0.5, "r": 0.05},
        "obstacles": [
            _crystal(),
            seg("A", "gate_anti", 0.4, 0.42, 0.4, 0.58, pair="crystal"),
            seg("B", "gate", 0.65, 0.42, 0.65, 0.58, pair="crystal"),
        ] + door_wall("wA", 0.4, 0.42, 0.58) + door_wall("wB", 0.65, 0.42, 0.58),
        "must_contact": [["A", "pass"], ["crystal", "measure"], ["B", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.4, "step": 0.05},
        },
    }


def _level_3():
    # Gate M, entangled with B, acts as a MIRROR while closed: cross A (anti:
    # open before the tap), bounce up off M (closed), THEN tap to open B (and
    # M, but we have already left it). Tapping too early: M opens and we go
    # through it; far too early: A closes in front of us. A single window:
    # between the bounce on M and B.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.55, "y": 0.18, "r": 0.05},
        "obstacles": [
            _crystal(0.14, 0.62),
            seg("A", "gate_anti", 0.3, 0.72, 0.3, 0.88, pair="crystal"),
            seg("M", "gate", 0.48, 0.87, 0.62, 0.73, pair="crystal"),
            seg("B", "gate", 0.47, 0.45, 0.63, 0.45, pair="crystal"),
            seg("ceilL", "wall", 0.3, 0.45, 0.47, 0.45),
            seg("ceilR", "wall", 0.63, 0.45, 1.05, 0.45),
        ] + door_wall("wA", 0.3, 0.72, 0.88),
        "must_contact": [["A", "pass"], ["M", "bounce"], ["crystal", "measure"], ["B", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.6, "step": 0.05},
        },
    }


def build(difficulty: int) -> dict:
    """Level template (layout, `must_contact`, `param_space`) before Photon placement."""
    return {1: _level_1, 2: _level_2, 3: _level_3}[difficulty]()


def param_space(difficulty: int) -> dict:
    """Public setting ranges of the level's dials (shipped in the level file)."""
    return build(difficulty)["param_space"]
