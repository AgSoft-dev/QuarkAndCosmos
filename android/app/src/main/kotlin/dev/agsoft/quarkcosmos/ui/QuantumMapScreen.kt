package dev.agsoft.quarkcosmos.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.requiredWidth

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicText
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
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import dev.agsoft.quarkcosmos.Catalog
import dev.agsoft.quarkcosmos.LevelNode
import kotlinx.coroutines.delay
import kotlin.math.sin

/**
 * Carte du monde Quantique : un chemin sinueux de bas (départ) en haut,
 * un nœud par concept dans l'ordre de CLAUDE.md. Seul l'effet tunnel est
 * jouable dans le POC ; les autres nœuds montrent leur concept, verrouillés.
 */
@Composable
fun QuantumMapScreen(best: Map<String, Int>, onBack: () -> Unit, onPlay: (LevelNode, Int) -> Unit) {
    val type = LocalType.current
    val t by rememberSeconds()
    val nodes = Catalog.quantique
    val total = nodes.mapNotNull { it.levelId }.sumOf { best[it] ?: 0 }
    var notice by remember { mutableStateOf<String?>(null) }
    LaunchedEffect(notice) { if (notice != null) { delay(2500); notice = null } }
    // nœud courant : le premier jouable pas encore à 3 étoiles (Quarky s'y tient)
    val current = nodes.indexOfFirst { it.levelId != null && (best[it.levelId] ?: 0) < Catalog.STARS_PER_LEVEL }.coerceAtLeast(0)

    Box(Modifier.fillMaxSize()) {
        LabBackground()
        Column(Modifier.fillMaxSize()) {
            Header("Monde Quantique", "10⁻¹⁵ m · cavité du détecteur", onBack, trailing = "★ $total/${nodes.size * Catalog.STARS_PER_LEVEL}")
            BoxWithConstraints(Modifier.weight(1f).fillMaxWidth()) {
                val w = maxWidth
                val h = maxHeight
                val step = (h - 80.dp) / (nodes.size - 1)
                fun pos(i: Int): Pair<Dp, Dp> {
                    val x = w / 2 + (w * .26f) * sin(i * 1.15f + .4f)
                    val y = h - 40.dp - step * i
                    return x to y
                }
                // chemin du voyage : fin, pointillé (couche « physique »), plein jusqu'au nœud courant
                Canvas(Modifier.fillMaxSize()) {
                    val pts = nodes.indices.map { i -> pos(i).let { (x, y) -> Offset(x.toPx(), y.toPx()) } }
                    for (i in 0 until pts.lastIndex) {
                        val a = pts[i]
                        val b = pts[i + 1]
                        val mid = Offset((a.x + b.x) / 2 + (b.y - a.y) * .25f, (a.y + b.y) / 2)
                        val p = Path().apply { moveTo(a.x, a.y); quadraticTo(mid.x, mid.y, b.x, b.y) }
                        val reached = i < current
                        drawPath(p, (if (reached) QC.key else QC.hudMuted).copy(alpha = if (reached) .8f else .35f),
                            style = Stroke(if (reached) 2.dp.toPx() else 1.dp.toPx(),
                                pathEffect = if (reached) null else PathEffect.dashPathEffect(floatArrayOf(4.dp.toPx(), 5.dp.toPx()), -t * 12)))
                    }
                }
                nodes.forEachIndexed { i, node ->
                    val (x, y) = pos(i)
                    MapNode(
                        node, i, best[node.levelId ?: ""], i == current, t,
                        Modifier.offset(x - 34.dp, y - 34.dp),
                    ) {
                        if (node.levelId != null) onPlay(node, i)
                        else notice = "${node.title} : ce niveau n’est pas encore jouable dans le POC."
                    }
                }
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
private fun MapNode(node: LevelNode, index: Int, stars: Int?, current: Boolean, t: Float, modifier: Modifier, onClick: () -> Unit) {
    val type = LocalType.current
    val playable = node.levelId != null
    Box(modifier.width(68.dp)) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Box(
                Modifier.size(68.dp)
                    .clickable(role = Role.Button, onClick = onClick)
                    .semantics { contentDescription = "Niveau ${index + 1}, ${node.title}" + if (playable) "" else ", verrouillé" },
                contentAlignment = Alignment.Center,
            ) {
                Canvas(Modifier.fillMaxSize()) {
                    val c = Offset(size.width / 2, size.height / 2)
                    val r = size.minDimension / 2 - 6.dp.toPx()
                    if (playable) {
                        glow(c, r * 1.8f, QC.key, if (current) .22f + .08f * sin(t * 3) else .1f)
                        drawCircle(QC.bezel, r, c)
                        drawCircle(QC.key, r, c, style = Stroke(2.dp.toPx()))
                        // anneau du portail qui tourne
                        val seg = 360f / 3
                        for (j in 0 until 3) drawArc(QC.accent.copy(alpha = .8f), t * 40 + j * seg, seg * .6f, false,
                            topLeft = Offset(c.x - r - 4.dp.toPx(), c.y - r - 4.dp.toPx()),
                            size = androidx.compose.ui.geometry.Size((r + 4.dp.toPx()) * 2, (r + 4.dp.toPx()) * 2),
                            style = Stroke(1.dp.toPx()))
                    } else {
                        drawCircle(QC.bezel.copy(alpha = .85f), r, c)
                        drawCircle(QC.hudMuted.copy(alpha = .35f), r, c, style = Stroke(1.dp.toPx()))
                    }
                }
                if (playable) {
                    if (current) {
                        Canvas(Modifier.size(40.dp)) { drawQuarky(Offset(size.width / 2, size.height / 2), size.minDimension * .38f, t, ghosts = .3f) }
                    } else {
                        BasicText("${index + 1}", style = type.mono13.copy(fontSize = type.title.fontSize))
                    }
                } else {
                    Canvas(Modifier.size(18.dp).alpha(.7f)) { lock(Offset(size.width / 2, size.height / 2), size.width, QC.hudMuted) }
                }
            }
            BasicText(
                node.title, Modifier.requiredWidth(120.dp).offset(0.dp, 2.dp),
                style = (if (playable) type.label.copy(color = QC.hud) else type.label).copy(textAlign = TextAlign.Center),
            )
            if (playable) StarRow(stars ?: 0, 10.dp, Modifier.padding(top = 3.dp))
        }
    }
}

