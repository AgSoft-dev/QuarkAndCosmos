"""
Level templates for the first world (Quantum scale; the 7 beta concepts are
listed in the gameplay-mechanics skill): 3 difficulties per concept
(1 discover → 2 sequence → 3 chain, see gameplay-mechanics). Layouts are
deliberately simple and readable.

Player-facing text (the Codex line of each concept) is not generated here: it
lives in content/codex/{en,fr}/quantique.json, keyed by concept.
"""

from ..core.simulate import TAP_MIN_TIME
from ..solver.stars import place_photons


def _seg(id_, type_, x1, y1, x2, y2, **extra):
    """Flat obstacle (see shapes.py) defined by its two end points."""
    import math
    return dict({
        "id": id_, "type": type_,
        "x": round((x1 + x2) / 2, 4), "y": round((y1 + y2) / 2, 4),
        "length": round(math.hypot(x2 - x1, y2 - y1), 4),
        "angle_deg": round(math.degrees(math.atan2(y2 - y1, x2 - x1)), 2),
    }, **extra)


def make_level(concept: str, difficulty: int = 1) -> dict:
    builder = _BUILDERS.get(concept)
    if builder is None:
        raise ValueError(f"Unknown concept: {concept}")
    level = builder(difficulty)
    level["id"] = f"quantique-{concept}-{difficulty}"
    level["scale"] = "quantique"
    level["concept"] = concept
    level["difficulty"] = difficulty
    # Photons placed by ray tracing (see stars.py): the share of valid paths
    # earning 1/2/3 stars follows a truncated gaussian whose σ shrinks with
    # difficulty.
    return place_photons(level)


def _superposition(difficulty):
    return {1: _superposition_1, 2: _superposition_2, 3: _superposition_3}[difficulty]()


