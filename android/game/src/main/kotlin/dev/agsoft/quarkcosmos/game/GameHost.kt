package dev.agsoft.quarkcosmos.game

/** Retour haptique demandé par le jeu (cf. todo.md §3.3). */
enum class Haptic { TICK, LAUNCH, PHOTON, SUCCESS, FAIL }

/**
 * Ce que la coque Android fournit à la vue de jeu libGDX : le jeu ne connaît
 * ni les activités, ni la sauvegarde, ni le vibreur.
 */
interface GameHost {
    /** Niveau réussi avec [stars] étoiles (0–3) ; la coque garde le meilleur score. */
    fun onLevelCompleted(levelId: String, stars: Int)

    /** Retour à la carte du monde. */
    fun exitToMap()

    fun haptic(kind: Haptic)
}

/** Textes d'en-tête du niveau (fournis par la coque, qui connaît la carte). */
class LevelInfo(
    /** Fichier sous assets/levels/, ex. `quantique_tunnel_1.json`. */
    val file: String,
    /** Nom du concept, ex. « Effet tunnel ». */
    val title: String,
    /** Ligne secondaire, ex. « Quantique · niveau 1 ». */
    val subtitle: String,
)
