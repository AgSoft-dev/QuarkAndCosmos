"""
Star distribution (1-2-3) and Photon placement by "ray tracing" (see the
gameplay-mechanics skill — 3-star scoring).

1. Ray tracing: fire a dense fan of launches over the whole parameter space
   (angle, power, tap instant…), finer than the solver grid, and keep the
   trajectory of every launch that reaches the target: these are the valid
   rays. Rays following exactly the same trajectory (space AND time) form a
   single "path": no Photon can tell them apart.
2. Truncated gaussian: among valid rays, the share earning at least k stars
   follows exp(-k² / 2σ²) for k = 1, 2, 3 (curve cut at 3). Many valid
   launches earn 1 star, few earn 3.
3. Difficulty: σ shrinks as difficulty grows, so the window of launches
   (paths / timings) earning 3 stars gets narrower.
4. Placement: the 3 Photons are placed on the path of a reference solution
   (the one that collects them all), chosen together so that the measured
   distribution matches the target. Several reference paths are tried: a
   very common path suits easy levels, a rarer path allows a narrow 3-star
   window.
5. Timing: when valid paths overlap in space, position alone separates
   nothing. The Photon can then oscillate ("oscillating element" building
   block of the gameplay-mechanics skill), phase-locked to the reference
   solution: only launches passing at the right MOMENT collect it. A fixed
   Photon is preferred at equal error (MOTION_PENALTY).
"""
import copy
import itertools
import json
import math

from ..core import shapes, vec
from ..core.simulate import (COLLISION_EPS, DT, TAP_MIN_TIME, _oscillate, launch_speed_max, simulate_cone, taps_ordered)

PHOTONS_PER_LEVEL = 3
PHOTON_RADIUS = 0.03
# Minimum free margin between a Photon and an obstacle/the target/the launcher.
PHOTON_CLEARANCE = 0.02
# Minimum gap (in simulation steps) between two Photons along the trajectory.
PHOTON_MIN_GAP_STEPS = 10

# Gaussian σ per difficulty level (see target_shares). Beyond the last
# entry, the smallest value is kept.
SIGMA_BY_DIFFICULTY = {1: 2.2, 2: 1.6, 3: 1.2}

# Ray-tracing resolution: each continuous parameter is sampled REFINE times
# finer than its solver grid, within MAX_RAYS launches in total.
REFINE = 3
MAX_RAYS = 4000

# Oscillation variants tried for each candidate position (amplitude, period
# in simulated seconds), perpendicular to the path.
PHOTON_MOTIONS = ((0.04, 0.5), (0.08, 0.5), (0.04, 0.25), (0.08, 0.25), (0.06, 0.15), (0.12, 0.15))
# Penalty (as a share of rays) of an oscillating Photon versus a fixed one.
MOTION_PENALTY = 0.03
# Weight of the error to target per tier (the 3-star tier is the one that
# carries the difficulty).
TIER_WEIGHTS = (1.0, 1.0, 2.0)
# Number of reference paths tried, spread from most to least robust, plus
# the most robust path of each of the ROUTE_ANCHORS most frequent routes: a
# rare route that uses the mechanic more (e.g. ping-pong between entangled
# gates) is the natural candidate for the 3rd star.
ANCHORS = 5
ROUTE_ANCHORS = 4
# Photon triplet search: for each tier k, keep the SHORTLIST candidates
# whose captured share is closest to the tier's target, then evaluate every
# triplet they form exactly.
SHORTLIST = 18
SHORTLIST_PER_STEP = 2
# Step (in simulation steps) between two candidate positions on the path.
CANDIDATE_STRIDE = 3


def sigma_for(difficulty: int) -> float:
    if difficulty in SIGMA_BY_DIFFICULTY:
        return SIGMA_BY_DIFFICULTY[difficulty]
    return min(SIGMA_BY_DIFFICULTY.values())


def target_shares(difficulty: int) -> dict:
    """Target share of valid rays earning at least k stars."""
    s = sigma_for(difficulty)
    return {k: round(math.exp(-k * k / (2 * s * s)), 4) for k in range(1, PHOTONS_PER_LEVEL + 1)}


# --- ray tracing -----------------------------------------------------------

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
        for i, key in enumerate(keys):
            if key.startswith("tap_time"):
                grids[i] = [t for t in grids[i] if t >= TAP_MIN_TIME]
        size = math.prod(len(g) for g in grids)
        if size <= MAX_RAYS or refine == 1:
            return keys, grids
        refine -= 1


