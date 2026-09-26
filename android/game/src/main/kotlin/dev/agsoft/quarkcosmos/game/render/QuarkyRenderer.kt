package dev.agsoft.quarkcosmos.game.render

import com.badlogic.gdx.graphics.Color
import dev.agsoft.quarkcosmos.game.render.Canvas.Companion.TAU
import dev.agsoft.quarkcosmos.game.render.Canvas.Companion.hash
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/** Expression de Quarky v2 (états procéduraux, skill art-direction). */
enum class Eyes { NORMAL, WIDE, HAPPY, SQUINT }
enum class Mouth { SMILE, O, FLAT }

/** Pose d'un frame : tout ce qui déforme ou anime le corps. */
class QuarkyPose {
    var x = 0f
    var y = 0f
    var r = 13f
    var alpha = 1f
    /** Étirement le long de [ang] (squash & stretch piloté par la vitesse). */
    var stretch = 0f
    var ang = 0f
    var eyes = Eyes.NORMAL
    var mouth = Mouth.SMILE
    /** Regard (-1..1). */
    var lookX = 0f
    var lookY = 0f
    /** Copies de phase fantômes (mutation Quantique), 0..1. */
    var ghosts = 0f
    /** Dissolution (échec), 0..1. */
    var fizzle = 0f
}

/**
 * Quarky v2 en rendu plat « B » : membrane gélatineuse (aplat sombre + zone
 * éclairée découpée par un disque décalé = croissant d'ombre), cœur lumineux,
 * contour clair, reflet gomme, grands yeux. Port de body()/drawEyes()/
 * drawQuarky() de stage1-art-direction/poc-v2/index.html (repère y vers le haut).
 */
class QuarkyRenderer(private val cv: Canvas) {
    private val n = 30
    private val xs = FloatArray(n)
    private val ys = FloatArray(n)
    private val lx = FloatArray(n)
    private val ly = FloatArray(n)
    private val ghostCol = arrayOf(Pal.mid, Pal.accent, Pal.mid)

    fun draw(p: QuarkyPose, t: Float) {
        if (p.alpha <= .004f || p.r < .4f) return
        val fz = p.fizzle
        if (p.ghosts > 0f) {
            val nx = -sin(p.ang)
            val ny = cos(p.ang)
            for (i in 0 until 3) {
                val off = (if (i == 0) -1f else if (i == 1) 1f else 0f) * p.r * .42f + sin(t * 5.3f + i * 2.1f) * p.r * .14f
                val lag = if (i == 2) -p.r * .6f else 0f
                val ga = p.alpha * p.ghosts * flicker(t, i) * (if (i == 2) .75f else 1f) * (1 - fz)
                if (ga > .01f) body(
                    p.x + nx * off + cos(p.ang) * lag, p.y + ny * off + sin(p.ang) * lag,
                    p.r * .96f, t + i * 1.7f, ga, ghostCol[i], ghost = true, p = p, seed = i + 3f,
                )
            }
        }
        val key = if (fz > 0f) Pal.mix(Pal.key, GREY, fz * .8f) else Pal.key
        body(p.x, p.y, p.r, t, p.alpha * (1 - fz * .85f), key, ghost = false, p = p, seed = 0f)
        if (fz > 0f) {
            cv.additive(true)
            for (i in 0 until 16) {
                val an = hash(i * 3.1f) * TAU
                val d = p.r * (.35f + 2.9f * fz) * (.55f + .45f * hash(i + 5.7f))
                val s = (1 - fz) * 1.7f + .25f
                cv.disc(p.x + cos(an) * d, p.y + sin(an) * d + fz * p.r * .4f, s, Pal.keyHi, p.alpha * (1 - fz) * .95f)
            }
            cv.additive(false)
        }
    }

