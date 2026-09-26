package dev.agsoft.quarkcosmos.game

import com.badlogic.gdx.Game

/** Application libGDX : un seul écran pour le POC, le niveau demandé. */
class QuarkGame(private val info: LevelInfo, private val host: GameHost) : Game() {
    override fun create() {
        setScreen(LevelScreen(info, host))
    }

    override fun dispose() {
        screen?.dispose()
        super.dispose()
    }
}
