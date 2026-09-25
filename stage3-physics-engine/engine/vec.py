"""Vecteurs 2D minimalistes (tuples), sans dépendance externe."""
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
    """Plus petite différence angulaire signée entre deux angles en degrés, dans [-180, 180]."""
    d = (a - b + 180) % 360 - 180
    return d


def reflect(v, normal):
    """Réflexion d'un vecteur vitesse par rapport à une normale unitaire."""
    n = normalize(normal)
    d = v[0] * n[0] + v[1] * n[1]
    return (v[0] - 2 * d * n[0], v[1] - 2 * d * n[1])