def _superposition_1():
    # Discover: splitter S cuts Quarky into two ghost copies — one goes
    # straight on towards the ceiling (and crashes there), the other reflects
    # towards the target. Tap = measure: Quarky becomes the copy closest to
    # detector D, placed on the target's side. Window: between the split and
    # the moment the reflected copy passes the target (the target only
    # accepts a measured Quarky). The partition ("cloison") blocks the direct shot.
    return {
        "launcher": {"x": 0.4, "y": 0.9},
        "target": {"x": 0.85, "y": 0.55, "r": 0.05},
        "obstacles": [
            _seg("S", "splitter", 0.28, 0.67, 0.52, 0.43),
            _seg("D", "detector", 0.72, 0.3, 0.72, 0.36),
            _seg("cloison", "wall", 0.58, 0.64, 0.58, 1.0),
        ],
        "must_contact": [["S", "reflect"], ["D", "measure"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -100, "max": -80, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": 0.1, "max": 1.6, "step": 0.1},
        },
    }


def _superposition_2():
    # Two-mirror loop (interferometer): the transmitted copy goes up, then M1
    # sends it right; the reflected copy goes right, then M2 sends it up. Both
    # copies cross near the target, so either can reach it: two routes, keep
    # one or the other. Detector D sweeps up and down: its position at the
    # tap instant decides which copy becomes real.
    return {
        "launcher": {"x": 0.2, "y": 0.92},
        "target": {"x": 0.8, "y": 0.1, "r": 0.05},
        "obstacles": [
            _seg("S", "splitter", 0.1, 0.7, 0.3, 0.5),
            _seg("M1", "mirror", 0.1, 0.3, 0.3, 0.1),
            _seg("M2", "mirror", 0.7, 0.7, 0.9, 0.5),
            dict(_seg("D", "detector", 0.47, 0.45, 0.53, 0.45),
                 motion={"axis": "y", "amplitude": 0.15, "period": 1.2, "phase": 3.14}),
            _seg("cloison", "wall", 0.36, 0.62, 0.36, 1.0),
        ],
        "must_contact": [["D", "measure"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -94, "max": -84, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.8, "step": 0.1},
            "tap_time": {"type": "range", "min": 0.3, "max": 3.0, "step": 0.1},
        },
    }


def _superposition_3():
    # Two measurements in one flight: S1 splits, keep the reflected copy (the
    # transmitted one soon crashes on the lid, "couvercle": short window), then
    # S2 splits again, this time keep the copy rising towards the target
    # before the other crashes on the right. Two taps, each in a window
    # between two contacts.
    return {
        "launcher": {"x": 0.3, "y": 0.9},
        "target": {"x": 0.62, "y": 0.12, "r": 0.05},
        "obstacles": [
            _seg("S1", "splitter", 0.2, 0.65, 0.4, 0.45),
            _seg("couvercle", "wall", 0.15, 0.35, 0.42, 0.35),
            _seg("S2", "splitter", 0.52, 0.65, 0.72, 0.45),
            _seg("D", "detector", 0.55, 0.39, 0.55, 0.45),
            _seg("cloison", "wall", 0.46, 0.62, 0.46, 1.0),
        ],
        "must_contact": [["S1", "reflect"], ["D", "measure"], ["S2", "reflect"], ["D", "measure"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -94, "max": -84, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.8, "step": 0.1},
            "tap_time": {"type": "range", "min": 0.3, "max": 1.4, "step": 0.1},
            "tap_time_2": {"type": "range", "min": 0.8, "max": 2.6, "step": 0.1},
        },
    }


def _tunnel(difficulty):
    return {1: _tunnel_1, 2: _tunnel_2, 3: _tunnel_3}[difficulty]()


def _barrier(id_, x1, y1, x2, y2, base, amplitude, period, phase):
    """Flat energy barrier whose threshold oscillates (see simulate)."""
    return _seg(id_, "barrier", x1, y1, x2, y2, energy_threshold=base,
                threshold_motion={"amplitude": amplitude, "period": period, "phase": phase})


def _tunnel_2():
    # Resonance: two barriers in series with oscillating thresholds (at the
    # peak even max power does not pass). The power sets both the speed AND
    # the two arrival instants: find a speed that hits a threshold trough at
    # both barriers.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.88, "y": 0.5, "r": 0.05},
        "obstacles": [
            _barrier("b1", 0.38, 0.4, 0.38, 0.6, base=0.6, amplitude=0.4, period=0.8, phase=0.0),
            _barrier("b2", 0.66, 0.4, 0.66, 0.6, base=0.6, amplitude=0.4, period=0.8, phase=2.2),
        ] + _door_wall("w1", 0.38, 0.4, 0.6) + _door_wall("w2", 0.66, 0.4, 0.6),
        "must_contact": [["b1", "pass"], ["b2", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.3, "max": 0.95, "step": 0.05},
        },
    }


def _tunnel_3():
    # Barrier, mirror, barrier: cross b1, get sent up by the mirror, cross b2
    # (offset oscillating thresholds). The longer path between the two
    # barriers makes the resonance tighter. The threshold peak (0.98) exceeds
    # max power (0.95): brute force never works, you must hit a trough.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.6, "y": 0.16, "r": 0.04},
        "obstacles": [
            _barrier("b1", 0.34, 0.71, 0.34, 0.89, base=0.6, amplitude=0.38, period=0.9, phase=1.5),
            _seg("m", "mirror", 0.53, 0.87, 0.67, 0.73),
            _barrier("b2", 0.51, 0.45, 0.69, 0.45, base=0.6, amplitude=0.38, period=0.9, phase=3.0),
            _seg("ceilL", "wall", 0.34, 0.45, 0.51, 0.45),
            _seg("ceilR", "wall", 0.69, 0.45, 1.05, 0.45),
        ] + _door_wall("w1", 0.34, 0.71, 0.89),
        "must_contact": [["b1", "pass"], ["m", "bounce"], ["b2", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.3, "max": 0.95, "step": 0.05},
        },
    }


