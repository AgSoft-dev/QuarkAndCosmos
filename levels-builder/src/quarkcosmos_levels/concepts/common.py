"""
Layout helpers shared by the concept modules (flat obstacles defined by their
end points, walls with an opening). See concepts/<concept>.py.
"""
import math


def seg(id_, type_, x1, y1, x2, y2, **extra):
    """Flat obstacle (see shapes.py) defined by its two end points."""
    return dict({
        "id": id_, "type": type_,
        "x": round((x1 + x2) / 2, 4), "y": round((y1 + y2) / 2, 4),
        "length": round(math.hypot(x2 - x1, y2 - y1), 4),
        "angle_deg": round(math.degrees(math.atan2(y2 - y1, x2 - x1)), 2),
    }, **extra)


def barrier(id_, x1, y1, x2, y2, base, amplitude, period, phase):
    """Flat energy barrier whose threshold oscillates (see simulate)."""
    return seg(id_, "barrier", x1, y1, x2, y2, energy_threshold=base,
                threshold_motion={"amplitude": amplitude, "period": period, "phase": phase})


def door_wall(prefix, x, y0, y1):
    """Vertical wall at x with an opening [y0, y1] (for a gate)."""
    return [seg(f"{prefix}Top", "wall", x, -0.05, x, y0), seg(f"{prefix}Bot", "wall", x, y1, x, 1.05)]
