package dev.agsoft.quarkcosmos.game.render

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.graphics.Camera
import com.badlogic.gdx.graphics.Color
import com.badlogic.gdx.graphics.GL20
import com.badlogic.gdx.graphics.Pixmap
import com.badlogic.gdx.graphics.Texture
import com.badlogic.gdx.graphics.g2d.SpriteBatch
import com.badlogic.gdx.graphics.glutils.ShapeRenderer
import com.badlogic.gdx.utils.Disposable
import kotlin.math.cos
import kotlin.math.exp
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Thin vector drawing layer (equivalent of the Canvas 2D helpers of
 * design/art-direction-v2/index.html): a ShapeRenderer for filled shapes, a
 * SpriteBatch for halos, grain and text. It switches between the two, and
 * between normal / additive blending, without the caller handling
 * begin/end. Everything is procedural: no image is shipped.
 */
class Canvas : Disposable {
    val shapes = ShapeRenderer(5000)
    val batch = SpriteBatch()

    /** White radial halo (alpha falling from the centre to the edge), tinted when drawn. */
    val halo: Texture = radialTexture(128) { d -> val f = max(0f, 1f - d); f * f * (3 - 2 * f) }
    /** Vignette: transparent in the centre, black at the edge. */
    val vignette: Texture = radialTexture(256) { d -> min(1f, max(0f, (d - .55f) / .45f)).let { it * it } }
    /** Grain (white noise) as a repeated tile. */
    val grain: Texture = noiseTexture(128)

    private enum class Mode { NONE, SHAPES, SPRITES }

    private var mode = Mode.NONE
    private var additive = false
    private lateinit var camera: Camera

    fun begin(cam: Camera) {
        camera = cam
        additive = false
        mode = Mode.NONE
    }

    fun end() {
        when (mode) {
            Mode.SHAPES -> shapes.end()
            Mode.SPRITES -> batch.end()
            Mode.NONE -> Unit
        }
        mode = Mode.NONE
    }

    /** Switch to filled shapes (ShapeRenderer). */
    fun shapes(): ShapeRenderer {
        if (mode == Mode.SHAPES) return shapes
        if (mode == Mode.SPRITES) batch.end()
        Gdx.gl.glEnable(GL20.GL_BLEND)
        Gdx.gl.glBlendFunc(GL20.GL_SRC_ALPHA, if (additive) GL20.GL_ONE else GL20.GL_ONE_MINUS_SRC_ALPHA)
        shapes.projectionMatrix = camera.combined
        shapes.begin(ShapeRenderer.ShapeType.Filled)
        mode = Mode.SHAPES
        return shapes
    }

    /** Switch to sprites (halos, grain, text). */
    fun sprites(): SpriteBatch {
        if (mode == Mode.SPRITES) return batch
        if (mode == Mode.SHAPES) shapes.end()
        batch.projectionMatrix = camera.combined
        batch.setBlendFunction(GL20.GL_SRC_ALPHA, if (additive) GL20.GL_ONE else GL20.GL_ONE_MINUS_SRC_ALPHA)
        batch.begin()
        mode = Mode.SPRITES
        return batch
    }

    /** Additive (light) or normal blending. */
    fun additive(on: Boolean) {
        if (on == additive) return
        val was = mode
        end()
        additive = on
        when (was) {
            Mode.SHAPES -> shapes()
            Mode.SPRITES -> sprites()
            Mode.NONE -> Unit
        }
    }

    // --- shapes ----------------------------------------------------------

    fun color(c: Color, a: Float = 1f) = shapes().setColor(c.r, c.g, c.b, c.a * a)

    fun disc(x: Float, y: Float, r: Float, c: Color, a: Float = 1f) {
        if (r <= 0f || a <= 0.003f) return
        color(c, a)
        shapes.circle(x, y, r, segments(r))
    }

    fun line(x1: Float, y1: Float, x2: Float, y2: Float, w: Float, c: Color, a: Float = 1f) {
        if (a <= 0.003f) return
        color(c, a)
        shapes.rectLine(x1, y1, x2, y2, w)
    }

    /** Stroked circular arc (thickness [w]), angles in radians, counter-clockwise. */
    fun arc(x: Float, y: Float, r: Float, a0: Float, a1: Float, w: Float, c: Color, a: Float = 1f) {
        if (a <= 0.003f || r <= 0f) return
        color(c, a)
        val n = max(2, ((a1 - a0) * r / 3f).toInt())
        val ri = r - w / 2
        val ro = r + w / 2
        var px = cos(a0)
        var py = sin(a0)
        for (i in 1..n) {
            val ang = a0 + (a1 - a0) * i / n
            val qx = cos(ang)
            val qy = sin(ang)
            shapes.triangle(x + px * ri, y + py * ri, x + px * ro, y + py * ro, x + qx * ro, y + qy * ro)
            shapes.triangle(x + px * ri, y + py * ri, x + qx * ro, y + qy * ro, x + qx * ri, y + qy * ri)
            px = qx; py = qy
        }
    }

    fun ring(x: Float, y: Float, r: Float, w: Float, c: Color, a: Float = 1f) =
        arc(x, y, r, 0f, TAU, w, c, a)

