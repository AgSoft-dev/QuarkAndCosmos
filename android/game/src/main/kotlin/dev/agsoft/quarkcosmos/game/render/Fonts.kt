package dev.agsoft.quarkcosmos.game.render

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.graphics.Texture
import com.badlogic.gdx.graphics.g2d.BitmapFont
import com.badlogic.gdx.graphics.g2d.freetype.FreeTypeFontGenerator
import com.badlogic.gdx.utils.Disposable

/**
 * Polices du HUD (skill art-direction) : JetBrains Mono pour les lectures
 * d'instrument, Fira Sans pour l'interface — OFL, dans assets/fonts/.
 * Générées à la résolution réelle de l'écran (net sur tout DPI) puis ramenées
 * à l'échelle des unités virtuelles de la vue.
 */
class Fonts(pxPerUnit: Float) : Disposable {
    val mono: BitmapFont
    val monoSmall: BitmapFont
    val ui: BitmapFont
    val uiBold: BitmapFont
    val title: BitmapFont

    init {
        val monoGen = FreeTypeFontGenerator(Gdx.files.internal("fonts/JetBrainsMono-Medium.ttf"))
        val uiGen = FreeTypeFontGenerator(Gdx.files.internal("fonts/FiraSans-Regular.ttf"))
        val boldGen = FreeTypeFontGenerator(Gdx.files.internal("fonts/FiraSans-SemiBold.ttf"))
        fun make(gen: FreeTypeFontGenerator, size: Float): BitmapFont {
            val p = FreeTypeFontGenerator.FreeTypeFontParameter().apply {
                this.size = (size * pxPerUnit).toInt().coerceAtLeast(8)
                characters = FreeTypeFontGenerator.DEFAULT_CHARS + EXTRA_CHARS
                minFilter = Texture.TextureFilter.Linear
                magFilter = Texture.TextureFilter.Linear
                kerning = true
            }
            return gen.generateFont(p).apply {
                data.setScale(1f / pxPerUnit)
                setUseIntegerPositions(false)
                data.markupEnabled = false
            }
        }
        mono = make(monoGen, 11f)
        monoSmall = make(monoGen, 9f)
        ui = make(uiGen, 13.5f)
        uiBold = make(boldGen, 14f)
        title = make(boldGen, 19f)
        monoGen.dispose(); uiGen.dispose(); boldGen.dispose()
    }

    override fun dispose() {
        mono.dispose(); monoSmall.dispose(); ui.dispose(); uiBold.dispose(); title.dispose()
    }

    private companion object {
        const val EXTRA_CHARS = "’‘“”—–…•−→←↑↓·"
    }
}
