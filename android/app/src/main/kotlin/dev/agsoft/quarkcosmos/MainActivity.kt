package dev.agsoft.quarkcosmos

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import dev.agsoft.quarkcosmos.ui.LocalType
import dev.agsoft.quarkcosmos.ui.QC
import dev.agsoft.quarkcosmos.ui.QuantumMapScreen
import dev.agsoft.quarkcosmos.ui.WelcomeScreen
import dev.agsoft.quarkcosmos.ui.WorldsScreen
import dev.agsoft.quarkcosmos.ui.rememberQcType

/** POC menus: welcome → scales → Quantum world map → level (GameActivity). */
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        setContent { QuarkApp() }
    }
}

private enum class Screen { WELCOME, WORLDS, QUANTUM_MAP }

@Composable
private fun QuarkApp() {
    val context = LocalContext.current
    var screen by rememberSaveable { mutableStateOf(Screen.WELCOME) }
    val best by remember { Progress.bestStars(context) }.collectAsState(initial = emptyMap())
    val back = { screen = if (screen == Screen.QUANTUM_MAP) Screen.WORLDS else Screen.WELCOME }
    BackHandler(enabled = screen != Screen.WELCOME) { back() }

    CompositionLocalProvider(LocalType provides rememberQcType()) {
        Box(Modifier.fillMaxSize().background(QC.bg).windowInsetsPadding(WindowInsets.safeDrawing)) {
            when (screen) {
                Screen.WELCOME -> WelcomeScreen(onPlay = { screen = Screen.WORLDS })
                Screen.WORLDS -> WorldsScreen(best, onBack = back, onOpen = { screen = Screen.QUANTUM_MAP })
                Screen.QUANTUM_MAP -> QuantumMapScreen(best, onBack = back, onPlay = { node, i ->
                    context.startActivity(GameActivity.intent(context, node, i))
                })
            }
        }
    }
}
