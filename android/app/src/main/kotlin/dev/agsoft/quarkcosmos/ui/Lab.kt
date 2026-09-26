package dev.agsoft.quarkcosmos.ui

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.core.animateFloat
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.State
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import kotlin.math.cos
import kotlin.math.floor
import kotlin.math.sin

/** Temps qui s'écoule en continu (secondes), pour les animations procédurales. */
@Composable
fun rememberSeconds(): State<Float> {
    val tr = rememberInfiniteTransition(label = "clock")
    return tr.animateFloat(
        initialValue = 0f,
        targetValue = 3600f,
        animationSpec = infiniteRepeatable(tween(3_600_000, easing = LinearEasing), RepeatMode.Restart),
        label = "seconds",
    )
}

fun hash(n: Float): Float {
    val s = sin(n * 127.1f + 311.7f) * 43758.5453f
    return s - floor(s)
}

/** Halo doux (dégradé radial vers transparent). */
fun DrawScope.glow(c: Offset, r: Float, color: Color, alpha: Float) {
    if (r <= 0f || alpha <= 0f) return
    drawCircle(
        Brush.radialGradient(listOf(color.copy(alpha = alpha), color.copy(alpha = 0f)), center = c, radius = r),
        radius = r, center = c,
    )
}

/**
 * Fond « C » des menus : gradient profond, bokeh lointain, brume, poussière
 * (parallaxe lente), toujours sous la matière (luminance ≤ 20 %).
 */
@Composable
fun LabBackground(key: Color = QC.key, modifier: Modifier = Modifier.fillMaxSize()) {
    val t by rememberSeconds()
    Canvas(modifier) {
        drawRect(Brush.verticalGradient(listOf(QC.bgTop, QC.bg, QC.bgBottom)))
        val w = size.width
        val h = size.height
        glow(Offset(w * .8f, h * .2f), w * .9f, key, .07f)
        glow(Offset(w * .1f, h * .85f), w * .7f, QC.accent, .035f)
        for (i in 0 until 12) {
            val x = hash(i * 1.7f) * w + sin(t * .1f * (.6f + hash(i + 11f)) + i) * 24
            val y = hash(i * 2.9f + 3) * h + cos(t * .08f + i) * 20
            glow(Offset(x, y), (22f + 40 * hash(i * 5.3f)) * density, if (hash(i + 11f) > .5f) QC.accent else key, .05f)
        }
        for (i in 0 until 5) {
            glow(Offset(hash(i * 3.3f + 1) * w + sin(t * .12f + i) * 60, hash(i * 4.1f + 2) * h), (120f + 90 * hash(i * 2.2f)) * density, key, .04f)
        }
        for (i in 0 until 30) {
            val x = ((hash(i * 9.1f) * w + t * 6 * hash(i * 1.3f)) % w + w) % w
            val y = ((hash(i * 4.7f + 5) * h - t * 9 * hash(i * 1.3f)) % h + h) % h
            drawCircle(QC.hud.copy(alpha = .1f), radius = (.5f + .8f * hash(i * 3.9f)) * density, center = Offset(x, y))
        }
    }
}
