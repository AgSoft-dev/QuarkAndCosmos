package dev.agsoft.quarkcosmos.physics

import org.junit.Assert.assertEquals
import org.junit.Test

class ParamGridTest {
    @Test fun rangeMatchesPythonGrid() {
        // validator._grid_values({"type": "range", "min": 0.3, "max": 0.95, "step": 0.05})
        val expected = listOf(0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95)
        assertEquals(expected, ParamGrid.rangeValues(0.3, 0.95, 0.05))
        assertEquals((-12..12).map { it.toDouble() }, ParamGrid.rangeValues(-12.0, 12.0, 1.0))
    }

    @Test fun snapPicksNearest() {
        val spec = ParamSpec.Range(0.3, 0.95, 0.05)
        assertEquals(0.45, ParamGrid.snap(spec, 0.46), 0.0)
        assertEquals(0.95, ParamGrid.snap(spec, 2.0), 0.0)
        assertEquals(0.3, ParamGrid.snap(spec, -1.0), 0.0)
    }

    @Test(expected = UnsupportedObstacle::class)
    fun unportedObstacleIsRefused() {
        Handlers.forType("splitter")
    }
}
