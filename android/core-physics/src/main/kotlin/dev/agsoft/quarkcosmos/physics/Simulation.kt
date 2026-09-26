package dev.agsoft.quarkcosmos.physics

/** Événement d'un contact avec un obstacle (cf. engine/concepts.py). */
enum class ContactEvent(val wire: String) { BOUNCE("bounce"), PASS("pass") }

enum class Status { RUNNING, WIN, LOST_WALL_BOUNCES, TIMEOUT }

/** Obstacle dont le handler n'est pas encore porté (cf. Handlers). */
class UnsupportedObstacle(type: String) : IllegalArgumentException("obstacle « $type » pas encore porté en Kotlin")

/** Effets visibles d'un pas, pour le rendu (particules, haptique). */
interface SimListener {
    fun onContact(obstacleIndex: Int, event: ContactEvent) {}
    fun onBoxBounce() {}
    fun onPhoton(photonIndex: Int) {}
}

/**
 * Un lancer, pas à pas — port de `simulate()` (engine/simulate.py) pour une
 * seule copie de Quarky, suffisant pour les concepts portés (tunnel : paroi,
 * barrière, miroir). L'ordre d'un pas suit docs/physics-spec.md §4 :
 * déplacement → tap → parois de la boîte → obstacles (dans l'ordre du niveau)
 * → Photons → cible.
 *
 * La boucle de jeu appelle [step] un nombre entier de fois par frame (temps
 * réel accumulé, jamais de pas fractionnaire) ; [runToEnd] sert aux tests.
 * Aucune allocation par pas.
 */
class Simulation(val level: Level, params: Map<String, Any>, private val listener: SimListener? = null) {
    /** Position et vitesse de Quarky (boîte unité, y vers le bas). */
    var x = level.launcher.x; private set
    var y = level.launcher.y; private set
    var vx = 0.0; private set
    var vy = 0.0; private set

    /** Position juste après le déplacement du dernier pas, avant les rebonds :
     *  c'est le point que le moteur Python enregistre dans sa traînée. */
    var movedX = x; private set
    var movedY = y; private set

    /** Nombre de pas exécutés ; le temps simulé écoulé vaut steps · DT. */
    var steps = 0; private set
    var status = Status.RUNNING; private set

    /** Pas de fin, au sens de SimResult.steps du moteur Python. */
    var endStep = 0; private set

    val collected = BooleanArray(level.photons.size)
    var collectedCount = 0; private set
    /** (index d'obstacle, événement) dans l'ordre, hors murs — comme SimResult.contacts. */
    val contacts = ArrayList<Pair<Int, ContactEvent>>()

    private val shapes = Shapes()
    private val inContact = BooleanArray(level.obstacles.size)
    private val handlers = level.obstacles.map { Handlers.forType(it.type) }
    private var wallBounces = 0
    private val taps = tapTimes(params)
    private var nextTap = 0
    private var tapped = false

    init {
        val precision = (params["precision"] as Number?)?.toDouble()
        if (precision != null) {
            // Concept incertitude (spec §3) : arrondi bancaire → Math.rint.
            val snap = 2 + (1 - precision) * 28
            val effAngle = Math.rint((params["angle_deg"] as Number).toDouble() / snap) * snap
            setVelocity(effAngle, Math.max(0.15, 1.2 - precision))
        } else {
            setVelocity((params["angle_deg"] as Number).toDouble(), (params["power"] as Number?)?.toDouble() ?: 1.0)
        }
    }

    private fun setVelocity(angleDeg: Double, magnitude: Double) {
        val rad = Math.toRadians(angleDeg)
        vx = Math.cos(rad) * magnitude
        vy = Math.sin(rad) * magnitude
    }

    val running get() = status == Status.RUNNING
    val elapsed get() = steps * DT

