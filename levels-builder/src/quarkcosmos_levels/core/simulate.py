"""
Generic simulation loop for the Quantum scale: a closed box with NO gravity
(see the art-direction skill — "Gravity: absent" at this scale), an initial
velocity given by the launch parameters, bounces on the box walls, and
deflections/events driven by the level's concept.

Base "in-flight action" rule (see the gameplay-mechanics skill): on top of
the pre-launch settings, each level can carry a variable that depends on TIME
during the flight, through generic building blocks:
  - "motion" on an obstacle or the target: oscillating position (back and forth).
  - "threshold_motion" on a threshold obstacle (tunnel/quantisation):
    oscillating energy threshold.
  - "tap_time" in the params: a single player gesture during the flight,
    whose instant is one more parameter searched by the solver (like the
    angle or the power) — see concepts/handlers.py for the handlers that read
    the "tapped" state once that instant has passed.
"""
import math
from dataclasses import dataclass, field
from . import shapes, vec
from ..concepts.handlers import handler_for, reflect_velocity

DT = 0.01
# Deliberately short (~3 s of simulated flight): beyond that, a random bounce
# in the box nearly always "finds" the target by chance, which would validate
# trajectories that don't really use the concept's mechanic. A short flight
# time forces a direct / few-bounce trajectory, hence a real puzzle solution.
MAX_STEPS = 300
COLLISION_EPS = 0.004
# Earliest in-flight tap (simulated seconds). Below it, tapping would be a
# disguised pre-launch setting (audit finding: the best dualite/intrication
# solutions tapped at t=0), which contradicts the "in-flight action" rule of
# the gameplay-mechanics skill. The validator discards those shots.
TAP_MIN_TIME = 0.1
# "Suffered" bounces (box walls + internal walls) tolerated before the
# particle counts as lost, see the comment in simulate().
MAX_WALL_BOUNCES = 1


def _oscillate(base_x, base_y, motion, t):
    """Effective position of an object at time t, shifted by a sinusoidal
    oscillation along one axis (see "Oscillating element", gameplay-mechanics skill)."""
    if not motion:
        return base_x, base_y
    offset = motion["amplitude"] * math.sin(2 * math.pi * t / motion["period"] + motion.get("phase", 0.0))
    if motion["axis"] == "x":
        return base_x + offset, base_y
    return base_x, base_y + offset


def _effective_threshold(obstacle, t):
    """Effective energy threshold at time t (see "Oscillating element")."""
    motion = obstacle.get("threshold_motion")
    base = obstacle.get("energy_threshold", 0.6)
    if not motion:
        return base
    return base + motion["amplitude"] * math.sin(2 * math.pi * t / motion["period"] + motion.get("phase", 0.0))


@dataclass
class SimResult:
    success: bool
    reason: str = ""
    photons_collected: set = field(default_factory=set)
    steps: int = 0
    trail: list = field(default_factory=list)
    # (obstacle id, handler event) in contact order
    contacts: list = field(default_factory=list)


@dataclass
class _Body:
    """Quarky, or one of its ghost copies while in superposition (see
    concepts.handlers.superposition_splitter). Each copy has its own
    trajectory, contacts, suffered bounces and Photons: only those of the copy
    that survives the measurement count."""
    pos: tuple
    vel: tuple
    wall_bounces: int = 0
    in_contact: set = field(default_factory=set)
    contacts: list = field(default_factory=list)
    collected: set = field(default_factory=set)
    trail: list = field(default_factory=list)

    def fork(self, vel):
        return _Body(self.pos, vel, self.wall_bounces, set(self.in_contact),
                     list(self.contacts), set(self.collected), list(self.trail))


def tap_times(params: dict) -> list:
    """Tap instants of a launch: `tap_time`, then `tap_time_2`… (a
    superposition level can ask for one measurement per splitter)."""
    keys = sorted((k for k in params if k.startswith("tap_time")), key=lambda k: (len(k), k))
    return [params[k] for k in keys if params[k] is not None]


