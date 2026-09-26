package dev.agsoft.quarkcosmos.physics

import java.math.BigDecimal
import java.math.RoundingMode

/**
 * Reachable setting values (port of validator._grid_values): the game snaps
 * the angle and power chosen by finger to this grid, the same one on which the
 * validator checked solvability and stars.
 */
object ParamGrid {
    fun rangeValues(min: Double, max: Double, step: Double): List<Double> {
        val out = ArrayList<Double>()
        var v = min
        while (v <= max + 1e-9) {
            out.add(round4(v))
            v += step
        }
        return out
    }

    /** Python's round(v, 4): correct rounding of the exact binary value, half → even. */
    fun round4(v: Double): Double = BigDecimal(v).setScale(4, RoundingMode.HALF_EVEN).toDouble()

    /** Grid value closest to [v]. */
    fun snap(spec: ParamSpec, v: Double): Double {
        var best = Double.NaN
        var bestD = Double.MAX_VALUE
        for (c in spec.values) {
            val d = Math.abs((c as Number).toDouble() - v)
            if (d < bestD) { bestD = d; best = c.toDouble() }
        }
        return best
    }
}