    /** Star-shaped polygon around (x, y) given by its radii (relative xs/ys), filled as a fan. */
    fun fan(x: Float, y: Float, xs: FloatArray, ys: FloatArray, n: Int, c: Color, a: Float = 1f) {
        if (a <= 0.003f) return
        color(c, a)
        for (i in 0 until n) {
            val j = (i + 1) % n
            shapes.triangle(x, y, x + xs[i], y + ys[i], x + xs[j], y + ys[j])
        }
    }

    fun outline(x: Float, y: Float, xs: FloatArray, ys: FloatArray, n: Int, w: Float, c: Color, a: Float = 1f) {
        if (a <= 0.003f) return
        color(c, a)
        for (i in 0 until n) {
            val j = (i + 1) % n
            shapes.rectLine(x + xs[i], y + ys[i], x + xs[j], y + ys[j], w)
        }
    }

    /** Oriented quad (thick segment) from (x1, y1) to (x2, y2), half-thickness [h]. */
    fun slab(x1: Float, y1: Float, x2: Float, y2: Float, h: Float, c: Color, a: Float = 1f) {
        if (a <= 0.003f) return
        val dx = x2 - x1
        val dy = y2 - y1
        val l = sqrt(dx * dx + dy * dy).coerceAtLeast(1e-4f)
        val nx = -dy / l * h
        val ny = dx / l * h
        color(c, a)
        shapes.triangle(x1 + nx, y1 + ny, x2 + nx, y2 + ny, x2 - nx, y2 - ny)
        shapes.triangle(x1 + nx, y1 + ny, x2 - nx, y2 - ny, x1 - nx, y1 - ny)
    }

    /** 5-pointed star (rating), filled or outlined. */
    fun star(x: Float, y: Float, r: Float, filled: Boolean, c: Color, a: Float = 1f) {
        val n = 10
        for (i in 0 until n) {
            val rr = if (i % 2 == 0) r else r * .45f
            val ang = PI_2 + i * TAU / n
            starX[i] = cos(ang) * rr
            starY[i] = sin(ang) * rr
        }
        if (filled) fan(x, y, starX, starY, n, c, a) else outline(x, y, starX, starY, n, 1.4f, c, a)
    }

    /** 4-pointed glint (a Photon's sparkle). */
    fun glint(x: Float, y: Float, s: Float, c: Color, a: Float) {
        if (s <= .05f || a <= 0f) return
        color(c, a)
        val t = s * .22f
        shapes.triangle(x, y + s, x - t, y, x + t, y)
        shapes.triangle(x, y - s, x - t, y, x + t, y)
        shapes.triangle(x + s, y, x, y - t, x, y + t)
        shapes.triangle(x - s, y, x, y - t, x, y + t)
    }

    // --- sprites ---------------------------------------------------------

    /** Soft glow (additive recommended), radius [r]. */
    fun glow(x: Float, y: Float, r: Float, c: Color, a: Float) {
        if (a <= 0.003f || r <= 0f) return
        val b = sprites()
        b.setColor(c.r, c.g, c.b, min(1f, a))
        b.draw(halo, x - r, y - r, 2 * r, 2 * r)
    }

    override fun dispose() {
        shapes.dispose()
        batch.dispose()
        halo.dispose()
        vignette.dispose()
        grain.dispose()
    }

    private val starX = FloatArray(10)
    private val starY = FloatArray(10)

    companion object {
        const val TAU = (Math.PI * 2).toFloat()
        const val PI_2 = (Math.PI / 2).toFloat()

        fun segments(r: Float) = (r * 1.2f).toInt().coerceIn(12, 64)

        fun hash(n: Float): Float {
            val s = sin(n * 127.1f + 311.7f) * 43758.5453f
            return s - kotlin.math.floor(s)
        }

        /** Smoothing gaussian, handy for envelopes (fringes). */
        fun gauss(x: Float) = exp(-x * x)

        private fun noiseTexture(size: Int): Texture {
            val p = Pixmap(size, size, Pixmap.Format.RGBA8888)
            val rnd = java.util.Random(7)
            for (y in 0 until size) for (x in 0 until size) {
                val v = rnd.nextInt(256)
                p.drawPixel(x, y, (v shl 24) or (v shl 16) or (v shl 8) or 0xff)
            }
            return Texture(p).also {
                it.setWrap(Texture.TextureWrap.Repeat, Texture.TextureWrap.Repeat)
                p.dispose()
            }
        }

        private fun radialTexture(size: Int, alpha: (Float) -> Float): Texture {
            val p = Pixmap(size, size, Pixmap.Format.RGBA8888)
            val c = (size - 1) / 2f
            for (y in 0 until size) for (x in 0 until size) {
                val d = sqrt((x - c) * (x - c) + (y - c) * (y - c)) / c
                val a = (alpha(d.coerceAtMost(1f)) * 255).toInt().coerceIn(0, 255)
                p.drawPixel(x, y, (0xffffff00.toInt()) or a)
            }
            return Texture(p).also {
                it.setFilter(Texture.TextureFilter.Linear, Texture.TextureFilter.Linear)
                p.dispose()
            }
        }
    }
}
