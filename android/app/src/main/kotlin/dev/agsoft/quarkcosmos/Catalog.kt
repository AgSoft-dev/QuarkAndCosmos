package dev.agsoft.quarkcosmos

import androidx.annotation.StringRes
import androidx.compose.ui.graphics.Color

/** A scale of the universe (game order: from the infinitely small to the infinitely large). */
class World(
    val id: String,
    @StringRes val name: Int,
    /** Order of magnitude, e.g. "10⁻¹⁵ m" (same in every language). */
    val magnitude: String,
    /** What the instrument shows at this magnification (art direction v2). */
    @StringRes val instrument: Int,
    val key: Color,
    val available: Boolean,
)

/** A node of a world map: one concept, one level (null = not playable yet in this POC). */
class LevelNode(
    val concept: String,
    @StringRes val title: Int,
    val levelId: String?,
    val file: String?,
)

object Catalog {
    // Key colours per scale (art-direction skill).
    val worlds = listOf(
        World("quantique", R.string.world_quantique, "10⁻¹⁵ m", R.string.world_quantique_instrument, Color(0xFFF472B6), available = true),
        World("atomique", R.string.world_atomique, "10⁻⁹ m", R.string.world_atomique_instrument, Color(0xFFFACC15), available = false),
        World("macro", R.string.world_macro, "1 m", R.string.world_macro_instrument, Color(0xFF4ADE80), available = false),
        World("spatiale", R.string.world_spatiale, "10⁹ m", R.string.world_spatiale_instrument, Color(0xFFA78BFA), available = false),
        World("cosmologique", R.string.world_cosmologique, "10²² m", R.string.world_cosmologique_instrument, Color(0xFF818CF8), available = false),
    )

    /** Quantum world, beta: one level per concept, in the order of the gameplay-mechanics skill. */
    val quantique = listOf(
        LevelNode("tunnel", R.string.concept_tunnel, "quantique-tunnel-1", "quantique_tunnel_1.json"),
        LevelNode("superposition", R.string.concept_superposition, null, null),
        LevelNode("intrication", R.string.concept_intrication, null, null),
        LevelNode("incertitude", R.string.concept_incertitude, null, null),
        LevelNode("quantification", R.string.concept_quantification, null, null),
        LevelNode("spin", R.string.concept_spin, null, null),
        LevelNode("dualite", R.string.concept_dualite, null, null),
    )

    const val STARS_PER_LEVEL = 3
}
