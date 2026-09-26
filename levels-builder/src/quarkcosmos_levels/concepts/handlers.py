"""
Simplified ("popularised") collision rules per quantum concept (see the
gameplay-mechanics skill for the 7 beta concepts).

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
    return vec.reflect(vel, shapes.normal(obstacle, pos)), "bounce"


def wall_reflect(obstacle, pos, vel, params, state):
    """Default behaviour: a plain bounce, like a wall of the closed box."""
    return _bounce(obstacle, pos, vel)


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


def reflect_velocity(obstacle, pos, vel):
    """Velocity of the copy reflected by a beam splitter."""
    return vec.reflect(vel, shapes.normal(obstacle, pos))


def tunnel_barrier(obstacle, pos, vel, params, state):
    """
    Crossing under an energy condition: if the speed at contact reaches the
    barrier's threshold, the particle goes through (tunnel effect);
    otherwise it bounces like a classical wall.
    """
    if vec.mag(vel) >= obstacle.get("energy_threshold", 0.6):
        return vel, "pass"
    return _bounce(obstacle, pos, vel)


def intrication_gate(obstacle, pos, vel, params, state):
    """
    Gate linked to an identical "witness" (see the gameplay-mechanics skill —
    "Action triggered in flight"): the player taps ONCE during the flight
    (instant = params["tap_time"], searched by the solver like any other
    parameter), which flips both objects — witness and gate — at the same
    instant. Before the tap: gate closed (blocks like a wall). After: open
    (lets through).
    """
    if state.get("tapped", False):
        return vel, "pass"
    return _bounce(obstacle, pos, vel)


def intrication_gate_anti(obstacle, pos, vel, params, state):
    """
    Anti-correlated partner of an entangled gate: open BEFORE the tap, closed
    after. The same gesture opens one gate and closes another — two entangled
    objects whose states are always opposite (a popularisation of the
    anti-correlated measurements of an entangled pair). It creates a tap
    window: this gate must be crossed BEFORE tapping.
    """
    if state.get("tapped", False):
        return _bounce(obstacle, pos, vel)
    return vel, "pass"


def spin_pole(obstacle, pos, vel, params, state):
    """
    Spin polarity (+/-) deciding whether the obstacle attracts or repels.
    Pre-launch setting (spin_up = starting polarity, see gameplay-mechanics)
    AND in-flight action: a tap (params["tap_time"]) flips the polarity once
    during the flight — two variables combine to aim for the right contact at
    the right instant.
    """
    spin_up = params.get("spin_up", True)
    if state.get("tapped", False):
        spin_up = not spin_up
    pole = obstacle.get("pole", "+")
    attract = (spin_up and pole == "+") or (not spin_up and pole == "-")
    kick = obstacle.get("kick_deg", 40)
    kick = kick if attract else -kick
    ang = vec.angle_of(vel) + kick
    return vec.from_angle(ang, vec.mag(vel)), "deflect"


def dualite_surface(obstacle, pos, vel, params, state):
    """
    Wave/particle toggle IN FLIGHT (see gameplay-mechanics — "Action
    triggered in flight"): Quarky starts in particle mode (classical bounce),
    and a tap during the flight (params["tap_time"]) switches it to wave mode
    for the rest of the path (bounce + interference offset, which foreshadows
    without duplicating the real reflection lesson taught at the Macro scale,
    see the storytelling skill).
    """
    vel2, _ = _bounce(obstacle, pos, vel)
    if state.get("tapped", False):
        offset = obstacle.get("interference_offset_deg", 15)
        if offset % 360 == 180:
            # 180° = pure transmission: the wave crosses the surface without
            # changing direction, whatever the incidence (otherwise, on a
            # tilted surface, "bounce + 180°" sends back a mirror image of the
            # direction, unreadable for the player).
            return vel, "wave"
        ang = vec.angle_of(vel2) + offset
        return vec.from_angle(ang, vec.mag(vel2)), "wave"
    return vel2, "bounce"


# Registry: concept -> default handler for its specific obstacles.
# Concepts without a dedicated obstacle (incertitude, quantification) only
# use wall_reflect on the box walls.
HANDLERS = {
    "superposition": superposition_splitter,
    "tunnel": tunnel_barrier,
    "intrication": intrication_gate,
    "incertitude": wall_reflect,
    "quantification": wall_reflect,
    "spin": spin_pole,
    "dualite": dualite_surface,
}


def handler_for(concept, obstacle_type):
    """An obstacle can override the concept's handler through its own type."""
    specific = {
        "wall": wall_reflect,
        # flat mirror: a lab instrument (an intended bounce, never counted as
        # a "suffered" bounce, unlike the walls)
        "mirror": wall_reflect,
        "splitter": superposition_splitter,
        "barrier": tunnel_barrier,
        "gate": intrication_gate,
        "gate_anti": intrication_gate_anti,
        "pole": spin_pole,
        "surface": dualite_surface,
    }
    return specific.get(obstacle_type, HANDLERS.get(concept, wall_reflect))
