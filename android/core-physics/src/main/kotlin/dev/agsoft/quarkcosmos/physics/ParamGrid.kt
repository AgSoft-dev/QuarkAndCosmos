package dev.agsoft.quarkcosmos.physics

import java.math.BigDecimal
import java.math.RoundingMode

/**
 * Valeurs de réglage atteignables (port de validator._grid_values) : le jeu
 * cale l'angle et la puissance choisis au doigt sur cette grille, la même que
 * celle sur laquelle le validateur a vérifié la solvabilité et les étoiles.
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

    /** round(v, 4) de Python : arrondi correct de la valeur binaire exacte, demi → pair. */
    fun round4(v: Double): Double = BigDecimal(v).setScale(4, RoundingMode.HALF_EVEN).toDouble()

    /** Valeur de la grille la plus proche de [v]. */
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
