"""
Generic simulation loop for the Quantum scale: a closed box with NO gravity
(see the art-direction skill — "Gravity: absent" at this scale), an initial
velocity given by the launch parameters, bounces on the box walls, and
deflections/events driven by the level's concept.

Base "in-flight action" rule (see the gameplay-mechanics skill): on top of
the pre-launch settings, each level can carry a variable that depends on TIME
during the flight, through generic building blocks:
  - "motion" on an obstacle or the target: oscillating position (back and forth).
  - "thickness_motion" on a tunnel barrier: a "breathing" barrier whose
    thickness (hence tunnel threshold) varies over time.
  - "tap_time" in the params: a single player gesture during the flight,
    whose instant is one more parameter searched by the solver (like the
    angle or the power) — see concepts/handlers.py for the handlers that read
    the "tapped" state once that instant has passed.

Integration: fixed step DT, semi-implicit (symplectic) Euler — velocity first
(v += a·DT), then position (x += v·DT). The Quantum box has no force field
(a = 0), so a step is x += v·DT; the order is fixed now so a later scale with
gravity or fields stays bit-for-bit portable (docs/physics-spec.md §4).

Collisions (§5): a reflection only happens while approaching (v·n < 0), and
the penetration is then mirrored out of the contact surface — the position a
continuous collision would give on a flat face. Tunnelling through thin
objects is ruled out by construction: `check_limits` requires every moving
thing to travel less than half an object's contact band per step.
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
# Instruments Quarky never touches: the superposition detector and the near
# crystal of an entangled pair (both only matter at the tap, when measured).
NO_CONTACT = ("detector", "crystal")


def cone_spreads(level: dict, precision: float) -> tuple:
    """Uncertainty (ADR-0008 follow-up): the precision dial p narrows the
    direction cone and widens the speed spread, never both — (half-angle in
    degrees, speed spread). `cone` = {speed, angle: [at p=1, at p=0], speed_spread}."""
    cone = level["cone"]
    narrow, wide = cone["angle"]
    return narrow + (1.0 - precision) * (wide - narrow), cone["speed_spread"] * precision


# Draws that prove a cone: its centre, its edges and both speed extremes.
CONE_PROOF = tuple((a, v) for a in (-1.0, 0.0, 1.0) for v in (-1.0, 0.0, 1.0))


def simulate_cone(level: dict, params: dict, record_trail: bool = False) -> "SimResult":
    """The validator's view of a launch: for an uncertainty level, a setting
    only succeeds if EVERY draw of CONE_PROOF reaches the target; Photons and
    trail are the centre line's (in the game the actual draw decides the
    stars: a wide cone gambles them). Any other level: plain simulate()."""
    if "cone" not in level:
        return simulate(level, params, record_trail)
    centre = simulate(level, dict(params, draw_angle=0.0, draw_speed=0.0), record_trail)
    for a, v in CONE_PROOF:
        if not centre.success:
            break
        if (a, v) == (0.0, 0.0):
            continue
        r = simulate(level, dict(params, draw_angle=a, draw_speed=v))
        if not r.success:
            return SimResult(False, "cone:" + (r.reason or "missed"), set(), centre.steps, centre.trail, centre.contacts)
    return centre


def launch_speed_max(level: dict) -> float:
    """Highest launch speed the level's param_space allows (spec §3)."""
    ps = level.get("param_space", {})

    def values(spec):
        return spec["values"] if spec["type"] == "choice" else [spec["min"], spec["max"]]

    if "rungs" in level:
        return max(level["rungs"])
    if "cone" in level:
        return level["cone"]["speed"] + cone_spreads(level, max(values(ps["precision"])))[1]
    if "power" in ps:
        return max(values(ps["power"]))
    return 1.0


def _motion_speed(motion):
    return 2 * math.pi * abs(motion["amplitude"]) / motion["period"] if motion else 0.0


