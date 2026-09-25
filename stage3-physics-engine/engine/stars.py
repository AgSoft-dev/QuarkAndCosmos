"""
Distribution des étoiles (1-2-3) et placement des Photons par « lancer de
rayons » (cf. skill gameplay-mechanics — notation à 3 étoiles).

1. Lancer de rayons : on tire un éventail dense de lancers sur tout l'espace
   de paramètres (angle, puissance, instant du tap…), plus fin que la grille
   du solveur, et on garde la trajectoire de chaque lancer qui atteint la
   cible : ce sont les rayons valides. Les rayons qui suivent exactement la
   même trajectoire (espace ET temps) forment un même « chemin » : aucun
   Photon ne peut les départager.
2. Gaussienne tronquée : parmi les rayons valides, la part qui rapporte au
   moins k étoiles suit exp(-k² / 2σ²) pour k = 1, 2, 3 (courbe coupée à 3).
   Beaucoup de lancers valides donnent 1 étoile, peu en donnent 3.
3. Difficulté : σ diminue quand la difficulté augmente, donc la fenêtre de
   lancers (chemins / timings) qui rapporte 3 étoiles se resserre.
4. Placement : les 3 Photons sont posés sur le chemin d'une solution de
   référence (celle qui les collecte tous), choisis ensemble pour que la
   distribution mesurée colle à la cible. Plusieurs chemins de référence
   sont essayés : un chemin très fréquent convient aux niveaux faciles, un
   chemin plus rare permet une fenêtre 3 étoiles étroite.
5. Timing : quand les chemins valides se superposent dans l'espace, la
   position seule ne départage rien. Le Photon peut alors osciller (brique
   "élément oscillant" du skill gameplay-mechanics), calé en phase sur la
   solution de référence : seuls les lancers qui passent au bon MOMENT le
   collectent. Un Photon fixe est préféré à écart égal (MOTION_PENALTY).
"""
import copy
import itertools
import math

from . import vec
from .simulate import COLLISION_EPS, DT, TAP_MIN_TIME, _oscillate, simulate

PHOTONS_PER_LEVEL = 3
PHOTON_RADIUS = 0.03
# Marge libre minimale entre un Photon et un obstacle/la cible/le lanceur.
PHOTON_CLEARANCE = 0.02
# Écart minimal (en pas de simulation) entre deux Photons sur la trajectoire.
PHOTON_MIN_GAP_STEPS = 10

# σ de la gaussienne par niveau de difficulté (cf. target_shares). Au-delà
# de la dernière entrée, on garde la plus petite valeur.
SIGMA_BY_DIFFICULTY = {1: 2.2, 2: 1.6, 3: 1.2}

# Finesse du lancer de rayons : chaque paramètre continu est échantillonné
# REFINE fois plus finement que sa grille de solveur, dans la limite de
# MAX_RAYS lancers au total.
REFINE = 3
MAX_RAYS = 6000

# Variantes d'oscillation essayées pour chaque position candidate
# (amplitude, période en secondes simulées), perpendiculairement au trajet.
PHOTON_MOTIONS = ((0.04, 0.5), (0.08, 0.5), (0.04, 0.25), (0.08, 0.25), (0.06, 0.15), (0.12, 0.15))
# Pénalité (en part de rayons) d'un Photon oscillant face à un Photon fixe.
MOTION_PENALTY = 0.03
# Poids de l'écart à la cible par palier (le palier 3 étoiles est celui qui
# porte la difficulté).
TIER_WEIGHTS = (1.0, 1.0, 2.0)
# Nombre de chemins de référence essayés, répartis du plus robuste au moins
# robuste.
ANCHORS = 5
# Recherche du triplet de Photons : pour chaque palier k, on garde les
# SHORTLIST candidats dont la part capturée est la plus proche de la cible
# du palier, puis on évalue exactement tous les triplets formés.
SHORTLIST = 18
# Pas (en pas de simulation) entre deux positions candidates sur le chemin.
CANDIDATE_STRIDE = 3


def sigma_for(difficulty: int) -> float:
    if difficulty in SIGMA_BY_DIFFICULTY:
        return SIGMA_BY_DIFFICULTY[difficulty]
    return min(SIGMA_BY_DIFFICULTY.values())


def target_shares(difficulty: int) -> dict:
    """Part cible des rayons valides rapportant au moins k étoiles."""
    s = sigma_for(difficulty)
    return {k: round(math.exp(-k * k / (2 * s * s)), 4) for k in range(1, PHOTONS_PER_LEVEL + 1)}


# --- lancer de rayons ------------------------------------------------------

def _ray_values(spec, refine):
    if spec["type"] == "choice":
        return list(spec["values"])
    step = spec["step"] / refine
    n = int(round((spec["max"] - spec["min"]) / step))
    return [round(spec["min"] + i * step, 5) for i in range(n + 1)]


