"""
Obstacle shapes. By default an obstacle is a disc (x, y, r). With `length`
it is a flat segment (mirror, wall, surface) centred on (x, y), oriented by
`angle_deg`, 2*r thick: bounces on it follow "angle of incidence = angle of
reflection", which the player can predict, whereas a bounce on a disc
strongly amplifies the smallest aiming error.
"""
import math
from functools import lru_cache

from . import vec

SEGMENT_HALF_THICKNESS = 0.012


def radius(obs):
    return obs.get("r", SEGMENT_HALF_THICKNESS if "length" in obs else 0.03)


@lru_cache(maxsize=4096)
def _endpoints(x, y, length, angle_deg):
    half = length / 2
    a = math.radians(angle_deg)
    d = (math.cos(a) * half, math.sin(a) * half)
    return (x - d[0], y - d[1]), (x + d[0], y + d[1])


def endpoints(obs):
    return _endpoints(obs["x"], obs["y"], obs["length"], obs.get("angle_deg", 0.0))


def touching(obs, pos, margin):
    """True if pos is closer than radius(obs) + margin to the obstacle. Fast
    rejection by the bounding circle before the exact test (called at every
    simulation step for every obstacle)."""
    reach = radius(obs) + margin
    dx, dy = pos[0] - obs["x"], pos[1] - obs["y"]
    bound = reach + obs.get("length", 0.0) / 2
    if dx * dx + dy * dy > bound * bound:
        return False
    return distance(obs, pos) < reach


def closest_point(obs, pos):
    if "length" not in obs:
        return (obs["x"], obs["y"])
    a, b = endpoints(obs)
    ab = vec.sub(b, a)
    t = ((pos[0] - a[0]) * ab[0] + (pos[1] - a[1]) * ab[1]) / (ab[0] ** 2 + ab[1] ** 2)
    t = max(0.0, min(1.0, t))
    return vec.add(a, vec.scale(ab, t))


def distance(obs, pos):
    """Distance from the point to the obstacle's "skeleton" (a disc's centre,
    or the segment) — compare it with radius(obs)."""
    return vec.dist(pos, closest_point(obs, pos))


def normal(obs, pos):
    """Contact normal, pointing from the obstacle towards the particle."""
    return vec.sub(pos, closest_point(obs, pos))