    /** Exécute un pas de DT ; renvoie faux si le lancer est terminé. */
    fun step(): Boolean {
        if (status != Status.RUNNING) return false
        val step = steps
        if (step >= MAX_STEPS) return finish(Status.TIMEOUT, MAX_STEPS)
        val t = (step + 1) * DT
        steps = step + 1

        // 1. déplacement (Euler explicite, vitesse constante entre deux contacts)
        x += vx * DT
        y += vy * DT
        movedX = x
        movedY = y

        // 2. tap(s) : sans copie fantôme (superposition non portée), un tap ne
        // fait que basculer l'état consulté par les handlers.
        while (nextTap < taps.size && t >= taps[nextTap]) {
            nextTap++
            tapped = true
        }

        // 3. parois de la boîte fermée (un pas = au plus un rebond compté)
        var bounced = false
        if (x <= 0.0) { x = 0.0; vx = Math.abs(vx); bounced = true } else if (x >= 1.0) { x = 1.0; vx = -Math.abs(vx); bounced = true }
        if (y <= 0.0) { y = 0.0; vy = Math.abs(vy); bounced = true } else if (y >= 1.0) { y = 1.0; vy = -Math.abs(vy); bounced = true }
        if (bounced) {
            listener?.onBoxBounce()
            if (++wallBounces > level.maxWallBounces) return finish(Status.LOST_WALL_BOUNCES, step)
        }

        // 4. obstacles, dans l'ordre du niveau ; un handler par contact
        for (i in level.obstacles.indices) {
            val o = level.obstacles[i]
            if (o.type == "detector") continue
            var ox = o.x
            var oy = o.y
            o.motion?.let { m -> if (m.axis == 'x') ox += m.offset(t) else oy += m.offset(t) }
            if (!shapes.touching(o, ox, oy, x, y, COLLISION_EPS)) {
                inContact[i] = false
                continue
            }
            if (inContact[i]) continue
            inContact[i] = true
            val threshold = effectiveThreshold(o, t)
            val event = handlers[i](this, o, ox, oy, threshold)
            listener?.onContact(i, event)
            if (o.type == "wall") {
                if (++wallBounces > level.maxWallBounces) return finish(Status.LOST_WALL_BOUNCES, step)
            } else {
                contacts.add(i to event)
            }
        }

        // 5. Photons
        for (i in level.photons.indices) {
            if (collected[i]) continue
            val p = level.photons[i]
            var px = p.x
            var py = p.y
            p.motion?.let { m -> if (m.axis == 'x') px += m.offset(t) else py += m.offset(t) }
            if (Math.hypot(x - px, y - py) < p.r + COLLISION_EPS) {
                collected[i] = true
                collectedCount++
                listener?.onPhoton(i)
            }
        }

        // 6. cible
        val tg = level.target
        var tx = tg.x
        var ty = tg.y
        tg.motion?.let { m -> if (m.axis == 'x') tx += m.offset(t) else ty += m.offset(t) }
        if (Math.hypot(x - tx, y - ty) < tg.r + COLLISION_EPS) return finish(Status.WIN, step)

        if (steps >= MAX_STEPS) return finish(Status.TIMEOUT, MAX_STEPS)
        return true
    }

    fun runToEnd(): Simulation {
        while (step()) Unit
        return this
    }

    /** Étoiles du lancer : Photons ramassés, seulement si la cible est atteinte. */
    val stars get() = if (status == Status.WIN) collectedCount else 0

    private fun finish(s: Status, step: Int): Boolean {
        status = s
        endStep = step
        return false
    }

    // --- accès des handlers ---------------------------------------------

    internal val isTapped get() = tapped

    /** Réflexion de la vitesse sur l'obstacle placé en (ox, oy) — vec.reflect(vel, normal). */
    internal fun reflectOn(o: Obstacle, ox: Double, oy: Double) {
        shapes.closestPoint(o, ox, oy, x, y)
        val nx0 = x - shapes.cx
        val ny0 = y - shapes.cy
        val m = Math.hypot(nx0, ny0)
        val nx = if (m < 1e-9) 0.0 else nx0 / m
        val ny = if (m < 1e-9) 0.0 else ny0 / m
        val d = vx * nx + vy * ny
        vx -= 2 * d * nx
        vy -= 2 * d * ny
    }

    /** Énergie de Quarky : la norme de la vitesse (conservée par les rebonds). */
    val speed get() = Math.hypot(vx, vy)

    companion object {
        /** Seuil d'énergie effectif à l'instant t (simulate._effective_threshold). */
        fun effectiveThreshold(o: Obstacle, t: Double): Double {
            val base = o.energyThreshold ?: DEFAULT_ENERGY_THRESHOLD
            val m = o.thresholdMotion ?: return base
            return base + m.offset(t)
        }

        /** Instants des taps : `tap_time`, puis `tap_time_2`… (simulate.tap_times). */
        fun tapTimes(params: Map<String, Any>): DoubleArray =
            params.keys.filter { it.startsWith("tap_time") }
                .sortedWith(compareBy({ it.length }, { it }))
                .mapNotNull { (params[it] as Number?)?.toDouble() }
                .toDoubleArray()
    }
}
