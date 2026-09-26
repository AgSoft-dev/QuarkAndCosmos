"""
Concept `incertitude` — Heisenberg uncertainty principle (no obstacle of its own: box walls only). Plugin of the concept registry (concepts/__init__.py):
the default handler, the obstacle types it owns, and the level template of each
difficulty (1 discover → 2 sequence → 3 chain, see the gameplay-mechanics skill).
"""
from .common import door_wall
from .handlers import wall_reflect

CONCEPT = "incertitude"
# Key of the Codex line in content/codex/<lang>/quantique.json.
CODEX_KEY = "incertitude"


# Default handler of the concept's obstacles, and the obstacle types it owns.
DEFAULT_HANDLER = wall_reflect
HANDLERS = {}


# Continuous dial (slider): with notches, speed and arrival time would be
# discrete too and the moving target would become a lottery.
PRECISIONS = {"type": "range", "min": 0.3, "max": 1.0, "step": 0.05}
# Cone of probability (ADR-0008 follow-up, core/simulate.cone_spreads): the
# launcher always fires at `speed`; the precision dial narrows the direction
# cone (half-angle from 6° down to 0.5°) and in exchange widens the speed
# spread (up to ±0.5). The shot is a seeded draw inside both; a level is
# proven on the whole cone (simulate_cone).
CONE = {"speed": 0.7, "angle": [0.5, 6.0], "speed_spread": 0.5}


def _level_1():
    # Discover (beta level): a slit, then a portal that drifts. Too
    # imprecise, the cone does not fit through the slit; too precise, the
    # speed is so uncertain that the arrival instant — hence where the portal
    # is — becomes unpredictable. Only a middle setting (0.6–0.9) works for
    # every shot of the cone: that trade-off IS the uncertainty principle.
    return {
        "launcher": {"x": 0.1, "y": 0.6},
        "target": {"x": 0.85, "y": 0.5, "r": 0.08, "motion": {"axis": "y", "amplitude": 0.06, "period": 1.3}},
        "cone": CONE,
        "obstacles": door_wall("slit", 0.45, 0.495, 0.585),
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -10, "max": 5, "step": 0.5},
            "precision": PRECISIONS,
        },
    }


def _level_2():
    # Sequence: a narrower slit and a faster portal — the working band of the
    # precision dial shrinks.
    return {
        "launcher": {"x": 0.1, "y": 0.6},
        "target": {"x": 0.85, "y": 0.42, "r": 0.08, "motion": {"axis": "y", "amplitude": 0.07, "period": 1.1}},
        "cone": CONE,
        "obstacles": door_wall("slit", 0.45, 0.47, 0.55),
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -22, "max": -8, "step": 0.5},
            "precision": PRECISIONS,
        },
    }


def _level_3():
    # Chain: two aligned slits and a drifting portal — the cone must thread
    # both slits while the speed stays predictable enough.
    return {
        "launcher": {"x": 0.1, "y": 0.7},
        "target": {"x": 0.88, "y": 0.36, "r": 0.08, "motion": {"axis": "y", "amplitude": 0.05, "period": 1.3}},
        "cone": CONE,
        "obstacles": door_wall("slit1", 0.35, 0.53, 0.63) + door_wall("slit2", 0.6, 0.42, 0.52),
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -32, "max": -18, "step": 0.5},
            "precision": PRECISIONS,
        },
    }


def build(difficulty: int) -> dict:
    """Level template (layout, `must_contact`, `param_space`) before Photon placement."""
    return {1: _level_1, 2: _level_2, 3: _level_3}[difficulty]()


def param_space(difficulty: int) -> dict:
    """Public setting ranges of the level's dials (shipped in the level file)."""
    return build(difficulty)["param_space"]
