package dev.agsoft.quarkcosmos.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import kotlin.math.sin

/** Accueil : le labo vu à travers l'instrument, Quarky au repos, « Jouer ». */
@Composable
fun WelcomeScreen(onPlay: () -> Unit) {
    val type = LocalType.current
    val t by rememberSeconds()
    Box(Modifier.fillMaxSize()) {
        LabBackground()
        Column(
            Modifier.fillMaxSize().padding(horizontal = 28.dp, vertical = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Spacer(Modifier.weight(1f))
            BasicText("DÉTECTEUR · CAVITÉ 01", style = type.label)
            Spacer(Modifier.height(18.dp))
            // Quarky dans la lunette de l'instrument
            Canvas(Modifier.size(220.dp)) {
                val c = Offset(size.width / 2, size.height / 2)
                val r = size.minDimension / 2
                drawCircle(QC.hudMuted.copy(alpha = .25f), radius = r - 2, center = c, style = Stroke(1.dp.toPx()))
                for (i in 0 until 60) {
                    val a = i / 60f * 2 * Math.PI.toFloat()
                    val l = if (i % 5 == 0) 8.dp.toPx() else 4.dp.toPx()
                    val dx = kotlin.math.cos(a)
                    val dy = kotlin.math.sin(a)
                    drawLine(QC.hudMuted.copy(alpha = .3f), Offset(c.x + dx * (r - 2), c.y + dy * (r - 2)), Offset(c.x + dx * (r - 2 - l), c.y + dy * (r - 2 - l)), 1.dp.toPx())
                }
                // franges nettes derrière Quarky
                for (k in -4..4) {
                    val x = c.x + k * 18.dp.toPx() + sin(t * .4f) * 6.dp.toPx()
                    drawLine(QC.key.copy(alpha = .05f * (1 - kotlin.math.abs(k) / 5f)), Offset(x, c.y - r * .7f), Offset(x, c.y + r * .7f), 7.dp.toPx())
                }
                drawQuarky(Offset(c.x, c.y + sin(t * 1.3f) * 4.dp.toPx()), 46.dp.toPx(), t, ghosts = .45f, lookX = sin(t * .5f))
            }
            Spacer(Modifier.height(28.dp))
            BasicText("QUARK & COSMOS", style = type.logo)
            Spacer(Modifier.height(12.dp))
            Caption("Née au cœur d’une expérience, Quarky part explorer l’univers — de l’infiniment petit à l’infiniment grand.")
            Spacer(Modifier.weight(1f))
            LabButton("Jouer", Modifier.fillMaxWidth(), onClick = onPlay)
            Spacer(Modifier.height(14.dp))
            BasicText("POC · TEST INTERNE", style = type.label)
        }
    }
}
