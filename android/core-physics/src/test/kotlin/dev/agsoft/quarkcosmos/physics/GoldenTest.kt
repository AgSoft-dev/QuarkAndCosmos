package dev.agsoft.quarkcosmos.physics

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.double
import kotlinx.serialization.json.int
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * Python ⇄ Kotlin contract (docs/decisions/ADR-0005): every golden launch written
 * by `python3 -m quarkcosmos_levels golden` (export/golden.py) is replayed here;
 * position at every step within 1e-6, same outcome, same Photons, same contacts.
 */
class GoldenTest {
    private val levelsDir = File(System.getProperty("levels.dir") ?: "../../content/levels/quantique")
    private val goldenDir = File(System.getProperty("golden.dir") ?: "../../levels-builder/tests/golden")

    private fun level(name: String) = Level.parse(File(levelsDir, "$name.json").readText())

    private fun replay(name: String) {
        val level = level(name)
        val golden = Json.parseToJsonElement(File(goldenDir, "$name.golden.json").readText()).jsonObject
        assertEquals(level.id, golden["level_id"]!!.jsonPrimitive.content)
        val cases = golden["cases"]!!.jsonArray
        assertTrue(cases.size >= 3)
        for (c in cases.map { it.jsonObject }) {
            val label = "$name/${c["name"]!!.jsonPrimitive.content}"
            val params = c["params"]!!.jsonObject.mapValues { (_, v) -> v.jsonPrimitive.double as Any }
            val trail = c["trail"]!!.jsonArray
            val sim = Simulation(level, params)
            for ((i, p) in trail.withIndex()) {
                val (gx, gy) = p.jsonArray.map { it.jsonPrimitive.double }
                val stepped = sim.step()
                assertEquals("$label x at step $i", gx, sim.movedX, 1e-6)
                assertEquals("$label y at step $i", gy, sim.movedY, 1e-6)
                assertEquals("$label end at step $i", i < trail.size - 1, stepped)
            }
            val success = c["success"]!!.jsonPrimitive.boolean
            val reason = c["reason"]!!.jsonPrimitive.content
            val expected = when {
                success -> Status.WIN
                reason == "timeout" -> Status.TIMEOUT
                reason == "lost:too_many_wall_bounces" -> Status.LOST_WALL_BOUNCES
                else -> error("unknown outcome $reason")
            }
            assertEquals(label, expected, sim.status)
            assertEquals("$label steps", c["steps"]!!.jsonPrimitive.int, sim.endStep)
            val photons = level.photons.filterIndexed { i, _ -> sim.collected[i] }.map { it.id }.sorted()
            val goldenPhotons = c["photons"]!!.jsonArray.map { it.jsonPrimitive.content }
            // Python only counts Photons when the target is reached.
            assertEquals("$label photons", goldenPhotons, if (success) photons else emptyList<String>())
            val contacts = sim.contacts.map { (i, e) -> listOf(level.obstacles[i].id, e.wire) }
            val goldenContacts = c["contacts"]!!.jsonArray.map { pair -> pair.jsonArray.map { it.jsonPrimitive.content } }
            assertEquals("$label contacts", goldenContacts, contacts)
        }
    }

    @Test fun tunnel1() = replay("quantique_tunnel_1")
    @Test fun tunnel2() = replay("quantique_tunnel_2")
    @Test fun tunnel3() = replay("quantique_tunnel_3")

    @Test fun tunnel1HintWinsWithThreeStars() {
        val level = level("quantique_tunnel_1")
        val sim = Simulation(level, level.hint!!).runToEnd()
        assertEquals(Status.WIN, sim.status)
        assertEquals(3, sim.stars)
    }
}
