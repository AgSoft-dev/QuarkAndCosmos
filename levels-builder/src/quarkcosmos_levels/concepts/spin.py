"""
Concept `spin` — Quantum spin. Plugin of the concept registry (concepts/__init__.py):
the default handler, the obstacle types it owns, and the level template of each
difficulty (1 discover → 2 sequence → 3 chain, see the gameplay-mechanics skill).
"""
from ..core import vec
from ..core.simulate import TAP_MIN_TIME

CONCEPT = "spin"
# Key of the Codex line in content/codex/<lang>/quantique.json.
CODEX_KEY = "spin"


def stern_gerlach(obstacle, pos, vel, params, state):
    """
    Stern–Gerlach magnet (ADR-0008): its field is stronger on one side
    (`up_deg`, the direction of that side). Spin up is deflected TOWARDS it,
    spin down AWAY from it, by `kick_deg` (norm kept). Pre-launch setting
    (`spin_up`, default true) and in-flight action: a tap flips the spin once.
    In real physics the deflection comes from the field gradient and a
    measured spin only ever gives these two answers (physics-pedagogy skill).
    """
    spin_up = params.get("spin_up", True)
    if state.get("tapped", False):
        spin_up = not spin_up
    side = vec.from_angle(obstacle.get("up_deg", -90.0))
    towards = side if spin_up else vec.scale(side, -1.0)
    # rotate the velocity towards `towards`: sign of the 2D cross product
    cross = vel[0] * towards[1] - vel[1] * towards[0]
    kick = abs(obstacle.get("kick_deg", 40)) * (1.0 if cross >= 0.0 else -1.0)
    return vec.from_angle(vec.angle_of(vel) + kick, vec.mag(vel)), "deflect"


# Default handler of the concept's obstacles, and the obstacle types it owns.
DEFAULT_HANDLER = stern_gerlach
HANDLERS = {"magnet": stern_gerlach}


def _level_1():
    # Discover (beta level): one Stern–Gerlach magnet, strong side up. Spin up
    # is deflected up, spin down down. The portal sits on the DOWN branch:
    # start spin down, or start spin up and flip the spin (tap) before the
    # magnet — two variables (pre-launch spin + in-flight flip) to aim for.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.72, "y": 0.84, "r": 0.05},
        "obstacles": [
            {"id": "magnet", "type": "magnet", "x": 0.4, "y": 0.42, "r": 0.06, "up_deg": -90, "kick_deg": 60},
        ],
        "must_contact": [["magnet", "deflect"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -20, "max": 0, "step": 1},
            "power": {"type": "choice", "values": [0.5, 0.7]},
            "spin_up": {"type": "choice", "values": [True, False]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 0.8, "step": 0.05},
        },
    }


def _level_2():
    # Two magnets in series (cascaded Stern–Gerlach), strong side up, 45°
    # each: spin up goes up, spin down goes down. To rise at A then return to
    # horizontal at B, start spin up and flip the spin BETWEEN the magnets.
    return {
        "launcher": {"x": 0.1, "y": 0.72},
        "target": {"x": 0.86, "y": 0.51, "r": 0.05},
        "obstacles": [
            {"id": "A", "type": "magnet", "x": 0.36, "y": 0.72, "r": 0.06, "up_deg": -90, "kick_deg": 45},
            {"id": "B", "type": "magnet", "x": 0.555, "y": 0.465, "r": 0.06, "up_deg": -90, "kick_deg": 45},
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


def _level_3():
    # Three magnets, the middle one mounted upside down (strong side DOWN):
    # the player must READ each magnet's orientation. Rise at A (spin up),
    # rise again at B (upside down: needs spin down, so flip between A and
    # B), then come back down at C (spin down). Magnet C oscillates: the
    # power must also time the arrival.
    return {
        "launcher": {"x": 0.1, "y": 0.9},
        "target": {"x": 0.792, "y": 0.416, "r": 0.05},
        "obstacles": [
            {"id": "A", "type": "magnet", "x": 0.32, "y": 0.9, "r": 0.06, "up_deg": -90, "kick_deg": 40},
            {"id": "B", "type": "magnet", "x": 0.49, "y": 0.707, "r": 0.06, "up_deg": 90, "kick_deg": 40},
            {"id": "C", "type": "magnet", "x": 0.492, "y": 0.47, "r": 0.06, "up_deg": -90, "kick_deg": 60,
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


def build(difficulty: int) -> dict:
    """Level template (layout, `must_contact`, `param_space`) before Photon placement."""
    return {1: _level_1, 2: _level_2, 3: _level_3}[difficulty]()


def param_space(difficulty: int) -> dict:
    """Public setting ranges of the level's dials (shipped in the level file)."""
    return build(difficulty)["param_space"]
