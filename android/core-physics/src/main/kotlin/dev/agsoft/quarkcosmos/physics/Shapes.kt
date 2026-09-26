package dev.agsoft.quarkcosmos.physics

/**
 * Géométrie des obstacles (port de engine/shapes.py) : un disque (x, y, r), ou
 * avec `length` un segment plat de centre (x, y) orienté selon `angleDeg`,
 * d'épaisseur 2·r. Les calculs suivent l'ordre des opérations Python pour que
 * les trajectoires restent identiques bit à bit (cf. GoldenTest).
 *
 * Aucune allocation : les résultats sont écrits dans [cx]/[cy] (point le plus
 * proche) — un objet Shapes par simulation, jamais partagé entre threads.
 */
class Shapes {
    var cx = 0.0
        private set
    var cy = 0.0
        private set

    fun radius(o: Obstacle): Double = o.r ?: if (o.length != null) SEGMENT_HALF_THICKNESS else DEFAULT_DISC_RADIUS

    /** Point de l'obstacle (placé en ox, oy) le plus proche de (px, py) → [cx], [cy]. */
    fun closestPoint(o: Obstacle, ox: Double, oy: Double, px: Double, py: Double) {
        val length = o.length
        if (length == null) {
            cx = ox; cy = oy
            return
        }
        val half = length / 2
        val a = Math.toRadians(o.angleDeg)
        val dx = Math.cos(a) * half
        val dy = Math.sin(a) * half
        val ax = ox - dx
        val ay = oy - dy
        val abx = (ox + dx) - ax
        val aby = (oy + dy) - ay
        var t = ((px - ax) * abx + (py - ay) * aby) / (abx * abx + aby * aby)
        t = Math.max(0.0, Math.min(1.0, t))
        cx = ax + abx * t
        cy = ay + aby * t
    }

    fun distance(o: Obstacle, ox: Double, oy: Double, px: Double, py: Double): Double {
        closestPoint(o, ox, oy, px, py)
        return Math.hypot(px - cx, py - cy)
    }

    /** Vrai si (px, py) est à moins de radius + margin de l'obstacle placé en (ox, oy). */
    fun touching(o: Obstacle, ox: Double, oy: Double, px: Double, py: Double, margin: Double): Boolean {
        val reach = radius(o) + margin
        val dx = px - ox
        val dy = py - oy
        val bound = reach + (o.length ?: 0.0) / 2
        if (dx * dx + dy * dy > bound * bound) return false
        return distance(o, ox, oy, px, py) < reach
    }
}
