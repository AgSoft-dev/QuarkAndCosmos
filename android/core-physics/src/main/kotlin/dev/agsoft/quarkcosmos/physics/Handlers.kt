package dev.agsoft.quarkcosmos.physics

/**
 * Obstacle handler: changes the simulation's velocity on contact and returns
 * the event. (ox, oy) = effective position, threshold = effective energy
 * threshold at the contact instant.
 */
typealias Handler = (sim: Simulation, o: Obstacle, ox: Double, oy: Double, threshold: Double) -> ContactEvent

/**
 * Port of the concepts/handlers.py handlers, per obstacle type. Only those of
 * the Tunnel levels are ported for the POC; the other concepts are added here
 * together with their golden trajectories (export/golden.py).
 */
object Handlers {
    /** "Angle of incidence = angle of reflection" bounce (wall_reflect). */
    val bounce: Handler = { sim, o, ox, oy, _ ->
        sim.reflectOn(o, ox, oy)
        ContactEvent.BOUNCE
    }

    /** Tunnel effect (tunnel_barrier): passes if the speed reaches the threshold, otherwise bounces. */
    val barrier: Handler = { sim, o, ox, oy, threshold ->
        if (sim.speed >= threshold) ContactEvent.PASS
        else {
            sim.reflectOn(o, ox, oy)
            ContactEvent.BOUNCE
        }
    }

    fun forType(type: String): Handler = when (type) {
        "wall", "mirror" -> bounce
        "barrier" -> barrier
        "detector" -> bounce // never called: a detector never touches Quarky
        else -> throw UnsupportedObstacle(type)
    }
}