def taps_ordered(params: dict) -> bool:
    """True if successive taps are strictly in order (otherwise the solver
    would count the same launch twice)."""
    keys = sorted((k for k in params if k.startswith("tap_time")), key=lambda k: (len(k), k))
    times = [params[k] for k in keys]
    return all(a < b for a, b in zip(times, times[1:]))


def _measure(bodies, level, elapsed):
    """Measurement (a tap during a superposition): Quarky collapses onto the
    copy closest to a detector. Without a detector, nothing is measured."""
    detectors = [o for o in level.get("obstacles", []) if o.get("type") == "detector"]
    if not detectors:
        return bodies, None
    best, best_d, best_det = None, None, None
    for body in bodies:
        for det in detectors:
            dx, dy = _oscillate(det["x"], det["y"], det.get("motion"), elapsed)
            d = shapes.distance(dict(det, x=dx, y=dy), body.pos)
            if best_d is None or d < best_d - 1e-12:
                best, best_d, best_det = body, d, det
    return [best], best_det["id"]


def simulate(level: dict, params: dict, record_trail: bool = False) -> SimResult:
    launcher = level["launcher"]
    pos = (launcher["x"], launcher["y"])

    if "precision" in params:
        # "incertitude" concept: the aiming precision (dial) sets both the
        # angle step actually reachable (coarse snap when imprecise) and the
        # maximum available power (trade-off, see gameplay-mechanics).
        precision = params["precision"]
        snap = 2 + (1 - precision) * 28
        eff_angle = round(params["angle_deg"] / snap) * snap
        power = max(0.15, 1.2 - precision)
        vel = vec.from_angle(eff_angle, power)
    else:
        vel = vec.from_angle(params["angle_deg"], params.get("power", 1.0))

    target = level["target"]
    photons = {p["id"]: p for p in level.get("photons", [])}
    state = {}
    # MAX_WALL_BOUNCES: beyond it the particle counts as "lost" (this is not a
    # pinball table) — without this limit, a chaotic wall bounce nearly always
    # finds the target again "by chance", which would validate shots that
    # don't use the concept's mechanic.
    #
    # Obstacles currently in contact (per copy): a handler fires only on
    # ENTERING an obstacle's radius, not at every step spent inside it.
    # Previously a spin pole re-applied its deflection at every contact step
    # (total deflection = N * kick_deg, N depending on speed), and crossing a
    # barrier was re-evaluated at every step against an oscillating threshold.
    # One interaction = one contact = one event.
    bodies = [_Body(pos, vel)]
    # A level may allow more "suffered" bounces (e.g. a required bank shot).
    max_wall_bounces = level.get("max_wall_bounces", MAX_WALL_BOUNCES)
    obstacles = level.get("obstacles", [])

    taps = tap_times(params)
    next_tap = 0

    def result(success, body, reason, step):
        return SimResult(success=success, reason=reason,
                         photons_collected=body.collected if success else set(),
                         steps=step, trail=body.trail, contacts=body.contacts)

    for step in range(MAX_STEPS):
        elapsed = (step + 1) * DT
        for body in bodies:
            body.pos = vec.add(body.pos, vec.scale(body.vel, DT))
            if record_trail:
                body.trail.append(body.pos)

        # in-flight action (tap): one gesture whose instant is a parameter
        # searched by the solver just like the angle or the power (see the
        # gameplay-mechanics skill — "Action triggered in flight"). During a
        # superposition a tap is a measurement; otherwise it only affects the
        # objects that read state["tapped"].
        while next_tap < len(taps) and elapsed >= taps[next_tap]:
            next_tap += 1
            state["tapped"] = True
            if len(bodies) > 1:
                bodies, det_id = _measure(bodies, level, elapsed)
                if det_id is not None:
                    bodies[0].contacts.append((det_id, "measure"))

        superposed = len(bodies) > 1
        spawned = []
        for body in bodies:
            # walls of the closed box (bounce, never an exit)
            x, y = body.pos
            vel = body.vel
            bounced = False
            if x <= 0.0:
                x, vel = 0.0, (abs(vel[0]), vel[1])
                bounced = True
            elif x >= 1.0:
                x, vel = 1.0, (-abs(vel[0]), vel[1])
                bounced = True
            if y <= 0.0:
                y, vel = 0.0, (vel[0], abs(vel[1]))
                bounced = True
            elif y >= 1.0:
                y, vel = 1.0, (vel[0], -abs(vel[1]))
                bounced = True
            body.vel = vel
            if bounced:
                body.pos = (x, y)
                body.wall_bounces += 1
                if body.wall_bounces > max_wall_bounces:
                    return result(False, body, _lost(superposed), step)

            # concept-specific obstacles (effective position/threshold at the
            # current instant if the obstacle oscillates, see "Oscillating
            # element" - gameplay-mechanics skill)
            for obs in obstacles:
                if obs.get("type") == "detector":
                    continue  # measuring instrument: it never touches Quarky
                ox, oy = _oscillate(obs["x"], obs["y"], obs.get("motion"), elapsed)
                placed = obs if (ox, oy) == (obs["x"], obs["y"]) else dict(obs, x=ox, y=oy)
                if not shapes.touching(placed, body.pos, COLLISION_EPS):
                    body.in_contact.discard(obs["id"])
                    continue
                if obs["id"] in body.in_contact:
                    continue
                body.in_contact.add(obs["id"])
                obs_eff = obs
                if obs.get("motion") or obs.get("threshold_motion"):
                    obs_eff = dict(obs)
                    obs_eff["x"], obs_eff["y"] = ox, oy
                    obs_eff["energy_threshold"] = _effective_threshold(obs, elapsed)
                handler = handler_for(level["concept"], obs.get("type", ""))
                body.vel, event = handler(obs_eff, body.pos, body.vel, params, state)
                if event == "split":
                    # Superposition: Quarky goes straight on (transmitted copy)
                    # AND reflects (reflected copy).
                    ghost = body.fork(reflect_velocity(obs_eff, body.pos, body.vel))
                    body.contacts.append((obs["id"], "transmit"))
                    ghost.contacts.append((obs["id"], "reflect"))
                    spawned.append(ghost)
                elif obs.get("type") != "wall":
                    body.contacts.append((obs["id"], event))
                if obs.get("type") == "wall":
                    # An internal wall (e.g. an entry bottleneck) is a
                    # "suffered" bounce, like a box wall — it counts toward the
                    # same cap, otherwise a missed shot can ricochet on these
                    # walls forever and land on the target "by chance" (see
                    # the Stage 3 trials that originally motivated
                    # MAX_WALL_BOUNCES).
                    body.wall_bounces += 1
                    if body.wall_bounces > max_wall_bounces:
                        return result(False, body, _lost(superposed), step)

            # photons (collected during the flight, see gameplay-mechanics); a
            # Photon may oscillate (see stars.py: that is what makes 3 stars
            # depend on timing when all valid paths overlap)
            for pid, ph in photons.items():
                if pid in body.collected:
                    continue
                px, py = _oscillate(ph["x"], ph["y"], ph.get("motion"), elapsed)
                if vec.dist(body.pos, (px, py)) < ph.get("r", 0.02) + COLLISION_EPS:
                    body.collected.add(pid)

            # target (effective position if oscillating): it only accepts a
            # measured Quarky — a ghost copy passes through without reaching it.
            if superposed:
                continue
            tx, ty = _oscillate(target["x"], target["y"], target.get("motion"), elapsed)
            if vec.dist(body.pos, (tx, ty)) < target.get("r", 0.045) + COLLISION_EPS:
                return result(True, body, "", step)
        bodies = bodies + spawned

    return result(False, bodies[0], "timeout", MAX_STEPS)


def _lost(superposed):
    # A copy that crashes before the measurement breaks the superposition
    # (decoherence): the whole launch fails, not just that copy.
    return "lost:decoherence" if superposed else "lost:too_many_wall_bounces"
