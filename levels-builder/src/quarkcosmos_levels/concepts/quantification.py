"""
Concept `quantification` — Energy quantisation, "rung-lock" (ADR-0008). Plugin
of the concept registry (concepts/__init__.py): the default handler, the
obstacle types it owns, and the level template of each difficulty
(1 discover → 2 sequence → 3 chain, see the gameplay-mechanics skill).

The launcher only has a few energy rungs (`rungs`: E1…E4, the `rung` launch
parameter), never anything in between. A `lock` accepts ONE exact rung: too
little and too much energy both bounce off (a lock, not a threshold). The
in-flight tap makes Quarky jump DOWN one rung, like an atom giving out light
of one exact colour (event ("quarky", "emit")). Photons are colour-matched:
each belongs to a rung and is only collected by a Quarky on that rung
(core/simulate.py, solver/stars.py).
"""
from .common import door_wall, seg
from .handlers import _bounce, wall_reflect

CONCEPT = "quantification"
# Key of the Codex line in content/codex/<lang>/quantique.json.
CODEX_KEY = "quantification"

# Energy (speed) of the rungs E1…E4. Evenly spaced and far enough apart that
# the difference shows in the flight (a real atom's levels are not evenly
# spaced — the "In real physics…" note of the physics-pedagogy skill says so).
RUNGS = [0.35, 0.5, 0.65, 0.8]
RUNG_CHOICE = {"type": "choice", "values": [0, 1, 2, 3]}


def rung_lock(obstacle, pos, vel, params, state):
    """
    Lock tuned to one energy rung (`rung`, index into the level's `rungs`):
    Quarky passes only on exactly that rung; below AND above, it bounces.
    """
    if state.get("rung") == obstacle["rung"]:
        return vel, "pass"
    return _bounce(obstacle, pos, vel)


# Default handler of the concept's obstacles, and the obstacle types it owns.
DEFAULT_HANDLER = wall_reflect
HANDLERS = {"lock": rung_lock}


def _lock(id_, x1, y1, x2, y2, rung):
    return seg(id_, "lock", x1, y1, x2, y2, rung=rung)


def _level_1():
    # Discover (beta level): a single lock tuned to E3 in a wall window. Only
    # the E3 rung gets through — E2 and E4 bounce alike. The portal drifts
    # slowly (oscillating element), and each rung has its own flight time:
    # the aim has to meet the portal where it will be.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.86, "y": 0.5, "r": 0.05, "motion": {"axis": "y", "amplitude": 0.12, "period": 2.4}},
        "rungs": RUNGS,
        "obstacles": [_lock("lock", 0.45, 0.4, 0.45, 0.6, rung=2)] + door_wall("w", 0.45, 0.4, 0.6),
        "must_contact": [["lock", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "rung": RUNG_CHOICE,
        },
    }


def _level_2():
    # Sequence: two locks, E4 then E3. Launch on E4, then tap BETWEEN the
    # locks to jump down one rung — too early and the first lock bounces
    # you, too late and the second one does.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.88, "y": 0.5, "r": 0.05},
        "rungs": RUNGS,
        "obstacles": [
            _lock("l1", 0.36, 0.4, 0.36, 0.6, rung=3),
            _lock("l2", 0.64, 0.4, 0.64, 0.6, rung=2),
        ] + door_wall("w1", 0.36, 0.4, 0.6) + door_wall("w2", 0.64, 0.4, 0.6),
        "must_contact": [["l1", "pass"], ["quarky", "emit"], ["l2", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "rung": RUNG_CHOICE,
            "tap_time": {"type": "range", "min": 0.3, "max": 0.8, "step": 0.05},
        },
    }


def _level_3():
    # Chain: three locks E4 → E3 → E2 around a mirror, two jumps down (one
    # tap per gap). You can't "dose" energy: you choose rungs, and when to
    # leave them.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.6, "y": 0.16, "r": 0.07},
        "rungs": RUNGS,
        "obstacles": [
            _lock("l1", 0.3, 0.71, 0.3, 0.89, rung=3),
            _lock("l2", 0.44, 0.71, 0.44, 0.89, rung=2),
            seg("m", "mirror", 0.53, 0.87, 0.67, 0.73),
            _lock("l3", 0.51, 0.45, 0.69, 0.45, rung=1),
            seg("ceilL", "wall", 0.44, 0.45, 0.51, 0.45),
            seg("ceilR", "wall", 0.69, 0.45, 1.05, 0.45),
        ] + door_wall("w1", 0.3, 0.71, 0.89) + door_wall("w2", 0.44, 0.71, 0.89),
        # the second jump may happen before or after the mirror: both use the mechanic
        "must_contact": [["l1", "pass"], ["quarky", "emit"], ["l2", "pass"], ["quarky", "emit"], ["l3", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "rung": RUNG_CHOICE,
            "tap_time": {"type": "range", "min": 0.2, "max": 0.5, "step": 0.05},
            "tap_time_2": {"type": "range", "min": 0.45, "max": 1.2, "step": 0.05},
        },
    }


def build(difficulty: int) -> dict:
    """Level template (layout, `must_contact`, `param_space`) before Photon placement."""
    return {1: _level_1, 2: _level_2, 3: _level_3}[difficulty]()


def param_space(difficulty: int) -> dict:
    """Public setting ranges of the level's dials (shipped in the level file)."""
    return build(difficulty)["param_space"]
