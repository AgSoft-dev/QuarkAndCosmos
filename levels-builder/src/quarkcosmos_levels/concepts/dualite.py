"""
Concept `dualite` — Wave–particle duality. Plugin of the concept registry (concepts/__init__.py):
the default handler, the obstacle types it owns, and the level template of each
difficulty (1 discover → 2 sequence → 3 chain, see the gameplay-mechanics skill).
"""
from ..core import vec
from ..core.simulate import TAP_MIN_TIME
from .common import seg
from .handlers import _bounce

CONCEPT = "dualite"
# Key of the Codex line in content/codex/<lang>/quantique.json.
CODEX_KEY = "dualite"


def dualite_surface(obstacle, pos, vel, params, state):
    """
    Wave/particle toggle IN FLIGHT (see gameplay-mechanics — "Action
    triggered in flight"): Quarky starts in particle mode (classical bounce),
    and a tap during the flight (params["tap_time"]) switches it to wave mode
    for the rest of the path (bounce + interference offset, which foreshadows
    without duplicating the real reflection lesson taught at the Macro scale,
    see the storytelling skill).
    """
    vel2, _ = _bounce(obstacle, pos, vel)
    if state.get("tapped", False):
        offset = obstacle.get("interference_offset_deg", 15)
        if offset % 360 == 180:
            # 180° = pure transmission: the wave crosses the surface without
            # changing direction, whatever the incidence (otherwise, on a
            # tilted surface, "bounce + 180°" sends back a mirror image of the
            # direction, unreadable for the player).
            return vel, "wave"
        ang = vec.angle_of(vel2) + offset
        return vec.from_angle(ang, vec.mag(vel2)), "wave"
    return vel2, "bounce"


# Default handler of the concept's obstacles, and the obstacle types it owns.
DEFAULT_HANDLER = dualite_surface
HANDLERS = {"surface": dualite_surface}


def _level_1():
    # An in-flight action (see gameplay-mechanics) replaces the pre-launch
    # setting: Quarky starts in particle mode, a tap during the flight
    # (tap_time) switches to wave mode for the rest of the path.
    return {
        "launcher": {"x": 0.08, "y": 0.3},
        "target": {"x": 0.85, "y": 0.3, "r": 0.05},
        "obstacles": [
            {"id": "surface", "type": "surface", "x": 0.35, "y": 0.3, "r": 0.05,
             "interference_offset_deg": 180},
        ],
        "must_contact": [["surface", "wave"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -3, "max": 3, "step": 1},
            "power": {"type": "choice", "values": [0.5, 0.7]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 0.7, "step": 0.05},
        },
    }


def _level_2():
    # Two-step sequence, flat surfaces (angle of incidence = angle of
    # reflection): s1 is a 45° mirror that sends a PARTICLE upwards; s2 is a
    # window in the ceiling of the lower chamber that can only be crossed as
    # a WAVE. The tap must land between the two contacts: too early, Quarky
    # crosses s1 as a wave and flies off to the right; too late, it bounces
    # off s2 like a particle.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.45, "y": 0.14, "r": 0.05},
        "obstacles": [
            seg("s1", "surface", 0.38, 0.87, 0.52, 0.73, interference_offset_deg=180),
            seg("s2", "surface", 0.35, 0.42, 0.55, 0.42, interference_offset_deg=180),
            seg("ceilL", "wall", -0.05, 0.42, 0.35, 0.42),
            seg("ceilR", "wall", 0.55, 0.42, 1.05, 0.42),
        ],
        "must_contact": [["s1", "bounce"], ["s2", "wave"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -15, "max": 15, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.6, "step": 0.05},
        },
    }


def _level_3():
    # Chain: two particle bounces (mirrors s1 then s2: right -> up -> right),
    # then a wave crossing of window s3 into the right chamber, where the
    # target drifts. The tap must land between s2 and s3, and the power times
    # the arrival against the moving target.
    return {
        "launcher": {"x": 0.1, "y": 0.85},
        "target": {"x": 0.86, "y": 0.45, "r": 0.05,
                   "motion": {"axis": "y", "amplitude": 0.08, "period": 1.6}},
        "obstacles": [
            seg("s1", "surface", 0.25, 0.92, 0.39, 0.78, interference_offset_deg=180),
            seg("s2", "surface", 0.18, 0.59, 0.39, 0.38, interference_offset_deg=180),
            seg("s3", "surface", 0.65, 0.33, 0.65, 0.57, interference_offset_deg=180),
            seg("wallTop", "wall", 0.65, -0.05, 0.65, 0.33),
            seg("wallBot", "wall", 0.65, 0.57, 0.65, 1.05),
            seg("shelf", "wall", 0.42, 0.66, 0.65, 0.66),
            # lid above s2: in wave mode too early, Quarky crosses s2 upwards
            # and must not reach s3 via the ceiling
            seg("lid", "wall", 0.18, 0.26, 0.5, 0.26),
        ],
        "must_contact": [["s1", "bounce"], ["s2", "bounce"], ["s3", "wave"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -15, "max": 15, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 2.2, "step": 0.05},
        },
    }


def build(difficulty: int) -> dict:
    """Level template (layout, `must_contact`, `param_space`) before Photon placement."""
    return {1: _level_1, 2: _level_2, 3: _level_3}[difficulty]()


def param_space(difficulty: int) -> dict:
    """Public setting ranges of the level's dials (shipped in the level file)."""
    return build(difficulty)["param_space"]
