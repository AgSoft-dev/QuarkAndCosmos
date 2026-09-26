package dev.agsoft.quarkcosmos.physics

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Polygon outline and capsule geometry, same values as levels-builder/tests/test_physics_core.py. */
class ShapesTest {
    private fun obstacle(length: Double? = null, points: DoubleArray? = null) = Obstacle(
        id = "o", type = "mirror", x = 0.5, y = 0.5, r = null, length = length, points = points,
        angleDeg = 0.0, energyThreshold = null, motion = null, thresholdMotion = null,
    )

    private val square = obstacle(points = doubleArrayOf(-0.1, -0.1, 0.1, -0.1, 0.1, 0.1, -0.1, 0.1))

    @Test
    fun capsuleClampsToEndCaps() {
        val s = Shapes()
        s.closestPoint(obstacle(length = 0.2), 0.5, 0.5, 0.9, 0.5)
        assertEquals(0.6, s.cx, 1e-12)
        assertEquals(0.5, s.cy, 1e-12)
    }

    @Test
    fun polygonNearestEdgeAndRadius() {
        val s = Shapes()
        assertEquals(SEGMENT_HALF_THICKNESS, s.radius(square), 0.0)
        assertEquals(Math.hypot(0.1, 0.1), s.extent(square), 1e-12)
        s.closestPoint(square, 0.5, 0.5, 0.5, 0.2)
        assertEquals(0.5, s.cx, 1e-12)
        assertEquals(0.4, s.cy, 1e-12)
        s.closestPoint(square, 0.5, 0.5, 0.75, 0.52)
        assertEquals(0.6, s.cx, 1e-12)
        assertEquals(0.52, s.cy, 1e-12)
        assertTrue(s.touching(square, 0.5, 0.5, 0.5, 0.39, COLLISION_EPS))
        assertFalse(s.touching(square, 0.5, 0.5, 0.5, 0.3, COLLISION_EPS))
    }
}
