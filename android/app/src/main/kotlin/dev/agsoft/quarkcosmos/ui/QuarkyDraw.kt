package dev.agsoft.quarkcosmos.ui

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipPath
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.graphics.drawscope.translate
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.sin

private const val TAU = (PI * 2).toFloat()

/** Quarky's membrane: wavy circle (3 harmonics), smoothed into curves. */
private fun blobPath(r: Float, t: Float, wob: Float = 1f): Path {
    val n = 30
    val xs = FloatArray(n)
    val ys = FloatArray(n)
    for (i in 0 until n) {
        val a = i.toFloat() / n * TAU
        val rr = r * (1 + wob * (.035f * sin(3 * a + t * 2.6f) + .024f * sin(5 * a - t * 3.1f) + .014f * sin(2 * a + t * 1.3f)))
        xs[i] = cos(a) * rr
        ys[i] = sin(a) * rr
    }
    return Path().apply {
        for (i in 0..n) {
            val p = i % n
            val q = (i + 1) % n
            val mx = (xs[p] + xs[q]) / 2
            val my = (ys[p] + ys[q]) / 2
            if (i == 0) moveTo(mx, my) else quadraticTo(xs[p], ys[p], mx, my)
        }
        close()
    }
}

private fun flicker(t: Float, i: Int): Float {
    val f = sin(t * 9.1f + i * 3.3f) * sin(t * 3.7f + i * 1.3f)
    return .22f + .34f * max(0f, f) + if (hash(floor(t * 14) + i * 31) > .87f) .35f else 0f
}

/**
 * Quarky v2, flat "B" rendering (port of body()/drawEyes() from
 * design/art-direction-v2/index.html): dark membrane + cut-out lit area (shadow
 * crescent), glowing core, light outline, gummy highlight, big blinking eyes;
 * [ghosts] = phase copies of the Quantum mutation.
 */
fun DrawScope.drawQuarky(center: Offset, r: Float, t: Float, ghosts: Float = .35f, happy: Boolean = false, lookX: Float = 0f) {
    if (ghosts > 0f) {
        for (i in 0 until 3) {
            val off = (if (i == 0) -1f else if (i == 1) 1f else 0f) * r * .42f + sin(t * 5.3f + i * 2.1f) * r * .14f
            val lag = if (i == 2) -r * .6f else 0f
            val a = ghosts * flicker(t, i) * (if (i == 2) .75f else 1f)
            val c = if (i == 1) QC.accent else QC.mid
            translate(center.x + lag, center.y + off) {
                val p = blobPath(r * .96f, t + i * 1.7f)
                drawPath(p, c.copy(alpha = .4f * a))
                drawPath(p, c.copy(alpha = .7f * a), style = Stroke(1.5f * density))
            }
        }
    }
    glow(center, r * 1.9f, QC.key, .16f)
    translate(center.x, center.y) {
        val br = 1 + sin(t * 2.2f) * .022f
        val p = blobPath(r * br, t)
        clipPath(p) {
            drawRect(QC.keyShade, topLeft = Offset(-2 * r, -2 * r), size = Size(4 * r, 4 * r))
            drawCircle(QC.key, radius = r * .98f, center = Offset(-r * .15f, -r * .17f))
            drawCircle(QC.keyHi, radius = r * .3f, center = Offset(r * .08f, r * .42f))
        }
        glow(Offset(r * .08f, r * .38f), r * .7f, QC.keyHi, .3f)
        drawPath(p, QC.keyRim, style = Stroke(1.5f * density))
        drawArc(QC.accent.copy(alpha = .55f), startAngle = -54f, sweepAngle = 80f, useCenter = false,
            topLeft = Offset(-r * .97f, -r * .97f), size = Size(r * 1.94f, r * 1.94f), style = Stroke(1.3f * density))
        rotate(-34f, pivot = Offset(-r * .42f, -r * .5f)) {
            drawOval(Color.White, topLeft = Offset(-r * .64f, -r * .6f), size = Size(r * .44f, r * .2f))
        }
        // eyes
        val ex = r * .34f
        val ey = -r * .1f
        val ew = r * .17f
        val eh = r * .25f
        val lx = lookX * r * .09f
        val blink = if (!happy && (t % 3.9f) < .13f) .14f else 1f
        for (s in intArrayOf(-1, 1)) {
            val cx = s * ex + lx
            if (happy) {
                drawArc(QC.ink, startAngle = 201.6f, sweepAngle = 136.8f, useCenter = false,
                    topLeft = Offset(cx - ew * 1.05f, ey + eh * .35f - ew * 1.05f), size = Size(ew * 2.1f, ew * 2.1f),
                    style = Stroke(max(1f, r * .085f), cap = StrokeCap.Round))
                continue
            }
            val hh = eh * blink
            drawOval(QC.ink, topLeft = Offset(cx - ew, ey - hh), size = Size(ew * 2, hh * 2))
            if (blink > .5f) {
                drawCircle(Color.White.copy(alpha = .95f), radius = ew * .42f, center = Offset(cx + ew * .32f, ey - hh * .36f))
                drawCircle(Color.White.copy(alpha = .6f), radius = ew * .17f, center = Offset(cx - ew * .3f, ey + hh * .38f))
            }
        }
        // smile
        drawArc(QC.ink, startAngle = 32.4f, sweepAngle = 115.2f, useCenter = false,
            topLeft = Offset(lx - r * .12f, r * .24f - r * .12f), size = Size(r * .24f, r * .24f),
            style = Stroke(max(.9f, r * .065f), cap = StrokeCap.Round))
    }
}
