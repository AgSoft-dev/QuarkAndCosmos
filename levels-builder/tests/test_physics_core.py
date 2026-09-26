"""Physics core (S2, docs/physics-spec.md §4–§7): shapes, reflection only when
approaching, penetration mirrored out, anti-tunnelling limits, and one test per
handler of the concept registry."""
import math

import pytest

from quarkcosmos_levels.concepts import ALL_CONCEPTS, concept
from quarkcosmos_levels.concepts.handlers import handler_for, reflect_velocity, wall_reflect
from quarkcosmos_levels.core import shapes, vec
from quarkcosmos_levels.core.simulate import COLLISION_EPS, DT, check_limits, simulate


def _level(obstacles, concept_id="tunnel", target=(5.0, 5.0), launcher=(0.1, 0.5), max_wall_bounces=3):
    return {
        "concept": concept_id,
        "launcher": {"x": launcher[0], "y": launcher[1]},
        "target": {"x": target[0], "y": target[1], "r": 0.05},
        "obstacles": obstacles,
        "photons": [],
        "max_wall_bounces": max_wall_bounces,
    }


# --- shapes ------------------------------------------------------------------

def test_capsule_closest_point_clamps_to_end_caps():
    seg = {"x": 0.5, "y": 0.5, "length": 0.2, "angle_deg": 0}
    assert shapes.closest_point(seg, (0.55, 0.3)) == pytest.approx((0.55, 0.5))
    assert shapes.closest_point(seg, (0.9, 0.5)) == pytest.approx((0.6, 0.5))


def test_polygon_outline_nearest_edge_and_radius():
    square = {"x": 0.5, "y": 0.5, "points": [[-0.1, -0.1], [0.1, -0.1], [0.1, 0.1], [-0.1, 0.1]]}
    assert shapes.radius(square) == shapes.SEGMENT_HALF_THICKNESS
    assert shapes.extent(square) == pytest.approx(math.hypot(0.1, 0.1))
    assert shapes.closest_point(square, (0.5, 0.2)) == pytest.approx((0.5, 0.4))
    assert shapes.closest_point(square, (0.75, 0.52)) == pytest.approx((0.6, 0.52))
    assert shapes.touching(square, (0.5, 0.39), COLLISION_EPS)
    assert not shapes.touching(square, (0.5, 0.3), COLLISION_EPS)


def test_polygon_bounces_like_a_wall():
    square = {"id": "sq", "type": "mirror", "x": 0.5, "y": 0.5,
              "points": [[-0.1, -0.1], [0.1, -0.1], [0.1, 0.1], [-0.1, 0.1]]}
    res = simulate(_level([square]), {"angle_deg": 0, "power": 0.5}, record_trail=True)
    assert res.contacts[0] == ("sq", "bounce")
    # the trail records the position before the box-wall bounce of the step
    assert min(p[0] for p in res.trail) >= -0.5 * DT
    assert max(p[0] for p in res.trail[:100]) < 0.4 - shapes.SEGMENT_HALF_THICKNESS


# --- reflection only when approaching, penetration mirrored out ----------------

def test_reflect_ignores_a_particle_moving_away():
    assert vec.reflect((0.5, 0.0), (1.0, 0.0)) == (0.5, 0.0)
    assert vec.reflect((-0.5, 0.0), (1.0, 0.0)) == pytest.approx((0.5, 0.0))
    assert vec.reflect((0.3, 0.4), (0.0, 0.0)) == (0.3, 0.4)


def test_bounce_mirrors_the_penetration_on_a_flat_face():
    # Head-on shot at a vertical mirror: after the bounce the particle must sit
    # where a continuous collision would put it (mirror image about the contact
    # surface at radius + EPS), not inside the obstacle.
    mirror = {"id": "m", "type": "mirror", "x": 0.5, "y": 0.5, "length": 0.4, "angle_deg": 90}
    res = simulate(_level([mirror]), {"angle_deg": 0, "power": 0.7}, record_trail=True)
    surface = 0.5 - (shapes.radius(mirror) + COLLISION_EPS)
    bounce_step = next(i for i, p in enumerate(res.trail) if p[0] > surface)
    # the recorded point of the contact step is before the mirror-out; the next
    # one is already outside the contact band and moving back
    after = res.trail[bounce_step + 1]
    assert after[0] < surface
    # continuous-collision position: surface − (distance travelled past it) − 1 step back
    x_contact = res.trail[bounce_step][0]
    assert after[0] == pytest.approx(surface - (x_contact - surface) - 0.7 * DT, abs=1e-12)


def test_box_wall_mirrors_the_penetration():
    res = simulate(_level([], launcher=(0.95, 0.5)), {"angle_deg": 0, "power": 0.7}, record_trail=True)
    xs = [p[0] for p in res.trail]
    assert max(xs) <= 1.0 + 0.7 * DT
    i = next(i for i, x in enumerate(xs) if x >= 1.0)
    assert xs[i + 1] == pytest.approx(2.0 - xs[i] - 0.7 * DT, abs=1e-12)


# --- anti-tunnelling ------------------------------------------------------------

