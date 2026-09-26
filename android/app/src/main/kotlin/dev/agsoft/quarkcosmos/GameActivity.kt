package dev.agsoft.quarkcosmos

import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.view.HapticFeedbackConstants
import com.badlogic.gdx.backends.android.AndroidApplication
import com.badlogic.gdx.backends.android.AndroidApplicationConfiguration
import dev.agsoft.quarkcosmos.game.GameHost
import dev.agsoft.quarkcosmos.game.GameText
import dev.agsoft.quarkcosmos.game.Haptic
import dev.agsoft.quarkcosmos.game.LevelInfo
import dev.agsoft.quarkcosmos.game.QuarkGame
import org.json.JSONObject

/**
 * Hosts the libGDX game view for one level. The shell provides the vibrator,
 * saving, the way back to the map and every localised string; the Compose map
 * updates by itself (it observes the progress).
 */
class GameActivity : AndroidApplication(), GameHost {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val info = LevelInfo(
            file = intent.getStringExtra(EXTRA_FILE) ?: error("missing level"),
            title = intent.getStringExtra(EXTRA_TITLE) ?: "",
            subtitle = intent.getStringExtra(EXTRA_SUBTITLE) ?: "",
            codex = codexLine(intent.getStringExtra(EXTRA_CONCEPT)),
            text = gameText(),
        )
        val config = AndroidApplicationConfiguration().apply {
            useImmersiveMode = true
            useAccelerometer = false
            useCompass = false
            numSamples = 2
        }
        initialize(QuarkGame(info, this), config)
    }

    /** Codex line of [concept] in the app's language (assets/codex/<lang>/quantique.json). */
    private fun codexLine(concept: String?): String {
        if (concept == null) return ""
        return runCatching {
            val lang = getString(R.string.codex_lang)
            val json = assets.open("codex/$lang/quantique.json").bufferedReader().use { it.readText() }
            JSONObject(json).getJSONObject("lines").optString(concept, "")
        }.getOrDefault("")
    }

    private fun gameText() = GameText(
        flashPass = getString(R.string.game_flash_pass),
        flashBlocked = getString(R.string.game_flash_blocked),
        readingsHeader = getString(R.string.game_readings),
        angle = getString(R.string.game_angle),
        energy = getString(R.string.game_energy),
        threshold = getString(R.string.game_threshold),
        passes = getString(R.string.game_passes),
        blocked = getString(R.string.game_blocked),
        aimHelp = getString(R.string.game_aim_help),
        hint = getString(R.string.game_hint),
        resultHeader = getString(R.string.game_result),
        outcomeWin = getString(R.string.game_outcome_win),
        outcomeTimeout = getString(R.string.game_outcome_timeout),
        outcomeLost = getString(R.string.game_outcome_lost),
        msgPerfect = getString(R.string.game_msg_perfect),
        msgWin = getString(R.string.game_msg_win),
        msgTimeout = getString(R.string.game_msg_timeout),
        msgLost = getString(R.string.game_msg_lost),
        codexSignature = getString(R.string.game_codex_signature),
        retry = getString(R.string.game_retry),
        map = getString(R.string.game_map),
        next = getString(R.string.game_next),
    )

    // Called from the libGDX render thread.

    override fun onLevelCompleted(levelId: String, stars: Int) {
        Progress.record(this, levelId, stars)
    }

    override fun exitToMap() {
        runOnUiThread { finish() }
    }

    override fun haptic(kind: Haptic) {
        val constant = when (kind) {
            Haptic.TICK -> HapticFeedbackConstants.CLOCK_TICK
            Haptic.LAUNCH -> HapticFeedbackConstants.VIRTUAL_KEY
            Haptic.PHOTON -> HapticFeedbackConstants.KEYBOARD_TAP
            Haptic.SUCCESS -> if (Build.VERSION.SDK_INT >= 30) HapticFeedbackConstants.CONFIRM else HapticFeedbackConstants.LONG_PRESS
            Haptic.FAIL -> if (Build.VERSION.SDK_INT >= 30) HapticFeedbackConstants.REJECT else HapticFeedbackConstants.LONG_PRESS
        }
        runOnUiThread { window.decorView.performHapticFeedback(constant) }
    }

    companion object {
        private const val EXTRA_FILE = "level_file"
        private const val EXTRA_CONCEPT = "level_concept"
        private const val EXTRA_TITLE = "level_title"
        private const val EXTRA_SUBTITLE = "level_subtitle"

        fun intent(context: Context, node: LevelNode, index: Int) =
            Intent(context, GameActivity::class.java)
                .putExtra(EXTRA_FILE, node.file)
                .putExtra(EXTRA_CONCEPT, node.concept)
                .putExtra(EXTRA_TITLE, context.getString(node.title))
                .putExtra(EXTRA_SUBTITLE, context.getString(R.string.level_subtitle, index + 1))
    }
}
