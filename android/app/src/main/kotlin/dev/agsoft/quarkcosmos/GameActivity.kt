package dev.agsoft.quarkcosmos

import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.view.HapticFeedbackConstants
import com.badlogic.gdx.backends.android.AndroidApplication
import com.badlogic.gdx.backends.android.AndroidApplicationConfiguration
import dev.agsoft.quarkcosmos.game.GameHost
import dev.agsoft.quarkcosmos.game.Haptic
import dev.agsoft.quarkcosmos.game.LevelInfo
import dev.agsoft.quarkcosmos.game.QuarkGame

/**
 * Héberge la vue de jeu libGDX pour un niveau. La coque lui fournit le
 * vibreur, la sauvegarde et le retour à la carte ; la carte Compose se met à
 * jour seule (elle observe la progression).
 */
class GameActivity : AndroidApplication(), GameHost {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val info = LevelInfo(
            file = intent.getStringExtra(EXTRA_FILE) ?: error("niveau manquant"),
            title = intent.getStringExtra(EXTRA_TITLE) ?: "",
            subtitle = intent.getStringExtra(EXTRA_SUBTITLE) ?: "",
        )
        val config = AndroidApplicationConfiguration().apply {
            useImmersiveMode = true
            useAccelerometer = false
            useCompass = false
            numSamples = 2
        }
        initialize(QuarkGame(info, this), config)
    }

    // Appelés depuis le thread de rendu libGDX.

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
        private const val EXTRA_TITLE = "level_title"
        private const val EXTRA_SUBTITLE = "level_subtitle"

        fun intent(context: Context, node: LevelNode, index: Int) =
            Intent(context, GameActivity::class.java)
                .putExtra(EXTRA_FILE, node.file)
                .putExtra(EXTRA_TITLE, node.title)
                .putExtra(EXTRA_SUBTITLE, "Quantique · niveau ${index + 1}")
    }
}
