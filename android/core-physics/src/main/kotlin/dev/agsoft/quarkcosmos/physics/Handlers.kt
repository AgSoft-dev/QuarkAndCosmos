package dev.agsoft.quarkcosmos.physics

/**
 * Handler d'obstacle : modifie la vitesse de la simulation au contact et
 * renvoie l'événement. (ox, oy) = position effective, threshold = seuil
 * d'énergie effectif à l'instant du contact.
 */
typealias Handler = (sim: Simulation, o: Obstacle, ox: Double, oy: Double, threshold: Double) -> ContactEvent

/**
 * Port des handlers de engine/concepts.py, par type d'obstacle. Seuls ceux
 * des niveaux Tunnel sont portés pour le POC ; les autres concepts
 * s'ajoutent ici avec leurs trajectoires golden (engine/golden.py).
 */
object Handlers {
    /** Rebond « angle d'incidence = angle de réflexion » (wall_reflect). */
    val bounce: Handler = { sim, o, ox, oy, _ ->
        sim.reflectOn(o, ox, oy)
        ContactEvent.BOUNCE
    }

    /** Effet tunnel (tunnel_barrier) : passe si la vitesse atteint le seuil, sinon rebondit. */
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
        "detector" -> bounce // jamais appelé : un détecteur ne touche pas Quarky
        else -> throw UnsupportedObstacle(type)
    }
}
