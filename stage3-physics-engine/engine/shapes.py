"""
Formes d'obstacles. Par défaut un obstacle est un disque (x, y, r). Avec
`length`, c'est un segment plat (miroir, paroi, surface) de centre (x, y),
orienté selon `angle_deg`, d'épaisseur 2*r : le rebond y suit « angle
d'incidence = angle de réflexion », prévisible pour le joueur, là où un
rebond sur un disque amplifie fortement la moindre erreur de visée.
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
    """Vrai si pos est à moins de radius(obs) + margin de l'obstacle. Rejet
    rapide par le cercle englobant avant le calcul exact (appelé à chaque pas
    de simulation pour chaque obstacle)."""
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
    """Distance du point au bord « squelette » de l'obstacle (centre d'un
    disque, ou segment) — à comparer à radius(obs)."""
    return vec.dist(pos, closest_point(obs, pos))


def normal(obs, pos):
    """Normale de contact, orientée de l'obstacle vers la particule."""
    return vec.sub(pos, closest_point(obs, pos))