def _ray_grid(level):
    space = level["param_space"]
    keys = list(space.keys())
    refine = REFINE
    while True:
        grids = [_ray_values(space[k], refine) for k in keys]
        if "tap_time" in space:
            i = keys.index("tap_time")
            grids[i] = [t for t in grids[i] if t >= TAP_MIN_TIME]
        size = math.prod(len(g) for g in grids)
        if size <= MAX_RAYS or refine == 1:
            return keys, grids
        refine -= 1


class _Path:
    """Trajectoire valide partagée par `weight` rayons (mêmes positions aux
    mêmes instants), avec un index spatial des points visités."""
    CELL = 0.05

    def __init__(self, trail):
        self.trail = trail
        self.rays = []  # paramètres des rayons qui suivent ce chemin
        self.cells = {}
        for i, p in enumerate(trail):
            key = (int(p[0] // self.CELL), int(p[1] // self.CELL))
            self.cells.setdefault(key, []).append(((i + 1) * DT, p))

    @property
    def weight(self):
        return len(self.rays)

    def collects(self, photon):
        """Même règle que simulate() : distance au Photon (à sa position à
        l'instant t s'il oscille) < rayon + COLLISION_EPS."""
        radius = photon.get("r", PHOTON_RADIUS) + COLLISION_EPS
        motion = photon.get("motion")
        reach = radius + (motion["amplitude"] if motion else 0.0)
        span = int(reach // self.CELL) + 1
        cx, cy = int(photon["x"] // self.CELL), int(photon["y"] // self.CELL)
        for dx in range(-span, span + 1):
            for dy in range(-span, span + 1):
                for t, q in self.cells.get((cx + dx, cy + dy), ()):
                    pos = _oscillate(photon["x"], photon["y"], motion, t)
                    if vec.dist(q, pos) < radius:
                        return True
        return False


def trace(level: dict):
    """Tire l'éventail de rayons ; retourne (nb de rayons, chemins valides)."""
    bare = copy.deepcopy(level)
    bare["photons"] = []
    keys, grids = _ray_grid(bare)
    paths = {}
    total = 0
    for combo in itertools.product(*grids):
        total += 1
        params = dict(zip(keys, combo))
        res = simulate(bare, params, record_trail=True)
        if res.success:
            signature = tuple((round(x, 4), round(y, 4)) for x, y in res.trail)
            if signature not in paths:
                paths[signature] = _Path(res.trail)
            paths[signature].rays.append(params)
    return total, list(paths.values())


def _shares(paths, photons):
    """Part des rayons valides ayant au moins k Photons, k = 1..3."""
    n = sum(p.weight for p in paths)
    counts = [0] * (PHOTONS_PER_LEVEL + 1)
    for p in paths:
        got = sum(1 for ph in photons if p.collects(ph))
        for k in range(1, min(got, PHOTONS_PER_LEVEL) + 1):
            counts[k] += p.weight
    return {k: (counts[k] / n if n else 0.0) for k in range(1, PHOTONS_PER_LEVEL + 1)}


def star_profile(level: dict) -> dict:
    """
    Distribution réelle des étoiles d'un niveau, mesurée par lancer de rayons.
    `shares[k]` = part des rayons valides qui rapportent au moins k étoiles.
    """
    total, paths = trace(level)
    shares = _shares(paths, level.get("photons", []))
    return {
        "rays": total,
        "valid_rays": sum(p.weight for p in paths),
        "distinct_paths": len(paths),
        "shares": {str(k): round(v, 4) for k, v in shares.items()},
        "target_shares": {str(k): v for k, v in target_shares(level.get("difficulty", 1)).items()},
    }


# --- placement des Photons -------------------------------------------------

def _anchors(paths, keys_values):
    """ANCHORS chemins de référence, du plus robuste (le plus de rayons
    valides voisins, à un cran près sur chaque paramètre) au moins robuste."""
    keys, grids = keys_values
    index = [{v: i for i, v in enumerate(g)} for g in grids]
    occupied = set()
    for p in paths:
        for params in p.rays:
            occupied.add(tuple(index[k][params[key]] for k, key in enumerate(keys)))

    def robustness(path):
        best = 0
        for params in path.rays:
            pt = tuple(index[k][params[key]] for k, key in enumerate(keys))
            n = sum(1 for d in itertools.product((-1, 0, 1), repeat=len(pt))
                    if tuple(a + b for a, b in zip(pt, d)) in occupied)
            best = max(best, n)
        return best

    ranked = sorted(paths, key=lambda p: (-robustness(p), -p.weight))
    if len(ranked) <= ANCHORS:
        return ranked
    picks = sorted({round(i * (len(ranked) - 1) / (ANCHORS - 1)) for i in range(ANCHORS)})
    return [ranked[i] for i in picks]


def _clear_of_objects(level, pos, t):
    r = PHOTON_RADIUS
    for obs in level.get("obstacles", []):
        ox, oy = _oscillate(obs["x"], obs["y"], obs.get("motion"), t)
        if vec.dist(pos, (ox, oy)) < obs.get("r", 0.03) + r + PHOTON_CLEARANCE:
            return False
    tgt = level["target"]
    if vec.dist(pos, (tgt["x"], tgt["y"])) < tgt.get("r", 0.045) + r + PHOTON_CLEARANCE:
        return False
    lau = level["launcher"]
    return vec.dist(pos, (lau["x"], lau["y"])) >= 0.05 + r


def _candidates(level, trail):
    """Positions libres sur le chemin de référence, fixes ou oscillantes
    (oscillation perpendiculaire au trajet, en phase nulle à l'instant où la
    référence passe : elle collecte donc toujours ce Photon)."""
    out = []
    for i in range(0, len(trail), CANDIDATE_STRIDE):
        t = (i + 1) * DT
        if not _clear_of_objects(level, trail[i], t):
            continue
        base = {"x": round(trail[i][0], 3), "y": round(trail[i][1], 3), "r": PHOTON_RADIUS}
        out.append((i, base))
        step = vec.sub(trail[min(i + 1, len(trail) - 1)], trail[max(i - 1, 0)])
        axis = "y" if abs(step[0]) >= abs(step[1]) else "x"
        for amplitude, period in PHOTON_MOTIONS:
            phase = round((-2 * math.pi * t / period) % (2 * math.pi), 4)
            out.append((i, dict(base, motion={"axis": axis, "amplitude": amplitude,
                                              "period": period, "phase": phase})))
    return out


def _best_trio(paths, candidates, targets):
    """Meilleur triplet de candidats et son coût. Captures en masques de bits
    sur les rayons (chaque chemin occupe un bloc de `weight` bits) :
    >=1 étoile = union, >=2 = union des intersections deux à deux,
    3 = intersection. Idéalement les trois ensembles sont emboîtés."""
    blocks, offset = [], 0
    for p in paths:
        blocks.append(((1 << p.weight) - 1) << offset)
        offset += p.weight
    n = offset
    masks = []
    for _, ph in candidates:
        m = 0
        for p, block in zip(paths, blocks):
            if p.collects(ph):
                m |= block
        masks.append(m)
    fractions = [bin(m).count("1") / n for m in masks]
    shortlists = [
        sorted(range(len(candidates)), key=lambda c: abs(fractions[c] - targets[k]))[:SHORTLIST]
        for k in range(1, PHOTONS_PER_LEVEL + 1)
    ]

    best, best_cost = None, None
    for trio in itertools.product(*shortlists):
        steps = sorted(candidates[i][0] for i in trio)
        if len(set(trio)) < 3 or any(b - a < PHOTON_MIN_GAP_STEPS for a, b in zip(steps, steps[1:])):
            continue
        ma, mb, mc = (masks[i] for i in trio)
        got = (bin(ma | mb | mc).count("1") / n,
               bin((ma & mb) | (ma & mc) | (mb & mc)).count("1") / n,
               bin(ma & mb & mc).count("1") / n)
        moving = sum("motion" in candidates[i][1] for i in trio)
        cost = (sum(w * abs(g - targets[k]) for w, k, g in zip(TIER_WEIGHTS, (1, 2, 3), got))
                + MOTION_PENALTY * moving)
        if best_cost is None or cost < best_cost:
            best, best_cost = trio, cost
    return best, best_cost


def place_photons(level: dict) -> dict:
    """
    Retourne une copie du niveau avec 3 Photons posés sur le chemin d'une
    solution de référence, choisis ensemble pour que la part des rayons
    valides à >= k étoiles colle à target_shares(difficulté).
    Lève ValueError si le niveau n'est pas solvable.
    """
    bare = copy.deepcopy(level)
    bare["photons"] = []
    _, paths = trace(bare)
    if not paths:
        raise ValueError(f"Niveau non solvable, impossible de placer les Photons: {level.get('id')}")
    targets = target_shares(level.get("difficulty", 1))

    best, best_cost = None, None
    for anchor in _anchors(paths, _ray_grid(bare)):
        candidates = _candidates(bare, anchor.trail)
        trio, cost = _best_trio(paths, candidates, targets)
        if trio is not None and (best_cost is None or cost < best_cost):
            best, best_cost = [candidates[i] for i in trio], cost
    if best is None:
        raise ValueError(f"Aucun triplet de Photons assez espacés: {level.get('id')}")

    # numérotation dans l'ordre de passage le long de la trajectoire
    best.sort(key=lambda c: c[0])
    placed = copy.deepcopy(level)
    placed["photons"] = [dict(id=f"p{n}", **ph) for n, (_, ph) in enumerate(best, start=1)]
    return placed
