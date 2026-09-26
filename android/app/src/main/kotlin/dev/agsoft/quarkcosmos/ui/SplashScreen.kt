package dev.agsoft.quarkcosmos.ui

import android.provider.Settings
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameMillis
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.RoundRect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathMeasure
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipPath
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.graphics.drawscope.withTransform
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.unit.dp
import dev.agsoft.quarkcosmos.R
import kotlin.math.cos
import kotlin.math.exp
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.roundToInt

/**
 * AgSoft studio splash, option A "Struck silver" (design/splash-agsoft/option-a.html,
 * ADR-0009): a silver element tile (47 · Ag · Silver · 107.87) is traced, a sheen
 * crosses it, it is struck like a soft metal (squash, spring, rounder corners,
 * swelling glyphs), then slides left so "Soft" comes out: [Ag]Soft. Fades to the
 * game background. Cold start only; a tap skips it; with animations turned off
 * in the system settings the still logo is shown briefly.
 *
 * Geometry in dp, as in the mockup (tile 128 dp, centred at 47 % of the height).
 */
@Composable
fun AgSoftSplash(onDone: () -> Unit) {
    val context = LocalContext.current
    val density = LocalDensity.current
    val type = LocalType.current
    val measurer = rememberTextMeasurer()
    val name = stringResource(R.string.splash_element_name)
    val tagline = stringResource(R.string.splash_tagline)
    val description = stringResource(R.string.splash_description)
    var t by remember { mutableFloatStateOf(0f) }

    val texts = remember(name, tagline, density) {
        fun sp(v: Float) = with(density) { v.dp.toSp() }
        fun style(family: androidx.compose.ui.text.font.FontFamily, size: Float, weight: FontWeight = FontWeight.Normal, spacing: Float = 0f) =
            TextStyle(fontFamily = family, fontSize = sp(size), fontWeight = weight, letterSpacing = sp(spacing))
        SplashTexts(
            num = { n: Int -> measurer.measure(n.toString(), style(type.mono, 15f)) },
            sym = measurer.measure("Ag", style(type.ui, 60f, FontWeight.SemiBold)),
            name = measurer.measure(name, style(type.ui, 12.5f)),
            mass = measurer.measure("107.87", style(type.mono, 10.5f)),
            soft = measurer.measure("Soft", style(type.ui, 54f)),
            tag = measurer.measure(tagline, style(type.mono, 11f, spacing = 1.6f)),
        )
    }
    val nums = remember(texts) { Array(48) { texts.num(it) } }

    LaunchedEffect(Unit) {
        val scale = Settings.Global.getFloat(context.contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f)
        if (scale == 0f) {
            t = STILL
            val start = withFrameMillis { it }
            while (withFrameMillis { it } - start < 1200) Unit
        } else {
            val start = withFrameMillis { it }
            while (t < DURATION) t = min(DURATION, (withFrameMillis { it } - start).toFloat())
        }
        onDone()
    }

    Canvas(
        Modifier.fillMaxSize()
            .semantics { contentDescription = description }
            .pointerInput(Unit) { detectTapGestures { onDone() } },
    ) { drawSplash(t, texts, nums) }
}

private class SplashTexts(
    val num: (Int) -> TextLayoutResult,
    val sym: TextLayoutResult,
    val name: TextLayoutResult,
    val mass: TextLayoutResult,
    val soft: TextLayoutResult,
    val tag: TextLayoutResult,
)

private const val DURATION = 2450f
private const val STILL = 2000f
private const val S = 128f
private const val SC1 = .9f

private val SilverLo = Color(0xFF9AA1AD)
private val Silver = Color(0xFFC7CCD4)
private val SilverFacet = Color(0xFFD3D8DF)
private val SilverHi = Color(0xFFE4E7EC)
private val OutlineCol = Color(0xFFEEF1F5)
private val TileInk = Color(0xFF1A1426)
private val BloomCol = Color(0xFFDFE3EA)

private fun seg(t: Float, a: Float, b: Float) = ((t - a) / (b - a)).coerceIn(0f, 1f)
private fun lerp(a: Float, b: Float, p: Float) = a + (b - a) * p
private fun easeOut(p: Float) = 1 - (1 - p).pow(3)
private fun easeInOut(p: Float) = if (p < .5f) 4 * p * p * p else 1 - (-2 * p + 2).pow(3) / 2