    private fun body(x: Float, y: Float, r: Float, t: Float, a: Float, key: Color, ghost: Boolean, p: QuarkyPose, seed: Float) {
        if (a <= .004f) return
        cv.additive(true)
        cv.glow(x, y, r * 1.9f, key, (if (ghost) .07f else .13f) * a)
        cv.additive(false)

        // Membrane : contour ondulant (3 harmoniques), respiration, étirement.
        val tt = t + seed
        val br = 1 + sin(tt * 2.2f) * .022f
        val sx = (1 + p.stretch) * br
        val sy = 1 / (1 + p.stretch) / br
        val ca = cos(p.ang)
        val sa = sin(p.ang)
        // Zone éclairée = membrane ∩ disque décalé vers la lumière (haut-gauche) :
        // les deux formes sont étoilées depuis le centre, l'intersection prend
        // le plus petit des deux rayons dans chaque direction.
        val dcx = -.15f * r
        val dcy = .17f * r
        val dr = .98f * r
        for (i in 0 until n) {
            val an = i.toFloat() / n * TAU
            val rr = r * (1 + .035f * sin(3 * an + tt * 2.6f) + .024f * sin(5 * an - tt * 3.1f) + .014f * sin(2 * an + tt * 1.3f))
            val ux = cos(an)
            val uy = sin(an)
            val proj = dcx * ux + dcy * uy
            val litR = min(rr, proj + sqrt(max(0f, proj * proj - (dcx * dcx + dcy * dcy) + dr * dr)))
            transform(ux * rr, uy * rr, ca, sa, sx, sy) { tx, ty -> xs[i] = tx; ys[i] = ty }
            transform(ux * litR, uy * litR, ca, sa, sx, sy) { tx, ty -> lx[i] = tx; ly[i] = ty }
        }
        if (ghost) {
            cv.fan(x, y, xs, ys, n, key, .4f * a)
            cv.outline(x, y, xs, ys, n, 1.5f, key, .7f * a)
        } else {
            cv.fan(x, y, xs, ys, n, Pal.keyShade, a)
            cv.fan(x, y, lx, ly, n, key, a)
            // cœur lumineux (seul élément « lumineux » de la matière)
            cv.disc(x + .08f * r, y - .42f * r, .3f * r, Pal.keyHi, a)
            cv.additive(true)
            cv.glow(x + .08f * r, y - .38f * r, .7f * r, Pal.keyHi, .35f * a)
            cv.additive(false)
            cv.outline(x, y, xs, ys, n, 1.5f, Pal.keyRim, a)
            // reflet gomme + liseré froid (rim light)
            cv.arc(x, y, r * .97f, -.45f, .95f, 1.3f, Pal.accent, .55f * a)
            cv.color(Pal.white, a)
            cv.shapes.ellipse(x - .42f * r - .22f * r, y + .5f * r - .1f * r, .44f * r, .2f * r, 34f, 16)
        }
        eyes(x, y, r, tt, a, ghost, p)
    }

    private inline fun transform(px: Float, py: Float, ca: Float, sa: Float, sx: Float, sy: Float, out: (Float, Float) -> Unit) {
        // rotate(-ang) → scale → rotate(ang)
        val u = px * ca + py * sa
        val v = -px * sa + py * ca
        val su = u * sx
        val sv = v * sy
        out(su * ca - sv * sa, su * sa + sv * ca)
    }

    private fun eyes(x: Float, y: Float, r: Float, t: Float, a: Float, ghost: Boolean, p: QuarkyPose) {
        val ox = p.lookX * r * .09f
        val oy = p.lookY * r * .07f
        val ex = r * .34f
        val ey = r * .1f + oy
        val ew = r * .17f
        val eh = r * .25f
        val blink = if (p.eyes == Eyes.NORMAL && (t % 3.9f) < .13f) .14f else 1f
        val ea = if (ghost) a * .55f else a
        for (s in intArrayOf(-1, 1)) {
            val cx = x + s * ex + ox
            val cy = y + ey
            when {
                p.eyes == Eyes.HAPPY && !ghost ->
                    cv.arc(cx, cy - eh * .35f, ew * 1.05f, .12f * PI, .88f * PI, max(1f, r * .085f), Pal.ink, ea)
                ghost -> cv.arc(cx, cy, (ew + eh) / 2, 0f, TAU, max(.8f, r * .05f), Pal.ink, ea)
                else -> {
                    var w = ew
                    var h = eh * blink
                    if (p.eyes == Eyes.WIDE) { w *= 1.14f; h *= 1.2f }
                    if (p.eyes == Eyes.SQUINT) h *= .6f
                    cv.color(Pal.ink, ea)
                    cv.shapes.ellipse(cx - w, cy - h, 2 * w, 2 * h, segments(w))
                    if (blink > .5f) {
                        cv.disc(cx + w * .32f, cy + h * .36f, w * (if (p.eyes == Eyes.WIDE) .36f else .42f), Pal.white, .95f * ea)
                        cv.disc(cx - w * .3f, cy - h * .38f, w * .17f, Pal.white, .6f * ea)
                    }
                }
            }
        }
        if (ghost) return
        val my = y - r * .3f + oy
        val lw = max(.9f, r * .065f)
        when (p.mouth) {
            Mouth.SMILE -> cv.arc(x + ox, my + r * .06f, r * .12f, -.82f * PI, -.18f * PI, lw, Pal.ink, a)
            Mouth.O -> { cv.color(Pal.ink, a); cv.shapes.ellipse(x + ox - r * .07f, my - r * .09f, r * .14f, r * .18f, 12) }
            Mouth.FLAT -> cv.line(x + ox - r * .08f, my, x + ox + r * .08f, my, lw, Pal.ink, a)
        }
    }

    private fun segments(w: Float) = (w * 3).toInt().coerceIn(10, 24)

    companion object {
        private const val PI = Math.PI.toFloat()
        private val GREY: Color = Color.valueOf("7d6a8c")

        fun flicker(t: Float, i: Int): Float {
            val f = sin(t * 9.1f + i * 3.3f) * sin(t * 3.7f + i * 1.3f)
            return .22f + .34f * max(0f, f) + if (hash(kotlin.math.floor(t * 14) + i * 31) > .87f) .35f else 0f
        }
    }
}