class _Path:
    """Valid trajectory shared by `weight` rays (same positions at the same
    instants), with a spatial index of the visited points."""
    CELL = 0.05

    def __init__(self, trail, route=(), rungs=()):
        self.trail = trail
        # energy rung at each step (quantisation levels): colour-matched
        # Photons are only collected on their own rung
        self.rungs = list(rungs)
        # (obstacle, event) sequence: two paths on the same route use the
        # mechanic the same way (see SimResult.contacts)
        self.route = tuple(route)
        self.rays = []  # parameters of the rays following this path
        self.cells = {}
        for i, p in enumerate(trail):
            key = (int(p[0] // self.CELL), int(p[1] // self.CELL))
            self.cells.setdefault(key, []).append(((i + 1) * DT, p, self.rungs[i] if self.rungs else -1))

    @property
    def weight(self):
        return len(self.rays)

    def collects(self, photon):
        """Same rule as simulate(): distance to the Photon (at its position
        at time t if it oscillates) < radius + COLLISION_EPS."""
        radius = photon.get("r", PHOTON_RADIUS) + COLLISION_EPS
        motion = photon.get("motion")
        reach = radius + (motion["amplitude"] if motion else 0.0)
        span = int(reach // self.CELL) + 1
        cx, cy = int(photon["x"] // self.CELL), int(photon["y"] // self.CELL)
        for dx in range(-span, span + 1):
            for dy in range(-span, span + 1):
                for t, q, rung in self.cells.get((cx + dx, cy + dy), ()):
                    if "rung" in photon and photon["rung"] != rung:
                        continue
                    pos = _oscillate(photon["x"], photon["y"], motion, t)
                    if vec.dist(q, pos) < radius:
                        return True
        return False


# Photons don't change trajectories: a level's ray tracing depends only on
# its geometry, so it is memoised (placement, report and validation ask for
# it again for the same level).
_TRACE_CACHE = {}


def trace(level: dict):
    """Fire the fan of rays; return (number of rays, valid paths)."""
    bare = copy.deepcopy(level)
    bare["photons"] = []
    key = json.dumps(bare, sort_keys=True, default=str)
    if key not in _TRACE_CACHE:
        _TRACE_CACHE[key] = _trace(bare)
    return _TRACE_CACHE[key]


def _trace(bare):
    keys, grids = _ray_grid(bare)
    paths = {}
    total = 0
    for combo in itertools.product(*grids):
        params = dict(zip(keys, combo))
        if not taps_ordered(params):
            continue
        total += 1
        res = simulate_cone(bare, params, record_trail=True)
        if res.success:
            signature = tuple((round(x, 4), round(y, 4)) for x, y in res.trail)
            if signature not in paths:
                paths[signature] = _Path(res.trail, res.contacts, res.rung_trail)
            paths[signature].rays.append(params)
    return total, list(paths.values())


def _shares(paths, photons):
    """Share of valid rays with at least k Photons, k = 1..3."""
    n = sum(p.weight for p in paths)
    counts = [0] * (PHOTONS_PER_LEVEL + 1)
    for p in paths:
        got = sum(1 for ph in photons if p.collects(ph))
        for k in range(1, min(got, PHOTONS_PER_LEVEL) + 1):
            counts[k] += p.weight
    return {k: (counts[k] / n if n else 0.0) for k in range(1, PHOTONS_PER_LEVEL + 1)}


def star_profile(level: dict) -> dict:
    """
    Actual star distribution of a level, measured by ray tracing.
    `shares[k]` = share of valid rays earning at least k stars.
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


# --- Photon placement --------------------------------------------------------

def _anchors(paths, keys_values, param_space):
    """ANCHORS reference paths, from the most robust (the most valid
    neighbouring rays, one notch away on each parameter) to the least."""
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

    # Only paths followed by at least one launch of the SOLVER grid (coarser
    # than the ray grid) can be references: otherwise the 3-star solution
    # exists but the validator can't find it, and the exported reference
    # solution doesn't reproduce it.
    on_grid = [p for p in paths if any(_on_solver_grid(params, param_space) for params in p.rays)]
    ranked = sorted(on_grid or paths, key=lambda p: (-robustness(p), -p.weight))
    if len(ranked) <= ANCHORS:
        return ranked
    picks = sorted({round(i * (len(ranked) - 1) / (ANCHORS - 1)) for i in range(ANCHORS)})
    anchors = [ranked[i] for i in picks]
    routes = {}
    for p in paths:
        routes[p.route] = routes.get(p.route, 0) + p.weight
    for route, _ in sorted(routes.items(), key=lambda kv: -kv[1])[:ROUTE_ANCHORS]:
        best = next((p for p in ranked if p.route == route), None)
        if best is not None and best not in anchors:
            anchors.append(best)
    return anchors


def _on_solver_grid(params, param_space):
    """True if every continuous parameter falls on a notch of the solver
    grid (rays sample it REFINE times finer)."""
    for key, spec in param_space.items():
        if spec["type"] == "range":
            k = (params[key] - spec["min"]) / spec["step"]
            if abs(k - round(k)) > 1e-6:
                return False
    return True


def _clear_of_objects(level, pos, t):
    r = PHOTON_RADIUS
    for obs in level.get("obstacles", []):
        ox, oy = _oscillate(obs["x"], obs["y"], obs.get("motion"), t)
        if shapes.distance(dict(obs, x=ox, y=oy), pos) < shapes.radius(obs) + r + PHOTON_CLEARANCE:
            return False
    tgt = level["target"]
    if vec.dist(pos, (tgt["x"], tgt["y"])) < tgt.get("r", 0.045) + r + PHOTON_CLEARANCE:
        return False
    lau = level["launcher"]
    return vec.dist(pos, (lau["x"], lau["y"])) >= 0.05 + r


def _candidates(level, trail, rungs=()):
    """Free positions on the reference path, fixed or oscillating
    (oscillation perpendicular to the path, zero phase at the instant the
    reference passes: so the reference always collects this Photon)."""
    out = []
    v_max = launch_speed_max(level)
    for i in range(0, len(trail), CANDIDATE_STRIDE):
        t = (i + 1) * DT
        if not _clear_of_objects(level, trail[i], t):
            continue
        base = {"x": round(trail[i][0], 3), "y": round(trail[i][1], 3), "r": PHOTON_RADIUS}
        if rungs:
            base["rung"] = rungs[i]  # colour-matched to the rung Quarky has there
        out.append((i, base))
        step = vec.sub(trail[min(i + 1, len(trail) - 1)], trail[max(i - 1, 0)])
        axis = "y" if abs(step[0]) >= abs(step[1]) else "x"
        for amplitude, period in PHOTON_MOTIONS:
            # anti-tunnelling (core/simulate.check_limits): an oscillation so
            # fast that Quarky could step over the Photon is never proposed
            if (v_max + 2 * math.pi * amplitude / period) * DT >= PHOTON_RADIUS + COLLISION_EPS:
                continue
            phase = round((-2 * math.pi * t / period) % (2 * math.pi), 4)
            out.append((i, dict(base, motion={"axis": axis, "amplitude": amplitude,
                                              "period": period, "phase": phase})))
    return out


def _best_trio(paths, candidates, targets):
    """Best candidate triplet and its cost. Captures as bit masks over the
    rays (each path occupies a block of `weight` bits):
    >=1 star = union, >=2 = union of pairwise intersections,
    3 = intersection. Ideally the three sets are nested."""
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
    def shortlist(k):
        # closest to the tier's target share, at most PER_STEP candidates per
        # trajectory step: when every path collects about the same (a narrow
        # uncertainty cone), the list still spans the path and a well-spaced
        # triplet exists
        out, per_step = [], {}
        for c in sorted(range(len(candidates)), key=lambda c: abs(fractions[c] - targets[k])):
            step = candidates[c][0]
            if per_step.get(step, 0) < SHORTLIST_PER_STEP:
                per_step[step] = per_step.get(step, 0) + 1
                out.append(c)
                if len(out) == SHORTLIST:
                    break
        return out

    shortlists = [shortlist(k) for k in range(1, PHOTONS_PER_LEVEL + 1)]

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
    Return a copy of the level with 3 Photons placed on the path of a
    reference solution, chosen together so that the share of valid rays with
    >= k stars matches target_shares(difficulty).
    Raise ValueError if the level is not solvable.
    """
    bare = copy.deepcopy(level)
    bare["photons"] = []
    _, paths = trace(bare)
    if not paths:
        raise ValueError(f"Level not solvable, cannot place the Photons: {level.get('id')}")
    targets = target_shares(level.get("difficulty", 1))

    best, best_cost = None, None
    for anchor in _anchors(paths, _ray_grid(bare), bare["param_space"]):
        candidates = _candidates(bare, anchor.trail, anchor.rungs)
        trio, cost = _best_trio(paths, candidates, targets)
        if trio is not None and (best_cost is None or cost < best_cost):
            best, best_cost = [candidates[i] for i in trio], cost
    if best is None:
        raise ValueError(f"No triplet of well-spaced Photons: {level.get('id')}")

    # numbered in order of passage along the trajectory
    best.sort(key=lambda c: c[0])
    placed = copy.deepcopy(level)
    placed["photons"] = [dict(id=f"p{n}", **ph) for n, (_, ph) in enumerate(best, start=1)]
    return placed