private fun DrawScope.drawSplash(t: Float, tx: SplashTexts, nums: Array<TextLayoutResult>) {
    val k = density // px per dp
    val cx = size.width / 2
    val cy = size.height * .474f

    // C-style background and a single soft bloom behind the matter
    drawRect(Brush.radialGradient(listOf(Color(0xFF120B1D), QC.bg), Offset(cx, cy), size.maxDimension * .65f))
    val pFill = easeOut(seg(t, 260f, 620f))
    val s = t - 1060f
    val strike = when {
        s <= 0 -> 0f
        s < 70 -> easeOut(s / 70f)
        else -> exp(-(s - 70f) / 120f) * cos((s - 70f) / 38f)
    }
    val bloomA = (pFill * (1 + .5f * max(0f, strike))).coerceAtMost(1.5f)
    drawCircle(
        Brush.radialGradient(
            0f to BloomCol.copy(alpha = .20f * bloomA),
            .55f to BloomCol.copy(alpha = .05f * bloomA),
            1f to Color.Transparent,
            center = Offset(cx, cy), radius = 160 * k,
        ),
        160 * k, Offset(cx, cy),
    )

    // layout of the final [Ag]Soft lock-up
    val ts = S * SC1 * k
    val gap = 8 * k
    val total = ts + gap + tx.soft.size.width
    val x0 = cx - S / 2 * k
    val y0 = cy - S / 2 * k
    val x1 = cx - total / 2
    val y1 = cy - ts / 2
    val softX = x1 + ts + gap
    val base = y1 + 83 * SC1 * k

    val pm = easeInOut(seg(t, 1380f, 1780f))
    val sc = lerp(1f, SC1, pm)
    val tileX = lerp(x0, x1, pm)
    val tileY = lerp(y0, y1, pm)
    val soft = easeOut(seg(t, 1060f, 1380f))
    val rx = (10 + 8 * soft) * k

    withTransform({
        translate(tileX, tileY)
        scale(sc, sc, Offset.Zero)
        scale(1 + .07f * strike, 1 - .09f * strike, Offset(64 * k, 128 * k))
    }) {
        val tileRect = RoundRect(0f, 0f, S * k, S * k, CornerRadius(rx))
        val clip = Path().apply { addRoundRect(tileRect) }
        clipPath(clip) {
            if (pFill > 0f) {
                drawRect(SilverLo, alpha = pFill)
                drawRoundRect(Silver, Offset(-6 * k, -6 * k), Size(S * k, S * k), CornerRadius((14 + 8 * soft) * k), alpha = pFill)
                drawPath(Path().apply { moveTo(0f, 0f); lineTo(86 * k, 0f); lineTo(0f, 86 * k); close() }, SilverFacet, alpha = pFill)
            }
            // metallic sheen sweep, with a hair-thin pink/cyan fringe (decoration only)
            val pS = seg(t, 620f, 1040f)
            if (pS > 0f && pS < 1f) {
                withTransform({
                    translate((-60 + (S + 120) * easeInOut(pS)) * k, 0f)
                    rotate(18f, Offset(0f, 64 * k))
                }) {
                    drawRect(
                        Brush.horizontalGradient(
                            0f to Color.White.copy(alpha = 0f), .5f to Color.White.copy(alpha = .8f), 1f to Color.White.copy(alpha = 0f),
                            startX = -22 * k, endX = 22 * k,
                        ),
                        Offset(-22 * k, -80 * k), Size(44 * k, 300 * k),
                    )
                    drawLine(QC.key.copy(alpha = .7f), Offset(-22 * k, -80 * k), Offset(-22 * k, 220 * k), .75f * k)
                    drawLine(QC.accent.copy(alpha = .7f), Offset(22 * k, -80 * k), Offset(22 * k, 220 * k), .75f * k)
                }
            }
        }
        // outline traced like an instrument calibrating
        val pDraw = easeInOut(seg(t, 0f, 420f))
        if (pDraw > 0f) {
            val m = PathMeasure().apply { setPath(clip, false) }
            val part = Path()
            m.getSegment(0f, m.length * pDraw, part, true)
            drawPath(part, OutlineCol, style = Stroke(1.5f * k))
        }
        drawCircle(Color.White, 2 * k, Offset(8.5f * k, 8.5f * k), alpha = pFill)
        // atomic number counting up to 47
        val numA = seg(t, 40f, 160f)
        if (numA > 0f) {
            val n = nums[(47 * easeOut(seg(t, 40f, 470f))).roundToInt().coerceIn(0, 47)]
            drawText(n, TileInk, Offset(13 * k, 27 * k - n.firstBaseline), alpha = numA)
        }
        val pSym = easeOut(seg(t, 320f, 600f))
        if (pSym > 0f) {
            val o = Offset(64 * k - tx.sym.size.width / 2, 83 * k - tx.sym.firstBaseline + 6 * k * (1 - pSym))
            drawText(tx.sym, TileInk, o, alpha = pSym)
            // the glyphs swell and soften under the hammer
            if (soft > 0f) drawText(tx.sym, TileInk, o, alpha = pSym, drawStyle = Stroke(2.6f * k * soft, join = StrokeJoin.Round))
        }
        val pMeta = seg(t, 440f, 720f)
        if (pMeta > 0f) {
            drawText(tx.name, TileInk, Offset(64 * k - tx.name.size.width / 2, 103 * k - tx.name.firstBaseline), alpha = pMeta)
            drawText(tx.mass, TileInk, Offset(64 * k - tx.mass.size.width / 2, 118 * k - tx.mass.firstBaseline), alpha = pMeta)
        }
    }

    // "Soft" slides out from behind the tile
    val pr = easeOut(seg(t, 1480f, 1820f))
    if (pr > 0f) {
        clipRect(left = tileX + S * k * sc + 1) {
            val o = Offset(softX - 40 * k * (1 - pr), base - tx.soft.firstBaseline)
            drawText(tx.soft, SilverHi, o, alpha = pr)
            val w = 1.5f * k * easeOut(seg(t, 1640f, 1900f))
            if (w > 0f) drawText(tx.soft, SilverHi, o, alpha = pr, drawStyle = Stroke(w, join = StrokeJoin.Round))
        }
    }
    val tagA = easeOut(seg(t, 1700f, 1950f))
    if (tagA > 0f) drawText(tx.tag, QC.hudMuted, Offset(cx - tx.tag.size.width / 2, cy + 102 * k - tx.tag.firstBaseline), alpha = tagA)

    // hand-over to the game's background
    val fade = easeInOut(seg(t, 2100f, 2450f))
    if (fade > 0f) drawRect(QC.bg, alpha = fade)
}
