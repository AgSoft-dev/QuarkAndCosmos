package dev.agsoft.quarkcosmos.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicText
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import dev.agsoft.quarkcosmos.Catalog
import dev.agsoft.quarkcosmos.R
import dev.agsoft.quarkcosmos.World
import kotlinx.coroutines.delay
import kotlin.math.cos
import kotlin.math.sin

/** The 5 scales, from the infinitely small to the infinitely large; only Quantum is open in the POC. */
@Composable
fun WorldsScreen(best: Map<String, Int>, onBack: () -> Unit, onOpen: (World) -> Unit) {
    val type = LocalType.current
    val t by rememberSeconds()
    var notice by remember { mutableStateOf<String?>(null) }
    LaunchedEffect(notice) { if (notice != null) { delay(2500); notice = null } }
    Box(Modifier.fillMaxSize()) {
        LabBackground()
        Column(Modifier.fillMaxSize()) {
            Header(stringResource(R.string.worlds_title), stringResource(R.string.worlds_caption), onBack)
            Column(
                Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 16.dp),
            ) {
                Catalog.worlds.forEachIndexed { i, world ->
                    val ids = if (world.id == "quantique") Catalog.quantique.mapNotNull { it.levelId } else emptyList()
                    val done = ids.count { it in best }
                    val stars = ids.sumOf { best[it] ?: 0 }
                    val locked = stringResource(R.string.worlds_locked, stringResource(world.name))
                    WorldTile(world, i, t, done, stars) {
                        if (world.available) onOpen(world) else notice = locked
                    }
                    if (i < Catalog.worlds.lastIndex) {
                        // journey thread between two scales ("physics" layer: thin dotted line)
                        Canvas(Modifier.fillMaxWidth().height(18.dp)) {
                            val x = 44.dp.toPx()
                            drawLine(QC.hudMuted.copy(alpha = .4f), Offset(x, 0f), Offset(x, size.height), 1.dp.toPx(),
                                pathEffect = PathEffect.dashPathEffect(floatArrayOf(3.dp.toPx(), 4.dp.toPx())))
                        }
                    }
                }
                Spacer(Modifier.height(24.dp))
            }
            notice?.let {
                Box(Modifier.fillMaxWidth().padding(16.dp).background(QC.bezel.copy(alpha = .95f), RoundedCornerShape(4.dp))
                    .border(1.dp, QC.hudMuted.copy(alpha = .3f), RoundedCornerShape(4.dp)).padding(14.dp)) {
                    BasicText(it, style = type.body)
                }
            }
        }
    }
}

@Composable
private fun WorldTile(world: World, index: Int, t: Float, done: Int, stars: Int, onClick: () -> Unit) {
    val type = LocalType.current
    val shape = RoundedCornerShape(6.dp)
    Row(
        Modifier.fillMaxWidth()
            .alpha(if (world.available) 1f else .5f)
            .background(QC.bezel.copy(alpha = .85f), shape)
            .border(1.dp, world.key.copy(alpha = if (world.available) .6f else .25f), shape)
            .clickable(role = Role.Button, onClick = onClick)
            .padding(12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Canvas(Modifier.size(56.dp)) { emblem(world, index, t) }
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            BasicText("${index + 1} · ${world.magnitude}".uppercase(), style = type.label.copy(color = world.key))
            BasicText(stringResource(world.name), style = type.tileTitle)
            BasicText(stringResource(world.instrument), style = type.bodyMuted)
        }
        Column(horizontalAlignment = Alignment.End) {
            if (world.available) {
                BasicText("★ $stars/${Catalog.quantique.size * Catalog.STARS_PER_LEVEL}", style = type.mono13)
                BasicText(stringResource(R.string.worlds_levels_done, done, Catalog.quantique.size), style = type.label)
            } else {
                Canvas(Modifier.size(18.dp)) { lock(Offset(size.width / 2, size.height / 2), size.width, QC.hudMuted) }
                BasicText(stringResource(R.string.worlds_soon), style = type.label)
            }
        }
    }
}

/** Emblem of each scale: what the instrument shows there, in flat fills of the key colour. */
private fun DrawScope.emblem(world: World, index: Int, t: Float) {
    val c = Offset(size.width / 2, size.height / 2)
    val r = size.minDimension / 2
    val k = world.key
    glow(c, r * 1.1f, k, .18f)
    val s = Stroke(1.5f * density)
    when (index) {
        0 -> { // Quantum: Quarky and its phase copies
            drawQuarky(c, r * .55f, t, ghosts = .4f)
        }
        1 -> { // Atomic: nucleus + orbits
            drawCircle(k, r * .18f, c)
            for (i in 0 until 3) rotate(i * 60f + t * 20, c) {
                drawOval(k.copy(alpha = .8f), topLeft = Offset(c.x - r * .85f, c.y - r * .32f), size = Size(r * 1.7f, r * .64f), style = s)
            }
            val a = t * 2.4f
            drawCircle(Color(0xFF67E8F9), r * .09f, Offset(c.x + cos(a) * r * .85f, c.y + sin(a) * r * .32f))
        }
        2 -> { // Macro: mirror and reflected ray
            drawLine(k, Offset(c.x - r * .7f, c.y + r * .5f), Offset(c.x + r * .7f, c.y + r * .5f), 4f * density)
            drawLine(k.copy(alpha = .8f), Offset(c.x - r * .6f, c.y - r * .6f), Offset(c.x, c.y + r * .45f), 1.5f * density)
            drawLine(k.copy(alpha = .8f), Offset(c.x, c.y + r * .45f), Offset(c.x + r * .6f, c.y - r * .6f), 1.5f * density)
        }
        3 -> { // Space: ringed planet
            drawCircle(k, r * .42f, c)
            drawCircle(Color.Black.copy(alpha = .25f), r * .42f, Offset(c.x + r * .12f, c.y + r * .1f))
            drawOval(k.copy(alpha = .9f), topLeft = Offset(c.x - r * .85f, c.y - r * .2f), size = Size(r * 1.7f, r * .4f), style = s)
        }
        else -> { // Cosmological: black hole and ring of bent light
            drawCircle(k.copy(alpha = .9f), r * .62f, c, style = Stroke(2.5f * density))
            drawCircle(Color.Black, r * .45f, c)
        }
    }
}
