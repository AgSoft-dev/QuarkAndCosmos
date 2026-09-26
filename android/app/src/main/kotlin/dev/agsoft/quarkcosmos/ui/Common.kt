package dev.agsoft.quarkcosmos.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import dev.agsoft.quarkcosmos.R
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

/** "Eyepiece" header: back, title, subtitle as an instrument reading, info on the right. */
@Composable
fun Header(title: String, caption: String, onBack: () -> Unit, trailing: String? = null) {
    val type = LocalType.current
    val backLabel = stringResource(R.string.back)
    Row(
        Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            Modifier.size(40.dp).background(QC.bezel.copy(alpha = .9f), CircleShape)
                .border(1.dp, QC.hudMuted.copy(alpha = .45f), CircleShape)
                .clickable(role = Role.Button, onClick = onBack)
                .semantics { contentDescription = backLabel },
            contentAlignment = Alignment.Center,
        ) {
            Canvas(Modifier.size(14.dp)) {
                val s = Stroke(1.8.dp.toPx(), cap = StrokeCap.Round)
                drawPath(Path().apply { moveTo(size.width * .7f, 0f); lineTo(size.width * .2f, size.height / 2); lineTo(size.width * .7f, size.height) }, QC.hud, style = s)
            }
        }
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            BasicText(title, style = type.title)
            BasicText(caption.uppercase(), style = type.label)
        }
        if (trailing != null) BasicText(trailing, style = type.mono13)
    }
}

/** Primary button (flat key colour) or secondary (outline). */
@Composable
fun LabButton(label: String, modifier: Modifier = Modifier, primary: Boolean = true, onClick: () -> Unit) {
    val type = LocalType.current
    val shape = RoundedCornerShape(4.dp)
    Box(
        modifier.height(52.dp)
            .then(if (primary) Modifier.background(QC.key, shape) else Modifier.border(1.dp, QC.hudMuted.copy(alpha = .7f), shape))
            .clickable(role = Role.Button, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        BasicText(label.uppercase(), style = if (primary) type.button else type.button.copy(color = QC.hud))
    }
}

/** Rating stars (filled = earned). */
fun DrawScope.star(c: Offset, r: Float, filled: Boolean, color: Color) {
    val p = Path()
    for (i in 0 until 10) {
        val rr = if (i % 2 == 0) r else r * .45f
        val a = -PI / 2 + i * PI / 5
        val x = c.x + cos(a).toFloat() * rr
        val y = c.y + sin(a).toFloat() * rr
        if (i == 0) p.moveTo(x, y) else p.lineTo(x, y)
    }
    p.close()
    if (filled) drawPath(p, color) else drawPath(p, color, style = Stroke(1.2f * density))
}

@Composable
fun StarRow(stars: Int, size: Dp = 12.dp, modifier: Modifier = Modifier) {
    val description = pluralStringResource(R.plurals.stars_out_of_3, stars, stars)
    Canvas(modifier.width(size * 3 + 8.dp).height(size).semantics { contentDescription = description }) {
        val r = this.size.height / 2
        val step = (this.size.width - 2 * r) / 2
        for (i in 0 until 3) {
            star(Offset(r + i * step, r), r, i < stars, if (i < stars) QC.key else QC.hudMuted.copy(alpha = .6f))
        }
    }
}

/** Drawn padlock (no dependency on Material icons). */
fun DrawScope.lock(c: Offset, s: Float, color: Color) {
    val bw = s * 1.1f
    val bh = s * .8f
    drawArc(color, 180f, 180f, false, topLeft = Offset(c.x - s * .36f, c.y - s * .62f), size = Size(s * .72f, s * .72f), style = Stroke(s * .13f))
    drawRoundRect(color, topLeft = Offset(c.x - bw / 2, c.y - s * .28f), size = Size(bw, bh), cornerRadius = androidx.compose.ui.geometry.CornerRadius(s * .12f))
}

@Composable
fun Caption(text: String, modifier: Modifier = Modifier) {
    BasicText(text, modifier, style = LocalType.current.bodyMuted.copy(textAlign = TextAlign.Center))
}
