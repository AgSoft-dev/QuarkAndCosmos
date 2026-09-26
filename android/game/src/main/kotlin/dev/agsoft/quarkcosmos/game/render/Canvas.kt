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
 * Petite surcouche de dessin vectoriel (équivalent des helpers Canvas 2D de
 * stage1-art-direction/poc-v2/index.html) : un ShapeRenderer pour les formes
 * pleines, un SpriteBatch pour les halos, le grain et le texte. Elle bascule
 * entre les deux et entre fusion normale / additive sans que l'appelant ait à
 * gérer begin/end. Tout est procédural : aucune image n'est livrée.
 */
class Canvas : Disposable {
    val shapes = ShapeRenderer(5000)
    val batch = SpriteBatch()

    /** Halo radial blanc (alpha qui décroît du centre vers le bord), teinté au dessin. */
    val halo: Texture = radialTexture(128) { d -> val f = max(0f, 1f - d); f * f * (3 - 2 * f) }
    /** Vignette : transparente au centre, noire au bord. */
    val vignette: Texture = radialTexture(256) { d -> min(1f, max(0f, (d - .55f) / .45f)).let { it * it } }
    /** Grain (bruit blanc) en tuile répétée. */
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

    /** Passe en formes pleines (ShapeRenderer). */
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

    /** Passe en sprites (halos, grain, texte). */
    fun sprites(): SpriteBatch {
        if (mode == Mode.SPRITES) return batch
        if (mode == Mode.SHAPES) shapes.end()
        batch.projectionMatrix = camera.combined
        batch.setBlendFunction(GL20.GL_SRC_ALPHA, if (additive) GL20.GL_ONE else GL20.GL_ONE_MINUS_SRC_ALPHA)
        batch.begin()
        mode = Mode.SPRITES
        return batch
    }

    /** Fusion additive (lumière) ou normale. */
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

    // --- formes ----------------------------------------------------------

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

    /** Arc de cercle tracé (épaisseur [w]), angles en radians, sens trigonométrique. */
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

    /** Polygone étoilé autour de (x, y) donné par ses rayons (xs/ys relatifs), rempli en éventail. */
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

    /** Quadrilatère orienté (segment épais) de (x1, y1) à (x2, y2), demi-épaisseur [h]. */
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

    /** Étoile à 5 branches (notation), pleine ou en contour. */
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

    /** Scintillement à 4 branches (paillette d'un Photon). */
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

    /** Halo lumineux doux (additif conseillé), rayon [r]. */
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

        /** Gaussienne de lissage utile aux enveloppes (franges). */
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
