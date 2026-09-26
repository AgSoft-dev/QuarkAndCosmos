"""
Concept `dualite` — Wave–particle duality. Plugin of the concept registry (concepts/__init__.py):
the default handler, the obstacle types it owns, and the level template of each
difficulty (1 discover → 2 sequence → 3 chain, see the gameplay-mechanics skill).
"""
import math

from ..core import shapes, vec
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


def slit(obstacle, pos, vel, params, state):
    """
    A grating (a flat segment) with one slit NARROWER than Quarky: the
    aperture, `aperture` wide, centred `aperture_at` along the grating from its
    centre (ADR-0008). As a PARTICLE (before the tap) Quarky bounces off the
    grating, slit included. As a WAVE (after the tap) it diffracts through the
    aperture and spreads into a fan: the exit direction is the grating's
    normal, turned by up to `fan_deg` (default 25°) towards the side of the
    aperture it went through — deterministic, so the player can aim at a
    direction of the fan; elsewhere on the grating a wave bounces too. In real
    physics the wave spreads over the whole fan and Quarky would be detected
    at one random spot of it (physics-pedagogy skill).
    """
    a, b = shapes.endpoints(obstacle)
    along = vec.normalize(vec.sub(b, a))
    centre = vec.add((obstacle["x"], obstacle["y"]), vec.scale(along, obstacle.get("aperture_at", 0.0)))
    s = vec.dot(vec.sub(pos, centre), along)
    half = obstacle["aperture"] / 2
    if not state.get("tapped", False) or abs(s) > half:
        return vec.reflect(vel, shapes.normal(obstacle, pos)), "bounce"
    normal = (-along[1], along[0])
    if vec.dot(vel, normal) < 0.0:
        normal = (-normal[0], -normal[1])  # exit on the far side
    u = s / half
    theta = math.radians(u * obstacle.get("fan_deg", 25.0))
    exit_dir = vec.add(vec.scale(normal, math.cos(theta)), vec.scale(along, math.sin(theta)))
    return vec.scale(vec.normalize(exit_dir), vec.mag(vel)), "diffract"


# Default handler of the concept's obstacles, and the obstacle types it owns.
DEFAULT_HANDLER = dualite_surface
HANDLERS = {"surface": dualite_surface, "slit": slit}


def _level_1():
    # Discover (beta level): a grating with one slit NARROWER than Quarky.
    # As a particle, Quarky bounces off it; tap in flight to become a wave and
    # it diffracts through, spreading into a fan. The portal is off-axis: go
    # through the lower part of the slit to leave along the fan towards it.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.86, "y": 0.64, "r": 0.05},
        "obstacles": [
            seg("slit", "slit", 0.4, -0.05, 0.4, 1.05, aperture=0.06),
        ],
        "must_contact": [["slit", "diffract"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -8, "max": 8, "step": 1},
            "power": {"type": "choice", "values": [0.5, 0.7]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 0.7, "step": 0.05},
        },
    }


def _level_2():
    # Two-step sequence: s1 is a 45° surface that sends a PARTICLE upwards;
    # s2 is a slit in the ceiling of the lower chamber that only a WAVE gets
    # through (diffracting into a fan). The tap must land between the two contacts: too early, Quarky
    # crosses s1 as a wave and flies off to the right; too late, it bounces
    # off s2 like a particle.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.45, "y": 0.14, "r": 0.05},
        "obstacles": [
            seg("s1", "surface", 0.38, 0.87, 0.52, 0.73, interference_offset_deg=180),
            # the ceiling is the grating, its slit at x = 0.45
            seg("s2", "slit", -0.05, 0.42, 1.05, 0.42, aperture=0.06, aperture_at=-0.05),
        ],
        "must_contact": [["s1", "bounce"], ["s2", "diffract"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -6, "max": 2, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.6, "step": 0.05},
        },
    }


def _level_3():
    # Chain: two particle bounces (mirrors s1 then s2: right -> up -> right),
    # then a wave diffracting through slit s3 into the right chamber, where the
    # target drifts. The tap must land between s2 and s3, and the power times
    # the arrival against the moving target.
    return {
        "launcher": {"x": 0.1, "y": 0.85},
        "target": {"x": 0.86, "y": 0.45, "r": 0.055,
                   "motion": {"axis": "y", "amplitude": 0.08, "period": 1.6}},
        "obstacles": [
            seg("s1", "surface", 0.25, 0.92, 0.39, 0.78, interference_offset_deg=180),
            seg("s2", "surface", 0.18, 0.59, 0.39, 0.38, interference_offset_deg=180),
            # the right-hand wall is the grating, its slit at y = 0.45
            seg("s3", "slit", 0.65, -0.05, 0.65, 1.05, aperture=0.06, aperture_at=-0.05),
            seg("shelf", "wall", 0.42, 0.66, 0.65, 0.66),
            # lid above s2: in wave mode too early, Quarky crosses s2 upwards
            # and must not reach s3 via the ceiling
            seg("lid", "wall", 0.18, 0.26, 0.5, 0.26),
        ],
        # any route that ends by diffracting through s3 uses the mechanic (a
        # wave crossing s1 early, then bouncing, is a richer route, not a bypass)
        "must_contact": [["s3", "diffract"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -8, "max": 1, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": 0.5, "max": 2.2, "step": 0.05},
        },
    }


def build(difficulty: int) -> dict:
    """Level template (layout, `must_contact`, `param_space`) before Photon placement."""
    return {1: _level_1, 2: _level_2, 3: _level_3}[difficulty]()


def param_space(difficulty: int) -> dict:
    """Public setting ranges of the level's dials (shipped in the level file)."""
    return build(difficulty)["param_space"]