def check_limits(level: dict) -> list:
    """Anti-tunnelling guarantee (discrete steps, no sweep needed): Quarky and
    any object move towards each other by at most (v + v_obj)·DT per step,
    which must stay below half the object's contact band (radius + EPS), so a
    contact can never be stepped over, however thin the object. Returns the
    list of violations (empty = OK)."""
    v = launch_speed_max(level)
    problems = []
    def thinnest(o):
        # a breathing barrier is at its thinnest at the trough
        m = o.get("thickness_motion")
        return (o["thickness"] - abs(m["amplitude"])) / 2 if m else shapes.radius(o)

    things = [("obstacle", o, thinnest(o)) for o in level.get("obstacles", []) if o.get("type") not in NO_CONTACT]
    things += [("photon", p, p.get("r", 0.02)) for p in level.get("photons", [])]
    things.append(("target", level["target"], level["target"].get("r", 0.045)))
    for kind, obj, r in things:
        # a breathing surface moves at half the thickness rate
        travel = (v + _motion_speed(obj.get("motion")) + _motion_speed(obj.get("thickness_motion")) / 2) * DT
        if travel >= r + COLLISION_EPS:
            problems.append(f"{kind} {obj.get('id', '')}: {travel:.4f} per step >= contact band {r + COLLISION_EPS:.4f}")
    return problems


def _mirror_out(obs, pos, vel_in, vel_out):
    """After a reflection, mirror the penetration out of the contact surface
    (radius + EPS): exact for a flat face, where it equals a continuous
    collision. Only when the handler turned an approach (v·n < 0) into a
    departure (v'·n > 0)."""
    n = shapes.normal(obs, pos)
    d = vec.mag(n)
    reach = shapes.radius(obs) + COLLISION_EPS
    if d < 1e-9 or d >= reach or vec.dot(vel_in, n) >= 0.0 or vec.dot(vel_out, n) <= 0.0:
        return pos
    k = 2 * (reach - d) / d
    return (pos[0] + n[0] * k, pos[1] + n[1] * k)


def _oscillate(base_x, base_y, motion, t):
    """Effective position of an object at time t, shifted by a sinusoidal
    oscillation along one axis (see "Oscillating element", gameplay-mechanics skill)."""
    if not motion:
        return base_x, base_y
    offset = motion["amplitude"] * math.sin(2 * math.pi * t / motion["period"] + motion.get("phase", 0.0))
    if motion["axis"] == "x":
        return base_x + offset, base_y
    return base_x, base_y + offset


