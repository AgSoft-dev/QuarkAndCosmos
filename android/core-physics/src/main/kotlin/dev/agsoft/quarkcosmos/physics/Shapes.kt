package dev.agsoft.quarkcosmos.physics

/**
 * Obstacle geometry (port of core/shapes.py): a disc (x, y, r); with `length`
 * a capsule/segment centred on (x, y) oriented by `angleDeg`, 2·r thick; with
 * `points` a polygon outline (vertex offsets from (x, y)), 2·r thick.
 * Computations follow Python's order of operations so trajectories stay
 * bit-identical (see GoldenTest).
 *
 * No allocation: results are written to [cx]/[cy] (closest point) — one
 * Shapes object per simulation, never shared between threads.
 */
class Shapes {
    var cx = 0.0
        private set
    var cy = 0.0
        private set

    fun radius(o: Obstacle): Double = o.r ?: if (o.length != null || o.points != null) SEGMENT_HALF_THICKNESS else DEFAULT_DISC_RADIUS

    /** Distance from (x, y) to the farthest point of the skeleton (shapes.extent). */
    fun extent(o: Obstacle): Double {
        val pts = o.points ?: return (o.length ?: 0.0) / 2
        var m = 0.0
        var i = 0
        while (i < pts.size) { m = Math.max(m, Math.hypot(pts[i], pts[i + 1])); i += 2 }
        return m
    }

    /** Closest point of segment [A, B] to (px, py) → [cx], [cy] (shapes._closest_on_segment). */
    private fun closestOnSegment(ax: Double, ay: Double, bx: Double, by: Double, px: Double, py: Double) {
        val abx = bx - ax
        val aby = by - ay
        var t = ((px - ax) * abx + (py - ay) * aby) / (abx * abx + aby * aby)
        t = Math.max(0.0, Math.min(1.0, t))
        cx = ax + abx * t
        cy = ay + aby * t
    }

    /** Point of the obstacle (placed at ox, oy) closest to (px, py) → [cx], [cy]. */
    fun closestPoint(o: Obstacle, ox: Double, oy: Double, px: Double, py: Double) {
        val pts = o.points
        if (pts != null) {
            // closed outline: the nearest edge wins (the first one on a tie)
            val n = pts.size / 2
            var bx = 0.0
            var by = 0.0
            var bd = -1.0
            for (i in 0 until n) {
                val j = (i + 1) % n
                closestOnSegment(ox + pts[2 * i], oy + pts[2 * i + 1], ox + pts[2 * j], oy + pts[2 * j + 1], px, py)
                val d = Math.hypot(px - cx, py - cy)
                if (bd < 0 || d < bd) { bx = cx; by = cy; bd = d }
            }
            cx = bx; cy = by
            return
        }
        val length = o.length
        if (length == null) {
            cx = ox; cy = oy
            return
        }
        val half = length / 2
        val a = Math.toRadians(o.angleDeg)
        val dx = Math.cos(a) * half
        val dy = Math.sin(a) * half
        closestOnSegment(ox - dx, oy - dy, ox + dx, oy + dy, px, py)
    }

    fun distance(o: Obstacle, ox: Double, oy: Double, px: Double, py: Double): Double {
        closestPoint(o, ox, oy, px, py)
        return Math.hypot(px - cx, py - cy)
    }

    /** True if (px, py) is closer than radius + margin to the obstacle placed at (ox, oy). */
    fun touching(o: Obstacle, ox: Double, oy: Double, px: Double, py: Double, margin: Double): Boolean {
        val reach = radius(o) + margin
        val dx = px - ox
        val dy = py - oy
        val bound = reach + extent(o)
        if (dx * dx + dy * dy > bound * bound) return false
        return distance(o, ox, oy, px, py) < reach
    }
}
