package dev.agsoft.quarkcosmos

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch

private val Context.progressStore: DataStore<Preferences> by preferencesDataStore(name = "progress")

/**
 * Progression du joueur : meilleur nombre d'étoiles par niveau (0–3).
 * DataStore Preferences pour le POC ; Proto DataStore + Codex prévus au
 * Stage 5 complet (todo.md §4.4).
 */
object Progress {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private fun key(levelId: String) = intPreferencesKey("stars_$levelId")

    /** levelId → meilleures étoiles ; un niveau absent n'est pas encore réussi. */
    fun bestStars(context: Context): Flow<Map<String, Int>> =
        context.applicationContext.progressStore.data.map { prefs ->
            prefs.asMap().entries
                .filter { it.key.name.startsWith("stars_") }
                .associate { it.key.name.removePrefix("stars_") to (it.value as Int) }
        }

    /** Enregistre une réussite ; ne garde que le meilleur score. */
    fun record(context: Context, levelId: String, stars: Int) {
        val store = context.applicationContext.progressStore
        scope.launch {
            store.edit { prefs ->
                val k = key(levelId)
                prefs[k] = maxOf(prefs[k] ?: 0, stars)
            }
        }
    }
}