def _tunnel_1():
    # Intro: a single barrier, a window in a wall (same vocabulary as
    # difficulties 2-3). Its threshold oscillates slowly and its peak (1.05)
    # exceeds max power: you need enough speed AND to arrive during a trough.
    # Immediate visual feedback: you pass or you bounce.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.86, "y": 0.5, "r": 0.05},
        "obstacles": [
            _barrier("barrier", 0.5, 0.4, 0.5, 0.6, base=0.6, amplitude=0.45, period=1.0, phase=0.0),
        ] + _door_wall("w", 0.5, 0.4, 0.6),
        "must_contact": [["barrier", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.3, "max": 0.95, "step": 0.05},
        },
    }


def _intrication(difficulty):
    return {1: _intrication_1, 2: _intrication_2, 3: _intrication_3}[difficulty]()


def _door_wall(prefix, x, y0, y1):
    """Vertical wall at x with an opening [y0, y1] (for a gate)."""
    return [_seg(f"{prefix}Top", "wall", x, -0.05, x, y0), _seg(f"{prefix}Bot", "wall", x, y1, x, 1.05)]


def _intrication_2():
    # ANTI-correlated pair: gate A is open until the tap, gate B is closed
    # until the tap. A single gesture opens one and closes the other: cross
    # A, THEN tap, then cross B.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.88, "y": 0.5, "r": 0.05},
        "obstacles": [
            _seg("A", "gate_anti", 0.4, 0.42, 0.4, 0.58),
            _seg("B", "gate", 0.65, 0.42, 0.65, 0.58),
        ] + _door_wall("wA", 0.4, 0.42, 0.58) + _door_wall("wB", 0.65, 0.42, 0.58),
        "must_contact": [["A", "pass"], ["B", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.4, "step": 0.05},
        },
    }


def _intrication_3():
    # Gate M, entangled with B, acts as a MIRROR while closed: cross A (anti:
    # open before the tap), bounce up off M (closed), THEN tap to open B (and
    # M, but we have already left it). Tapping too early: M opens and we go
    # through it; far too early: A closes in front of us. A single window:
    # between the bounce on M and B.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.55, "y": 0.18, "r": 0.05},
        "obstacles": [
            _seg("A", "gate_anti", 0.3, 0.72, 0.3, 0.88),
            _seg("M", "gate", 0.48, 0.87, 0.62, 0.73),
            _seg("B", "gate", 0.47, 0.45, 0.63, 0.45),
            _seg("ceilL", "wall", 0.3, 0.45, 0.47, 0.45),
            _seg("ceilR", "wall", 0.63, 0.45, 1.05, 0.45),
        ] + _door_wall("wA", 0.3, 0.72, 0.88),
        "must_contact": [["A", "pass"], ["M", "bounce"], ["B", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.6, "step": 0.05},
        },
    }


def _intrication_1():
    # An in-flight action (see gameplay-mechanics) replaces the pre-launch
    # lever: the player taps ONCE during the flight (tap_time, searched by the
    # solver like the angle or the power) — the witness AND the gate flip at
    # the same instant. Too early or too late = gate closed when passing =
    # bounce.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.85, "y": 0.5, "r": 0.05},
        "obstacles": [
            {"id": "gate", "type": "gate", "x": 0.5, "y": 0.5, "r": 0.05},
        ],
        "must_contact": [["gate", "pass"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -3, "max": 3, "step": 1},
            "power": {"type": "choice", "values": [0.5, 0.7]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.0, "step": 0.05},
        },
    }


def _incertitude(difficulty):
    return {1: _incertitude_1, 2: _incertitude_2, 3: _incertitude_3}[difficulty]()


# Continuous dial (slider): with notches, speed and arrival time would be
# discrete too and the moving target would become a lottery.
PRECISIONS = {"type": "range", "min": 0.3, "max": 1.0, "step": 0.05}


