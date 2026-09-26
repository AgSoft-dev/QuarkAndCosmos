package dev.agsoft.quarkcosmos.physics

/** Event of a contact with an obstacle (see concepts/handlers.py). */
enum class ContactEvent(val wire: String) { BOUNCE("bounce"), PASS("pass") }

enum class Status { RUNNING, WIN, LOST_WALL_BOUNCES, TIMEOUT }

/** Obstacle whose handler is not ported yet (see Handlers). */
class UnsupportedObstacle(type: String) : IllegalArgumentException("obstacle \"$type\" not ported to Kotlin yet")

/** Visible effects of a step, for rendering (particles, haptics). */
interface SimListener {
    fun onContact(obstacleIndex: Int, event: ContactEvent) {}
    fun onBoxBounce() {}
    fun onPhoton(photonIndex: Int) {}
}

/**
 * One launch, step by step — port of `simulate()` (core/simulate.py) for a
 * single Quarky copy, enough for the ported concepts (tunnel: wall, barrier,
 * mirror). The order of a step follows docs/physics-spec.md §4:
 * move → tap → box walls → obstacles (in level order) → Photons → target.
 *
 * The game loop calls [step] a whole number of times per frame (accumulated
 * real time, never a fractional step); [runToEnd] is for tests.
 * No allocation per step.
 */
class Simulation(val level: Level, params: Map<String, Any>, private val listener: SimListener? = null) {
    /** Quarky's position and velocity (unit box, y pointing down). */
    var x = level.launcher.x; private set
    var y = level.launcher.y; private set
    var vx = 0.0; private set
    var vy = 0.0; private set

    /** Position right after the last step's move, before bounces: this is
     *  the point the Python engine records in its trail. */
    var movedX = x; private set
    var movedY = y; private set

    /** Number of steps run; elapsed simulated time is steps · DT. */
    var steps = 0; private set
    var status = Status.RUNNING; private set

    /** End step, as in the Python engine's SimResult.steps. */
    var endStep = 0; private set

    val collected = BooleanArray(level.photons.size)
    var collectedCount = 0; private set
    /** (obstacle index, event) in order, walls excluded — like SimResult.contacts. */
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
            // incertitude concept (spec §3): banker's rounding → Math.rint.
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

    /** Run one DT step; return false once the launch is over. */
    fun step(): Boolean {
        if (status != Status.RUNNING) return false
        val step = steps
        if (step >= MAX_STEPS) return finish(Status.TIMEOUT, MAX_STEPS)
        val t = (step + 1) * DT
        steps = step + 1

        // 1. move (semi-implicit Euler with no force field: x += v·DT)
        x += vx * DT
        y += vy * DT
        movedX = x
        movedY = y

        // 2. tap(s): without a ghost copy (superposition not ported), a tap
        // only flips the state read by the handlers.
        while (nextTap < taps.size && t >= taps[nextTap]) {
            nextTap++
            tapped = true
        }

        // 3. walls of the closed box (one step = at most one counted bounce);
        // the penetration is mirrored back inside
        var bounced = false
        if (x <= 0.0) { x = -x; vx = Math.abs(vx); bounced = true } else if (x >= 1.0) { x = 2.0 - x; vx = -Math.abs(vx); bounced = true }
        if (y <= 0.0) { y = -y; vy = Math.abs(vy); bounced = true } else if (y >= 1.0) { y = 2.0 - y; vy = -Math.abs(vy); bounced = true }
        if (bounced) {
            listener?.onBoxBounce()
            if (++wallBounces > level.maxWallBounces) return finish(Status.LOST_WALL_BOUNCES, step)
        }

        // 4. obstacles, in level order; one handler per contact
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
            val vxIn = vx
            val vyIn = vy
            val event = handlers[i](this, o, ox, oy, threshold)
            if (event == ContactEvent.BOUNCE) mirrorOut(o, ox, oy, vxIn, vyIn)
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

        // 6. target
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

    /** Stars of the launch: Photons collected, only if the target is reached. */
    val stars get() = if (status == Status.WIN) collectedCount else 0

    private fun finish(s: Status, step: Int): Boolean {
        status = s
        endStep = step
        return false
    }

    // --- handler access ----------------------------------------------

    internal val isTapped get() = tapped

    /** Reflect the velocity on the obstacle placed at (ox, oy), only while
     *  approaching — vec.reflect(vel, normal). */
    internal fun reflectOn(o: Obstacle, ox: Double, oy: Double) {
        shapes.closestPoint(o, ox, oy, x, y)
        val nx0 = x - shapes.cx
        val ny0 = y - shapes.cy
        val m = Math.hypot(nx0, ny0)
        val nx = if (m < 1e-9) 0.0 else nx0 / m
        val ny = if (m < 1e-9) 0.0 else ny0 / m
        val d = vx * nx + vy * ny
        if (d >= 0.0) return
        vx -= 2 * d * nx
        vy -= 2 * d * ny
    }

    /** After a reflection, mirror the penetration out of the contact surface
     *  (radius + EPS) — simulate._mirror_out, same order of operations. */
    private fun mirrorOut(o: Obstacle, ox: Double, oy: Double, vxIn: Double, vyIn: Double) {
        shapes.closestPoint(o, ox, oy, x, y)
        val nx = x - shapes.cx
        val ny = y - shapes.cy
        val d = Math.hypot(nx, ny)
        val reach = shapes.radius(o) + COLLISION_EPS
        if (d < 1e-9 || d >= reach || vxIn * nx + vyIn * ny >= 0.0 || vx * nx + vy * ny <= 0.0) return
        val k = 2 * (reach - d) / d
        x += nx * k
        y += ny * k
    }

    /** Quarky's energy: the velocity norm (conserved by bounces). */
    val speed get() = Math.hypot(vx, vy)

    companion object {
        /** Effective energy threshold at time t (simulate._effective_threshold). */
        fun effectiveThreshold(o: Obstacle, t: Double): Double {
            val base = o.energyThreshold ?: DEFAULT_ENERGY_THRESHOLD
            val m = o.thresholdMotion ?: return base
            return base + m.offset(t)
        }

        /** Tap instants: `tap_time`, then `tap_time_2`… (simulate.tap_times). */
        fun tapTimes(params: Map<String, Any>): DoubleArray =
            params.keys.filter { it.startsWith("tap_time") }
                .sortedWith(compareBy({ it.length }, { it }))
                .mapNotNull { (params[it] as Number?)?.toDouble() }
                .toDoubleArray()
    }
}
