package dev.agsoft.quarkcosmos

import androidx.compose.ui.graphics.Color

/** Une échelle de l'univers (ordre du jeu : de l'infiniment petit à l'infiniment grand). */
class World(
    val id: String,
    val name: String,
    /** Ordre de grandeur, ex. « 10⁻¹⁵ m ». */
    val magnitude: String,
    /** Ce que l'instrument montre à ce grossissement (DA v2). */
    val instrument: String,
    val key: Color,
    val available: Boolean,
)

/** Un nœud de la carte d'un monde : un concept, un niveau (null = pas encore jouable dans ce POC). */
class LevelNode(
    val concept: String,
    val title: String,
    val levelId: String?,
    val file: String?,
)

object Catalog {
    // Couleurs clés par échelle (skill art-direction).
    val worlds = listOf(
        World("quantique", "Quantique", "10⁻¹⁵ m", "Cavité du détecteur", Color(0xFFF472B6), available = true),
        World("atomique", "Atomique & moléculaire", "10⁻⁹ m", "Nuage d’électrons", Color(0xFFFACC15), available = false),
        World("macro", "Macro", "1 m", "Le labo", Color(0xFF4ADE80), available = false),
        World("spatiale", "Spatiale", "10⁹ m", "Au-delà de la Terre", Color(0xFFA78BFA), available = false),
        World("cosmologique", "Cosmologique", "10²² m", "L’espace-temps courbé", Color(0xFF818CF8), available = false),
    )

    /** Monde Quantique, beta : un niveau par concept, dans l'ordre de CLAUDE.md. */
    val quantique = listOf(
        LevelNode("tunnel", "Effet tunnel", "quantique-tunnel-1", "quantique_tunnel_1.json"),
        LevelNode("superposition", "Superposition", null, null),
        LevelNode("intrication", "Intrication", null, null),
        LevelNode("incertitude", "Incertitude", null, null),
        LevelNode("quantification", "Quantification", null, null),
        LevelNode("spin", "Spin", null, null),
        LevelNode("dualite", "Dualité onde-particule", null, null),
    )

    const val STARS_PER_LEVEL = 3
}
