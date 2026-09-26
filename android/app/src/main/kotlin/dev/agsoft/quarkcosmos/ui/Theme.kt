package dev.agsoft.quarkcosmos.ui

import android.content.res.AssetManager
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/** Colour contract — Quantum (art-direction skill), menu side. */
object QC {
    val key = Color(0xFFF472B6)
    val accent = Color(0xFF67E8F9)
    val bg = Color(0xFF0A0612)
    val bgTop = Color(0xFF17061D)
    val bgBottom = Color(0xFF040A14)
    val danger = Color(0xFFFB923C)
    val mid = Color(0xFFC4B5FD)
    val hud = Color(0xFFF7EEF9)
    val hudMuted = Color(0xFFB9A7C9)
    val bezel = Color(0xFF150D22)
    val ink = Color(0xFF1A0820)
    val keyShade = Color(0xFF9C3F74)
    val keyHi = Color(0xFFFAB9DB)
    val keyRim = Color(0xFFF8A9D1)
}

/** OFL fonts of the art direction (same files as the libGDX view, in assets/fonts/). */
class QcType(assets: AssetManager) {
    private val mono = FontFamily(Font(path = "fonts/JetBrainsMono-Medium.ttf", assetManager = assets))
    private val ui = FontFamily(
        Font(path = "fonts/FiraSans-Regular.ttf", assetManager = assets, weight = FontWeight.Normal),
        Font(path = "fonts/FiraSans-SemiBold.ttf", assetManager = assets, weight = FontWeight.SemiBold),
    )

    /** Instrument reading: small, capitals, letter-spaced. */
    val label = TextStyle(fontFamily = mono, fontSize = 10.sp, letterSpacing = 1.4.sp, color = QC.hudMuted)
    val mono13 = TextStyle(fontFamily = mono, fontSize = 13.sp, letterSpacing = 1.sp, color = QC.hud)
    val body = TextStyle(fontFamily = ui, fontSize = 15.sp, lineHeight = 21.sp, color = QC.hud)
    val bodyMuted = body.copy(color = QC.hudMuted)
    val title = TextStyle(fontFamily = ui, fontWeight = FontWeight.SemiBold, fontSize = 22.sp, color = QC.hud)
    val tileTitle = TextStyle(fontFamily = ui, fontWeight = FontWeight.SemiBold, fontSize = 17.sp, color = QC.hud)
    val logo = TextStyle(fontFamily = mono, fontSize = 28.sp, letterSpacing = 5.sp, color = QC.hud)
    val button = TextStyle(fontFamily = mono, fontSize = 14.sp, letterSpacing = 3.sp, color = QC.ink)
}

val LocalType = staticCompositionLocalOf<QcType> { error("QcType absent") }

@Composable
fun rememberQcType(): QcType {
    val assets = LocalContext.current.assets
    return remember(assets) { QcType(assets) }
}
