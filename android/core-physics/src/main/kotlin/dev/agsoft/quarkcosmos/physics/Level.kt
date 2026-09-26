package dev.agsoft.quarkcosmos.physics

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.double
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/** Version du format livré que ce runtime sait lire (cf. engine/export.py). */
const val SUPPORTED_SCHEMA_VERSION = 2

/** Oscillation sinusoïdale d'une position (`motion`) ou d'un seuil (`threshold_motion`). */
class Motion(val axis: Char, val amplitude: Double, val period: Double, val phase: Double) {
    /** Décalage à l'instant t — même ordre d'opérations que simulate._oscillate. */
    fun offset(t: Double): Double = amplitude * Math.sin(2 * Math.PI * t / period + phase)
}

class Point(val x: Double, val y: Double)

class Target(val x: Double, val y: Double, val r: Double, val motion: Motion?)

class Photon(val id: String, val x: Double, val y: Double, val r: Double, val motion: Motion?)

class Obstacle(
    val id: String,
    val type: String,
    val x: Double,
    val y: Double,
    /** Rayon explicite, sinon celui par défaut de Shapes.radius. */
    val r: Double?,
    /** Longueur d'un segment ; null pour un disque. */
    val length: Double?,
    val angleDeg: Double,
    val energyThreshold: Double?,
    val motion: Motion?,
    val thresholdMotion: Motion?,
)

/** Plage de réglage d'un paramètre de lancer (`param_space`). */
sealed class ParamSpec {
    abstract val values: List<Any>

    class Range(val min: Double, val max: Double, val step: Double) : ParamSpec() {
        override val values: List<Any> by lazy { ParamGrid.rangeValues(min, max, step) }
    }

    class Choice(override val values: List<Any>) : ParamSpec()
}

class Level(
    val id: String,
    val scale: String,
    val concept: String,
    val difficulty: Int,
    val codexText: String,
    val launcher: Point,
    val target: Target,
    val obstacles: List<Obstacle>,
    val photons: List<Photon>,
    val maxWallBounces: Int,
    val paramSpace: Map<String, ParamSpec>,
    /** Paramètres de la solution de référence (indice « premier segment »). */
    val hint: Map<String, Any>?,
) {
    companion object {
        private val json = Json { ignoreUnknownKeys = true }

        /** Lit un fichier `levels/<nom>.json` (format livré v2). */
        fun parse(text: String): Level = fromJson(json.parseToJsonElement(text).jsonObject)

        private fun fromJson(o: JsonObject): Level {
            val schema = o["schema_version"]?.jsonPrimitive?.int
            require(schema == SUPPORTED_SCHEMA_VERSION) {
                "schema_version $schema non supporté (attendu $SUPPORTED_SCHEMA_VERSION)"
            }
            val launcher = o.obj("launcher")
            val target = o.obj("target")
            return Level(
                id = o.str("id"),
                scale = o.str("scale"),
                concept = o.str("concept"),
                difficulty = o["difficulty"]!!.jsonPrimitive.int,
                codexText = o["codex_text"]?.jsonPrimitive?.content ?: "",
                launcher = Point(launcher.num("x"), launcher.num("y")),
                target = Target(
                    target.num("x"), target.num("y"),
                    target.numOrNull("r") ?: DEFAULT_TARGET_RADIUS, motion(target["motion"]),
                ),
                obstacles = o["obstacles"]?.jsonArray.orEmpty().map { obstacle(it.jsonObject) },
                photons = o["photons"]?.jsonArray.orEmpty().map {
                    val p = it.jsonObject
                    Photon(p.str("id"), p.num("x"), p.num("y"), p.numOrNull("r") ?: DEFAULT_PHOTON_RADIUS, motion(p["motion"]))
                },
                maxWallBounces = o["max_wall_bounces"]?.jsonPrimitive?.int ?: MAX_WALL_BOUNCES,
                paramSpace = o["param_space"]?.jsonObject.orEmpty().mapValues { (_, v) -> paramSpec(v.jsonObject) },
                hint = (o["hint"] as? JsonObject)?.get("params")?.jsonObject?.mapValues { (_, v) -> scalar(v) },
            )
        }

        private fun obstacle(o: JsonObject) = Obstacle(
            id = o.str("id"),
            type = o["type"]?.jsonPrimitive?.content ?: "",
            x = o.num("x"),
            y = o.num("y"),
            r = o.numOrNull("r"),
            length = o.numOrNull("length"),
            angleDeg = o.numOrNull("angle_deg") ?: 0.0,
            energyThreshold = o.numOrNull("energy_threshold"),
            motion = motion(o["motion"]),
            thresholdMotion = motion(o["threshold_motion"], axis = 'y'),
        )

        private fun motion(e: JsonElement?, axis: Char? = null): Motion? {
            if (e == null || e is JsonNull) return null
            val m = e.jsonObject
            return Motion(
                axis = axis ?: m["axis"]!!.jsonPrimitive.content.first(),
                amplitude = m.num("amplitude"),
                period = m.num("period"),
                phase = m.numOrNull("phase") ?: 0.0,
            )
        }

        private fun paramSpec(o: JsonObject): ParamSpec = when (val type = o.str("type")) {
            "range" -> ParamSpec.Range(o.num("min"), o.num("max"), o.num("step"))
            "choice" -> ParamSpec.Choice(o["values"]!!.jsonArray.map { scalar(it) })
            else -> error("param_space type inconnu : $type")
        }

        private fun scalar(e: JsonElement): Any {
            val p = e.jsonPrimitive
            return p.booleanOrNull ?: p.doubleOrNull ?: p.content
        }

        private fun JsonObject.obj(k: String) = this[k]!!.jsonObject
        private fun JsonObject.str(k: String) = this[k]!!.jsonPrimitive.content
        private fun JsonObject.num(k: String) = this[k]!!.jsonPrimitive.double
        private fun JsonObject.numOrNull(k: String) = (this[k] as? JsonPrimitive)?.doubleOrNull
    }
}
