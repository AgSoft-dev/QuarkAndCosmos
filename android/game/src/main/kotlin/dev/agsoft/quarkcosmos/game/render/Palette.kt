package dev.agsoft.quarkcosmos.game.render

import com.badlogic.gdx.graphics.Color

/**
 * Contrat couleur — Quantique (skill art-direction, DA v2). Seules ces
 * couleurs et leurs mélanges apparaissent à l'écran.
 */
object Pal {
    val key: Color = Color.valueOf("f472b6")
    val accent: Color = Color.valueOf("67e8f9")
    val bg: Color = Color.valueOf("0a0612")
    val danger: Color = Color.valueOf("fb923c")
    val mid: Color = Color.valueOf("c4b5fd")
    val hud: Color = Color.valueOf("f7eef9")
    val hudMuted: Color = Color.valueOf("b9a7c9")
    val bezel: Color = Color.valueOf("150d22")
    val ink: Color = Color.valueOf("1a0820")
    val metal: Color = Color.valueOf("2b1c3a")
    val coil: Color = Color.valueOf("3a2650")
    val wall: Color = Color.valueOf("241634")
    val white: Color = Color.WHITE

    val keyHi: Color = mix(key, white, .5f)
    val accentHi: Color = mix(accent, white, .45f)
    val keyShade: Color = mix(key, Color.valueOf("3a0a2e"), .45f)
    val keyRim: Color = mix(key, white, .35f)

    /** Couleur d'un Photon = son énergie (bas → haut), doublée par le nombre de rayons. */
    val energy = arrayOf(key, mid, accent)
    val energyRays = intArrayOf(4, 6, 8)

    // Fond « C » : gradient profond, luminance ≤ 20 % de la matière.
    val bgTop: Color = Color.valueOf("17061d")
    val bgBottom: Color = Color.valueOf("040a14")

    fun mix(a: Color, b: Color, t: Float): Color = Color(a).lerp(b, t)
}