def _incertitude_2():
    # Dilemma: a narrow slit needs precise aim (high dial)... which slows
    # Quarky down, while the target behind the slit drifts. An imprecise dial
    # is fast but only aims in big steps: find the trade-off that clears the
    # slit AND arrives at the right moment.
    return {
        "launcher": {"x": 0.1, "y": 0.6},
        "target": {"x": 0.85, "y": 0.39, "r": 0.05,
                   "motion": {"axis": "y", "amplitude": 0.04, "period": 1.1}},
        "obstacles": _door_wall("slit", 0.45, 0.465, 0.535),
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -30, "max": 5, "step": 0.5},
            "precision": PRECISIONS,
        },
    }


def _incertitude_3():
    # Two aligned slits (tighter opening) and a faster-drifting target: the
    # precision/speed trade-off gets tighter.
    return {
        "launcher": {"x": 0.1, "y": 0.7},
        "target": {"x": 0.88, "y": 0.33, "r": 0.04,
                   "motion": {"axis": "y", "amplitude": 0.07, "period": 0.8}},
        "obstacles": _door_wall("slit1", 0.35, 0.535, 0.625) + _door_wall("slit2", 0.6, 0.42, 0.51),
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -35, "max": 5, "step": 0.5},
            "precision": PRECISIONS,
        },
    }


def _incertitude_1():
    # Oscillating element (see gameplay-mechanics): the target drifts
    # slightly — it combines with the existing precision/speed trade-off
    # (aiming right is no longer enough, you must also arrive at the right
    # moment).
    return {
        "launcher": {"x": 0.1, "y": 0.6},
        "target": {"x": 0.85, "y": 0.5, "r": 0.03, "motion": {"axis": "y", "amplitude": 0.02, "period": 0.8}},
        "obstacles": [],
        "param_space": {
            "angle_deg": {"type": "range", "min": -15, "max": 5, "step": 0.5},
            "precision": {"type": "choice", "values": [0.3, 0.5, 0.7, 0.8, 0.9, 1.0]},
        },
    }


def _quantification(difficulty):
    return {1: _quantification_1, 2: _quantification_2, 3: _quantification_3}[difficulty]()


QUANTA = [0.3, 0.45, 0.6, 0.75, 0.9]


def _quantification_2():
    # The launcher only has 5 energy notches. Two barriers in series with
    # oscillating thresholds: each notch gives a different speed AND arrival
    # instants: only two notches (0.45 and 0.9) hit a trough at both barriers.
    # (Pending the "lock tuned to one notch" redesign — [GATE] in todo.md.)
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.88, "y": 0.5, "r": 0.05},
        "obstacles": [
            _barrier("b1", 0.36, 0.4, 0.36, 0.6, base=0.6, amplitude=0.4, period=0.7, phase=0.0),
            _barrier("b2", 0.64, 0.4, 0.64, 0.6, base=0.6, amplitude=0.4, period=0.7, phase=0.8),
        ] + _door_wall("w1", 0.36, 0.4, 0.6) + _door_wall("w2", 0.64, 0.4, 0.6),
        "must_contact": [["b1", "pass"], ["b2", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "choice", "values": QUANTA},
        },
    }


def _quantification_3():
    # Three barriers, one after a mirror: the right notch must hit a trough
    # three times in a row: only one notch (0.45) does. You can't "dose":
    # you have to choose.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.6, "y": 0.16, "r": 0.06},
        "obstacles": [
            _barrier("b1", 0.3, 0.71, 0.3, 0.89, base=0.6, amplitude=0.4, period=0.7, phase=0.0),
            _barrier("b2", 0.44, 0.71, 0.44, 0.89, base=0.6, amplitude=0.4, period=0.7, phase=3.6),
            _seg("m", "mirror", 0.53, 0.87, 0.67, 0.73),
            _barrier("b3", 0.51, 0.45, 0.69, 0.45, base=0.6, amplitude=0.4, period=0.7, phase=0.8),
            _seg("ceilL", "wall", 0.44, 0.45, 0.51, 0.45),
            _seg("ceilR", "wall", 0.69, 0.45, 1.05, 0.45),
        ] + _door_wall("w1", 0.3, 0.71, 0.89) + _door_wall("w2", 0.44, 0.71, 0.89),
        "must_contact": [["b1", "pass"], ["b2", "pass"], ["m", "bounce"], ["b3", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "choice", "values": QUANTA},
        },
    }


