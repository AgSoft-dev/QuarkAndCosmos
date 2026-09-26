"""Minimal 2D vectors (tuples), no external dependency."""
import math

Vec2 = tuple


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def scale(a, s):
    return (a[0] * s, a[1] * s)


def mag(a):
    return math.hypot(a[0], a[1])


def normalize(a):
    m = mag(a)
    if m < 1e-9:
        return (0.0, 0.0)
    return (a[0] / m, a[1] / m)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def angle_of(v):
    return math.degrees(math.atan2(v[1], v[0]))


def from_angle(deg, magnitude=1.0):
    rad = math.radians(deg)
    return (math.cos(rad) * magnitude, math.sin(rad) * magnitude)


def ang_diff(a, b):
    """Smallest signed angular difference between two angles in degrees, in [-180, 180]."""
    d = (a - b + 180) % 360 - 180
    return d


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def reflect(v, normal):
    """Reflect a velocity about a normal pointing towards the particle, only
    if the particle is approaching (v·n < 0). Moving away (or a zero normal)
    leaves the velocity unchanged: a contact detected while already leaving
    must never send the particle back into the obstacle."""
    n = normalize(normal)
    d = v[0] * n[0] + v[1] * n[1]
    if d >= 0.0:
        return v
    return (v[0] - 2 * d * n[0], v[1] - 2 * d * n[1])
