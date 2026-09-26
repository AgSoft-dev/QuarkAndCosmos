package dev.agsoft.quarkcosmos.game

/** Haptic feedback requested by the game (see todo.md §3.3). */
enum class Haptic { TICK, LAUNCH, PHOTON, SUCCESS, FAIL }

/**
 * What the Android shell provides to the libGDX game view: the game knows
 * nothing about activities, saving or the vibrator.
 */
interface GameHost {
    /** Level completed with [stars] stars (0–3); the shell keeps the best score. */
    fun onLevelCompleted(levelId: String, stars: Int)

    /** Back to the world map. */
    fun exitToMap()

    fun haptic(kind: Haptic)
}

/** Level header texts and localised strings (provided by the shell, which knows the map and the locale). */
class LevelInfo(
    /** File under assets/levels/, e.g. `quantique_tunnel_1.json`. */
    val file: String,
    /** Concept name, e.g. "Tunnel effect". */
    val title: String,
    /** Secondary line, e.g. "Quantum · level 1". */
    val subtitle: String,
    /** Codex line shown after a win (content/codex/<lang>/), empty if none. */
    val codex: String = "",
    val text: GameText = GameText(),
    /** Show the aiming guided tour (first slingshot level, not yet completed). */
    val tutorial: Boolean = false,
)

/**
 * Every player-facing string of the level screen. The libGDX module has no
 * Android resources: the shell fills this from `strings.xml` (values/ = English,
 * values-fr/ = French). The defaults are the English strings, used by desktop
 * tooling.
 */
class GameText(
    val flashPass: String = "Tunnel effect: Quarky went through the barrier, not over it!",
    val flashBlocked: String = "Below the tunnel threshold: the barrier sends Quarky back.",
    val readingsHeader: String = "INSTRUMENT READINGS",
    val angle: String = "ANGLE",
    val energy: String = "QUARKY’S ENERGY",
    val threshold: String = "TUNNEL THRESHOLD",
    val passes: String = "PASSES",
    val blocked: String = "BLOCKED",
    val aimHelp: String = "Pull left for energy, slide up or down to aim, then let go. The thinner the barrier, the less energy it takes to tunnel through.",
    val hint: String = "Hint: the violet dotted line shows the start of the reference path.",
    val resultHeader: String = "INSTRUMENT READING",
    val outcomeWin: String = "Target reached",
    val outcomeTimeout: String = "Time’s up",
    val outcomeLost: String = "One bounce too many",
    val msgPerfect: String = "Three Photons in a single flight: a perfect path!",
    val msgWin: String = "A Photon is still waiting: there is a finer path.",
    val msgTimeout: String = "Quarky lingered on the way. A more direct shot?",
    val msgLost: String = "Quarky bounced off the cavity wall. Adjust the energy and try again!",
    val codexSignature: String = "— LAB LOGBOOK",
    val retry: String = "RETRY",
    val map: String = "MAP",
    val next: String = "CONTINUE",
    val tourEnergy: String = "Pull left: energy",
    val tourAim: String = "Slide up/down: aim",
    val tourLaunch: String = "Let go: launch",
)
