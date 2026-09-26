package dev.agsoft.quarkcosmos.game

import com.badlogic.gdx.Game

/** libGDX application: a single screen for the POC, the requested level. */
class QuarkGame(private val info: LevelInfo, private val host: GameHost) : Game() {
    override fun create() {
        setScreen(LevelScreen(info, host))
    }

    override fun dispose() {
        screen?.dispose()
        super.dispose()
    }
}