def test_no_tunnelling_through_the_thinnest_wall_at_the_speed_limit():
    # Fastest speed the limits allow against the thinnest segment: whatever the
    # offset, the particle never ends up on the other side.
    limit = (shapes.SEGMENT_HALF_THICKNESS + COLLISION_EPS) / DT * 0.999
    wall = {"id": "w", "type": "mirror", "x": 0.5, "y": 0.5, "length": 0.8, "angle_deg": 90}
    for k in range(40):
        start = 0.1 + k * 0.00037
        res = simulate(_level([wall], launcher=(start, 0.5)), {"angle_deg": 0, "power": limit}, record_trail=True)
        assert all(p[0] < 0.5 for p in res.trail), start


def test_check_limits_flags_a_contact_that_could_be_stepped_over():
    thin = {"id": "w", "type": "wall", "x": 0.5, "y": 0.5, "length": 0.4, "r": 0.004}
    level = _level([thin])
    level["param_space"] = {"power": {"type": "range", "min": 0.3, "max": 1.0, "step": 0.1}}
    assert check_limits(level) and "w" in check_limits(level)[0]
    level["obstacles"][0]["r"] = 0.012
    assert check_limits(level) == []


# --- one test per handler ---------------------------------------------------------

def _call(concept_id, obs, pos, vel, params=None, state=None):
    return handler_for(concept_id, obs["type"])(obs, pos, vel, params or {}, state or {})


VERTICAL = {"x": 0.5, "y": 0.5, "length": 0.4, "angle_deg": 90}


def test_wall_and_mirror_reflect():
    for t in ("wall", "mirror"):
        vel, ev = _call("tunnel", dict(VERTICAL, type=t), (0.49, 0.5), (0.5, 0.1))
        assert ev == "bounce" and vel == pytest.approx((-0.5, 0.1))


def test_barrier_passes_at_or_above_the_tunnel_threshold():
    b = dict(VERTICAL, type="barrier", energy_threshold=0.6)
    assert _call("tunnel", b, (0.49, 0.5), (0.6, 0.0)) == ((0.6, 0.0), "pass")
    vel, ev = _call("tunnel", b, (0.49, 0.5), (0.5, 0.0))
    assert ev == "bounce" and vel == pytest.approx((-0.5, 0.0))


def test_splitter_splits_and_reflected_copy_is_mirrored():
    s = dict(VERTICAL, type="splitter")
    assert _call("superposition", s, (0.49, 0.5), (0.5, 0.0)) == ((0.5, 0.0), "split")
    assert reflect_velocity(s, (0.49, 0.5), (0.5, 0.0)) == pytest.approx((-0.5, 0.0))


def test_gates_open_and_close_with_the_tap():
    g = dict(VERTICAL, type="gate")
    ga = dict(VERTICAL, type="gate_anti")
    assert _call("intrication", g, (0.49, 0.5), (0.5, 0.0))[1] == "bounce"
    assert _call("intrication", g, (0.49, 0.5), (0.5, 0.0), state={"tapped": True})[1] == "pass"
    assert _call("intrication", ga, (0.49, 0.5), (0.5, 0.0))[1] == "pass"
    assert _call("intrication", ga, (0.49, 0.5), (0.5, 0.0), state={"tapped": True})[1] == "bounce"


def test_pole_deflects_by_kick_and_flips_with_the_tap():
    p = {"type": "pole", "x": 0.5, "y": 0.5, "r": 0.05, "pole": "+", "kick_deg": 30}
    vel, ev = _call("spin", p, (0.46, 0.5), (0.5, 0.0), params={"spin_up": True})
    assert ev == "deflect" and vec.angle_of(vel) == pytest.approx(30) and vec.mag(vel) == pytest.approx(0.5)
    vel, _ = _call("spin", p, (0.46, 0.5), (0.5, 0.0), params={"spin_up": True}, state={"tapped": True})
    assert vec.angle_of(vel) == pytest.approx(-30)


def test_surface_particle_bounces_wave_crosses_at_180():
    s = dict(VERTICAL, type="surface", interference_offset_deg=180)
    assert _call("dualite", s, (0.49, 0.5), (0.5, 0.0))[1] == "bounce"
    assert _call("dualite", s, (0.49, 0.5), (0.5, 0.0), state={"tapped": True}) == ((0.5, 0.0), "wave")


@pytest.mark.parametrize("concept_id", ALL_CONCEPTS)
def test_registry_plugin_contract(concept_id):
    m = concept(concept_id)
    assert m.CONCEPT == concept_id and m.CODEX_KEY
    assert callable(m.DEFAULT_HANDLER) and all(callable(h) for h in m.HANDLERS.values())
    for d in (1, 2, 3):
        assert m.param_space(d) == m.build(d)["param_space"]
    assert handler_for(concept_id, "unknown-type") in (m.DEFAULT_HANDLER, wall_reflect)


def test_every_shipped_level_respects_the_anti_tunnelling_limits():
    import glob
    import os

    from quarkcosmos_levels import paths
    from quarkcosmos_levels.export.levels import read_level
    files = sorted(glob.glob(os.path.join(str(paths.LEVELS_DIR), "*.json")))
    assert files
    for f in files:
        assert check_limits(read_level(f)) == [], f
