"""
Concept `superposition` — Superposition of states. Plugin of the concept registry (concepts/__init__.py):
the default handler, the obstacle types it owns, and the level template of each
difficulty (1 discover → 2 sequence → 3 chain, see the gameplay-mechanics skill).
"""
from .common import seg

CONCEPT = "superposition"
# Key of the Codex line in content/codex/<lang>/quantique.json.
CODEX_KEY = "superposition"


def superposition_splitter(obstacle, pos, vel, params, state):
    """
    (Flat) beam splitter: on contact Quarky enters superposition. It goes
    straight on (transmitted copy) AND reflects (reflected copy) — two ghost
    copies flying at the same time (see simulate._Body). The tap is the
    measurement: Quarky collapses onto the copy closest to a detector, the
    other fades out with its Photons. The target only accepts a measured
    Quarky, and a copy that crashes before the measurement breaks the
    superposition (decoherence: the launch fails).
    Deliberate simplification: a real measurement is random; here the timing
    and the detector make it deterministic and playable (see the Codex page).
    """
    return vel, "split"


# Default handler of the concept's obstacles, and the obstacle types it owns.
DEFAULT_HANDLER = superposition_splitter
HANDLERS = {"splitter": superposition_splitter}


def _level_1():
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
            seg("S", "splitter", 0.28, 0.67, 0.52, 0.43),
            seg("D", "detector", 0.72, 0.3, 0.72, 0.36),
            seg("cloison", "wall", 0.58, 0.64, 0.58, 1.0),
        ],
        "must_contact": [["S", "reflect"], ["D", "measure"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -100, "max": -80, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": 0.1, "max": 1.6, "step": 0.1},
        },
    }


def _level_2():
    # Two-mirror loop (interferometer): the transmitted copy goes up, then M1
    # sends it right; the reflected copy goes right, then M2 sends it up. Both
    # copies cross near the target, so either can reach it: two routes, keep
    # one or the other. Detector D sweeps up and down: its position at the
    # tap instant decides which copy becomes real.
    return {
        "launcher": {"x": 0.2, "y": 0.92},
        "target": {"x": 0.8, "y": 0.1, "r": 0.05},
        "obstacles": [
            seg("S", "splitter", 0.1, 0.7, 0.3, 0.5),
            seg("M1", "mirror", 0.1, 0.3, 0.3, 0.1),
            seg("M2", "mirror", 0.7, 0.7, 0.9, 0.5),
            dict(seg("D", "detector", 0.47, 0.45, 0.53, 0.45),
                 motion={"axis": "y", "amplitude": 0.15, "period": 1.2, "phase": 3.14}),
            seg("cloison", "wall", 0.36, 0.62, 0.36, 1.0),
        ],
        "must_contact": [["D", "measure"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -94, "max": -84, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.8, "step": 0.1},
            "tap_time": {"type": "range", "min": 0.3, "max": 3.0, "step": 0.1},
        },
    }


def _level_3():
    # Two measurements in one flight: S1 splits, keep the reflected copy (the
    # transmitted one soon crashes on the lid, "couvercle": short window), then
    # S2 splits again, this time keep the copy rising towards the target
    # before the other crashes on the right. Two taps, each in a window
    # between two contacts.
    return {
        "launcher": {"x": 0.3, "y": 0.9},
        "target": {"x": 0.62, "y": 0.12, "r": 0.05},
        "obstacles": [
            seg("S1", "splitter", 0.2, 0.65, 0.4, 0.45),
            seg("couvercle", "wall", 0.15, 0.35, 0.42, 0.35),
            seg("S2", "splitter", 0.52, 0.65, 0.72, 0.45),
            seg("D", "detector", 0.55, 0.39, 0.55, 0.45),
            seg("cloison", "wall", 0.46, 0.62, 0.46, 1.0),
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


def build(difficulty: int) -> dict:
    """Level template (layout, `must_contact`, `param_space`) before Photon placement."""
    return {1: _level_1, 2: _level_2, 3: _level_3}[difficulty]()


def param_space(difficulty: int) -> dict:
    """Public setting ranges of the level's dials (shipped in the level file)."""
    return build(difficulty)["param_space"]