def _quantification_1():
    # Oscillating element (see gameplay-mechanics), same principle as the
    # tunnel: the barrier's threshold varies over time, on top of the
    # launcher's fixed energy notches (the two variables combine).
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.85, "y": 0.5, "r": 0.05},
        "obstacles": [
            {"id": "barrier", "type": "barrier", "x": 0.45, "y": 0.5, "r": 0.05,
             "energy_threshold": 0.65,
             "threshold_motion": {"amplitude": 0.45, "period": 0.2, "phase": 1.2}},
        ],
        "must_contact": [["barrier", "pass"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -3, "max": 3, "step": 1},
            "power": {"type": "choice", "values": [0.2, 0.4, 0.6, 0.8, 1.0]},
        },
    }


def _spin(difficulty):
    return {1: _spin_1, 2: _spin_2, 3: _spin_3}[difficulty]()


def _spin_2():
    # Two "+" poles in series (cascaded Stern-Gerlach style), each deflecting
    # by 45°: spin up = attracted (upwards), spin down = repelled. To rise at
    # A then return to horizontal at B, start spin up and flip the spin
    # BETWEEN the two poles. The only combination.
    return {
        "launcher": {"x": 0.1, "y": 0.72},
        "target": {"x": 0.86, "y": 0.51, "r": 0.05},
        "obstacles": [
            {"id": "A", "type": "pole", "x": 0.36, "y": 0.72, "r": 0.06, "pole": "+", "kick_deg": -45},
            {"id": "B", "type": "pole", "x": 0.555, "y": 0.465, "r": 0.06, "pole": "+", "kick_deg": -45},
        ],
        "must_contact": [["A", "deflect"], ["B", "deflect"]],
        # no bank shots: touching a wall = particle lost
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -10, "max": 10, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "spin_up": {"type": "choice", "values": [True, False]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.4, "step": 0.05},
        },
    }


def _spin_3():
    # Three poles with signs +, −, + (deflections 40°, 40°, 60°): the player
    # must READ each pole's sign. Rise at A (spin up, attracted by +), rise
    # again at B (pole −, must be attracted so spin down: flip between A and
    # B), then come back down at C (pole +, spin down = repelled). Pole C
    # oscillates: the power must also time the arrival.
    return {
        "launcher": {"x": 0.1, "y": 0.9},
        "target": {"x": 0.792, "y": 0.416, "r": 0.05},
        "obstacles": [
            {"id": "A", "type": "pole", "x": 0.32, "y": 0.9, "r": 0.06, "pole": "+", "kick_deg": -40},
            {"id": "B", "type": "pole", "x": 0.49, "y": 0.707, "r": 0.06, "pole": "-", "kick_deg": -40},
            {"id": "C", "type": "pole", "x": 0.492, "y": 0.47, "r": 0.06, "pole": "+", "kick_deg": -60,
             "motion": {"axis": "x", "amplitude": 0.05, "period": 1.2}},
        ],
        "must_contact": [["A", "deflect"], ["B", "deflect"], ["C", "deflect"]],
        # no bank shots: touching a wall = particle lost
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -10, "max": 10, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "spin_up": {"type": "choice", "values": [True, False]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.8, "step": 0.05},
        },
    }