def _effective_thickness(obstacle, t):
    """Effective barrier thickness at time t (a "breathing" barrier)."""
    motion = obstacle.get("thickness_motion")
    base = obstacle["thickness"]
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
    # energy rung at each recorded step (quantisation levels only)
    rung_trail: list = field(default_factory=list)


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
    # energy rung (index in level["rungs"]) — quantisation levels only
    rung: int = -1
    rung_trail: list = field(default_factory=list)

    def fork(self, vel):
        return _Body(self.pos, vel, self.wall_bounces, set(self.in_contact),
                     list(self.contacts), set(self.collected), list(self.trail),
                     self.rung, list(self.rung_trail))


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

    if "cone" in level:
        # uncertainty: the shot is a draw inside a cone of probability
        # (cone_spreads); draw_angle / draw_speed in [-1, 1], 0 = centre line
        half_angle, spread = cone_spreads(level, params["precision"])
        angle = params["angle_deg"] + params.get("draw_angle", 0.0) * half_angle
        speed = level["cone"]["speed"] + params.get("draw_speed", 0.0) * spread
        vel = vec.from_angle(angle, speed)
    elif "rungs" in level:
        # quantisation: the launcher only has a few energy rungs (E1…E4),
        # nothing in between (concepts/quantification.py)
        vel = vec.from_angle(params["angle_deg"], level["rungs"][params["rung"]])
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
    bodies = [_Body(pos, vel, rung=params["rung"] if "rungs" in level else -1)]
    # A level may allow more "suffered" bounces (e.g. a required bank shot).
    max_wall_bounces = level.get("max_wall_bounces", MAX_WALL_BOUNCES)
    obstacles = level.get("obstacles", [])

    taps = tap_times(params)
    next_tap = 0
    crystals = [o for o in obstacles if o.get("type") == "crystal"]

    def result(success, body, reason, step):
        return SimResult(success=success, reason=reason,
                         photons_collected=body.collected if success else set(),
                         steps=step, trail=body.trail, contacts=body.contacts,
                         rung_trail=body.rung_trail)

    for step in range(MAX_STEPS):
        elapsed = (step + 1) * DT
        for body in bodies:
            body.pos = vec.add(body.pos, vec.scale(body.vel, DT))
            if record_trail:
                body.trail.append(body.pos)
                if body.rung >= 0:
                    body.rung_trail.append(body.rung)

        # in-flight action (tap): one gesture whose instant is a parameter
        # searched by the solver just like the angle or the power (see the
        # gameplay-mechanics skill — "Action triggered in flight"). During a
        # superposition a tap is a measurement; otherwise it only affects the
        # objects that read state["tapped"].
        while next_tap < len(taps) and elapsed >= taps[next_tap]:
            next_tap += 1
            state["tapped"] = True
            for body in bodies:
                # entanglement: the tap measures the near crystal(s); their
                # linked far gates react at the same instant (gate handlers)
                for crystal in crystals:
                    body.contacts.append((crystal["id"], "measure"))
                if body.rung > 0:
                    # quantisation: the tap makes Quarky jump DOWN one rung,
                    # like an atom giving out light of one exact colour
                    body.rung -= 1
                    body.vel = vec.scale(vec.normalize(body.vel), level["rungs"][body.rung])
                    body.contacts.append(("quarky", "emit"))
            if len(bodies) > 1:
                bodies, det_id = _measure(bodies, level, elapsed)
                if det_id is not None:
                    bodies[0].contacts.append((det_id, "measure"))

        superposed = len(bodies) > 1
        spawned = []
        for body in bodies:
            # walls of the closed box (bounce, never an exit); the penetration
            # is mirrored back inside, like on any flat face
            x, y = body.pos
            vel = body.vel
            bounced = False
            if x <= 0.0:
                x, vel = -x, (abs(vel[0]), vel[1])
                bounced = True
            elif x >= 1.0:
                x, vel = 2.0 - x, (-abs(vel[0]), vel[1])
                bounced = True
            if y <= 0.0:
                y, vel = -y, (vel[0], abs(vel[1]))
                bounced = True
            elif y >= 1.0:
                y, vel = 2.0 - y, (vel[0], -abs(vel[1]))
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
            state["rung"] = body.rung
            for obs in obstacles:
                if obs.get("type") in NO_CONTACT:
                    continue  # measuring instrument: it never touches Quarky
                ox, oy = _oscillate(obs["x"], obs["y"], obs.get("motion"), elapsed)
                placed = obs if (ox, oy) == (obs["x"], obs["y"]) else dict(obs, x=ox, y=oy)
                if obs.get("thickness_motion"):
                    placed = dict(placed, thickness=_effective_thickness(obs, elapsed))
                if not shapes.touching(placed, body.pos, COLLISION_EPS):
                    body.in_contact.discard(obs["id"])
                    continue
                if obs["id"] in body.in_contact:
                    continue
                body.in_contact.add(obs["id"])
                obs_eff = obs
                if obs.get("motion") or obs.get("thickness_motion"):
                    obs_eff = dict(obs)
                    obs_eff["x"], obs_eff["y"] = ox, oy
                    if obs.get("thickness_motion"):
                        obs_eff["thickness"] = _effective_thickness(obs, elapsed)
                handler = handler_for(level["concept"], obs.get("type", ""))
                vel_in = body.vel
                body.vel, event = handler(obs_eff, body.pos, body.vel, params, state)
                if event in ("bounce", "wave"):
                    body.pos = _mirror_out(obs_eff, body.pos, vel_in, body.vel)
                if event == "split":
                    # Superposition: Quarky goes straight on (transmitted copy)
                    # AND reflects (reflected copy).
                    ghost = body.fork(reflect_velocity(obs_eff, body.pos, body.vel))
                    ghost.pos = _mirror_out(obs_eff, body.pos, vel_in, ghost.vel)
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
                if "rung" in ph and ph["rung"] != body.rung:
                    continue  # colour-matched Photon: only on its own rung
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
