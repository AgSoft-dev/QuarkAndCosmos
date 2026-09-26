"""
Base collision rules and handler lookup. Concept-specific handlers live in
their plugin module (concepts/<concept>.py, see concepts/__init__.py).

Every handler has the signature:
    handler(obstacle: dict, pos: Vec2, vel: Vec2, params: dict, state: dict) -> (Vec2, str)

The returned event says what happened on contact (it is logged in
SimResult.contacts, which lets the validator check that a solution really
uses the intended mechanic, see `must_contact`):
    'bounce'  — reflection on the obstacle
    'deflect' — deflection (spin pole)
    'pass'    — the particle goes through the obstacle
    'wave'    — reflection in wave mode (duality)
    'split'   — enters superposition (logged as 'transmit' / 'reflect'
                depending on the copy; the measurement adds 'measure')

A handler is called only once per contact (on entering the obstacle's
radius), see core/simulate.py.
"""
from ..core import shapes, vec


def _bounce(obstacle, pos, vel):
    """Reflection on the obstacle, only if Quarky is approaching it (vec.reflect);
    core/simulate.py then mirrors the penetration out of the obstacle."""
    return vec.reflect(vel, shapes.normal(obstacle, pos)), "bounce"


def wall_reflect(obstacle, pos, vel, params, state):
    """Default behaviour: a plain bounce, like a wall of the closed box."""
    return _bounce(obstacle, pos, vel)


def reflect_velocity(obstacle, pos, vel):
    """Velocity of the copy reflected by a beam splitter."""
    return vec.reflect(vel, shapes.normal(obstacle, pos))


# Base obstacle types, shared by every concept.
_BASE = {
    "wall": wall_reflect,
    # flat mirror: a lab instrument (an intended bounce, never counted as a
    # "suffered" bounce, unlike the walls)
    "mirror": wall_reflect,
}
_by_type = None


def handler_for(concept_id, obstacle_type):
    """Handler of an obstacle: its type's (base or owned by a concept), else
    the level concept's default handler, else a plain bounce."""
    global _by_type
    from . import concept, obstacle_handlers  # lazy: concept modules import this one
    if _by_type is None:
        _by_type = dict(_BASE, **obstacle_handlers())
    handler = _by_type.get(obstacle_type)
    if handler is not None:
        return handler
    try:
        return concept(concept_id).DEFAULT_HANDLER
    except KeyError:
        return wall_reflect