def _spin_1():
    # Combines with the pre-launch setting (spin_up = starting polarity): a
    # tap during the flight (see gameplay-mechanics) flips the polarity once —
    # two variables instead of one to aim for the right contact.
    # Target placed on the "repelled" branch (downward deflection): either
    # start spin down, or start spin up and tap BEFORE touching the pole. The
    # deflection applies only once per contact (see simulate.py) — the old
    # target (0.867, 0.69) was only reached thanks to a deflection re-applied
    # at every step, and only within 1° of aim.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.72, "y": 0.84, "r": 0.05},
        "obstacles": [
            {"id": "pole", "type": "pole", "x": 0.4, "y": 0.42, "r": 0.06,
             "pole": "+", "kick_deg": -60},
        ],
        "must_contact": [["pole", "deflect"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -20, "max": 0, "step": 1},
            "power": {"type": "choice", "values": [0.5, 0.7]},
            "spin_up": {"type": "choice", "values": [True, False]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 0.8, "step": 0.05},
        },
    }


def _dualite(difficulty):
    return {1: _dualite_1, 2: _dualite_2, 3: _dualite_3}[difficulty]()


def _dualite_2():
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
            _seg("s1", "surface", 0.38, 0.87, 0.52, 0.73, interference_offset_deg=180),
            _seg("s2", "surface", 0.35, 0.42, 0.55, 0.42, interference_offset_deg=180),
            _seg("ceilL", "wall", -0.05, 0.42, 0.35, 0.42),
            _seg("ceilR", "wall", 0.55, 0.42, 1.05, 0.42),
        ],
        "must_contact": [["s1", "bounce"], ["s2", "wave"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -15, "max": 15, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.6, "step": 0.05},
        },
    }


def _dualite_3():
    # Chain: two particle bounces (mirrors s1 then s2: right -> up -> right),
    # then a wave crossing of window s3 into the right chamber, where the
    # target drifts. The tap must land between s2 and s3, and the power times
    # the arrival against the moving target.
    return {
        "launcher": {"x": 0.1, "y": 0.85},
        "target": {"x": 0.86, "y": 0.45, "r": 0.05,
                   "motion": {"axis": "y", "amplitude": 0.08, "period": 1.6}},
        "obstacles": [
            _seg("s1", "surface", 0.25, 0.92, 0.39, 0.78, interference_offset_deg=180),
            _seg("s2", "surface", 0.18, 0.59, 0.39, 0.38, interference_offset_deg=180),
            _seg("s3", "surface", 0.65, 0.33, 0.65, 0.57, interference_offset_deg=180),
            _seg("wallTop", "wall", 0.65, -0.05, 0.65, 0.33),
            _seg("wallBot", "wall", 0.65, 0.57, 0.65, 1.05),
            _seg("shelf", "wall", 0.42, 0.66, 0.65, 0.66),
            # lid above s2: in wave mode too early, Quarky crosses s2 upwards
            # and must not reach s3 via the ceiling
            _seg("lid", "wall", 0.18, 0.26, 0.5, 0.26),
        ],
        "must_contact": [["s1", "bounce"], ["s2", "bounce"], ["s3", "wave"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -15, "max": 15, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 2.2, "step": 0.05},
        },
    }


def _dualite_1():
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


# Order = introduction order in the Quantum world (beta), see the
# gameplay-mechanics skill. "tunnel" opens the world: the most immediate
# mechanic (a speed threshold to clear or not, a single obstacle, obvious
# visual feedback) gets the player used to launching in a closed box without
# gravity before asking them to understand a choice of path (superposition).
_BUILDERS = {
    "tunnel": _tunnel,
    "superposition": _superposition,
    "intrication": _intrication,
    "incertitude": _incertitude,
    "quantification": _quantification,
    "spin": _spin,
    "dualite": _dualite,
}

ALL_CONCEPTS = list(_BUILDERS.keys())
# Difficulties available per concept: 1 = discover (one instance of the
# mechanic), 2 = sequence (the mechanic used twice, both ways), 3 = chain
# (three instances, or two + a moving element).
DIFFICULTIES = [1, 2, 3]
