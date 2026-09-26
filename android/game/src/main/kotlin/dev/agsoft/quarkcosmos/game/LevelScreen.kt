package dev.agsoft.quarkcosmos.game

import com.badlogic.gdx.Gdx
import com.badlogic.gdx.Input
import com.badlogic.gdx.InputAdapter
import com.badlogic.gdx.ScreenAdapter
import com.badlogic.gdx.graphics.Color
import com.badlogic.gdx.graphics.OrthographicCamera
import com.badlogic.gdx.graphics.g2d.BitmapFont
import com.badlogic.gdx.graphics.g2d.GlyphLayout
import com.badlogic.gdx.math.Vector2
import com.badlogic.gdx.utils.Align
import com.badlogic.gdx.utils.ScreenUtils
import com.badlogic.gdx.utils.viewport.ExtendViewport
import dev.agsoft.quarkcosmos.game.render.Canvas
import dev.agsoft.quarkcosmos.game.render.Canvas.Companion.TAU
import dev.agsoft.quarkcosmos.game.render.Canvas.Companion.hash
import dev.agsoft.quarkcosmos.game.render.Eyes
import dev.agsoft.quarkcosmos.game.render.Fonts
import dev.agsoft.quarkcosmos.game.render.Mouth
import dev.agsoft.quarkcosmos.game.render.Pal
import dev.agsoft.quarkcosmos.game.render.QuarkyPose
import dev.agsoft.quarkcosmos.game.render.QuarkyRenderer
import dev.agsoft.quarkcosmos.physics.ContactEvent
import dev.agsoft.quarkcosmos.physics.DT
import dev.agsoft.quarkcosmos.physics.Level
import dev.agsoft.quarkcosmos.physics.MAX_STEPS
import dev.agsoft.quarkcosmos.physics.Obstacle
import dev.agsoft.quarkcosmos.physics.ParamGrid
import dev.agsoft.quarkcosmos.physics.ParamSpec
import dev.agsoft.quarkcosmos.physics.SEGMENT_HALF_THICKNESS
import dev.agsoft.quarkcosmos.physics.SimListener
import dev.agsoft.quarkcosmos.physics.Simulation
import dev.agsoft.quarkcosmos.physics.Status
import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * One playable level (POC: Tunnel 1). Portrait, art direction v2 "B + C background".
 *
 * - Aim: drag back from anywhere in the box (slingshot), release to launch.
 *   Angle and energy snap to the level's `param_space` grid — the one on which
 *   the validator proved solvability and measured the stars. Coming back near
 *   the start point cancels.
 * - Flight: the physics (`:core-physics`) advances in whole DT steps, the
 *   render interpolates between the last two states. The apparatus "starts"
 *   with the shot: every oscillation starts from t = 0 at release (spec §3).
 * - Result: read as an instrument reading in the bottom panel, never as a
 *   pop-up over the play area.
 * - Text: every player-facing string comes from [LevelInfo.text] (localised by the shell).
 */
class LevelScreen(private val info: LevelInfo, private val host: GameHost) : ScreenAdapter(), SimListener {

    private enum class Phase { AIM, FLIGHT, OUTRO, RESULT }
    private enum class Btn { BACK, RESET, RETRY, MAP }

    private class Button(val id: Btn, val x: Float, val y: Float, val w: Float, val h: Float) {
        fun hit(px: Float, py: Float) = px >= x - 6 && px <= x + w + 6 && py >= y - 6 && py <= y + h + 6
    }

    private val txt = info.text
    private val level = Level.parse(Gdx.files.internal("levels/${info.file}").readString("UTF-8"))
    private val cam = OrthographicCamera()
    private val viewport = ExtendViewport(MIN_W, MIN_H, cam)
    private val cv = Canvas()
    private val quarky = QuarkyRenderer(cv)
    private val pose = QuarkyPose()
    private var fonts: Fonts? = null
    private var fontsPx = 0f
    private val layout = GlyphLayout()

    // --- layout (virtual units, y pointing up) -----------------------------
    private var w = MIN_W
    private var h = MIN_H
    private var boxX = 0f
    private var boxS = 0f
    private var boxTop = 0f
    private val boxBottom get() = boxTop - boxS
    private fun px(u: Double) = boxX + u.toFloat() * boxS
    private fun py(v: Double) = boxTop - v.toFloat() * boxS

    // --- launch settings -----------------------------------------------
    private val angleSpec = level.paramSpace["angle_deg"] ?: ParamSpec.Range(0.0, 0.0, 1.0)
    private val powerSpec = level.paramSpace["power"] ?: ParamSpec.Choice(listOf(1.0))
    private val angleMin = angleSpec.values.minOf { (it as Number).toDouble() }
    private val angleMax = angleSpec.values.maxOf { (it as Number).toDouble() }
    private val powerMin = powerSpec.values.minOf { (it as Number).toDouble() }
    private val powerMax = powerSpec.values.maxOf { (it as Number).toDouble() }
    private var aimAngle = ParamGrid.snap(angleSpec, 0.0)
    private var aimPower = ParamGrid.snap(powerSpec, (powerMin + powerMax) / 2)
    private val powerFrac get() = if (powerMax > powerMin) ((aimPower - powerMin) / (powerMax - powerMin)).toFloat() else 1f

    // --- state ------------------------------------------------------------
    private var phase = Phase.AIM
    private var time = 0f
    /** Apparatus clock (s): 0 before the shot, simulated time during the flight. */
    private var clock = 0f
    private var outroT = 0f
    private var dragging = false
    private var armed = false
    private val dragStart = Vector2()
    private var pull = 0f
    private var sim: Simulation? = null
    private var acc = 0f
    private var prevX = 0.0
    private var prevY = 0.0
    private var endX = 0f
    private var endY = 0f
    private var outcome = Status.RUNNING
    private var stars = 0
    private var failures = 0
    private var flightStart = 0f
    private var happyUntil = 0f
    private var barrierHitT = -9f
    private var flash = ""
    private var flashT = -9f

    // trail of the current flight and ghost of the previous shot
    private val trail = FloatArray(TRAIL * 2)
    private var trailN = 0
    private var trailHead = 0
    private val lastShot = FloatArray((MAX_STEPS + 1) * 2)
    private var lastShotN = 0

    // Photon collection bursts
    private val burstX = FloatArray(6)
    private val burstY = FloatArray(6)
    private val burstT = FloatArray(6) { -9f }
    private val burstC = IntArray(6)
    private var burstI = 0

    private val buttons = ArrayList<Button>()
    private val touch = Vector2()

    // precomputed scenery (C background: bokeh, fog, dust)
    private val bokeh = Array(12) { i -> floatArrayOf(hash(i * 1.7f), hash(i * 2.9f + 3), 22f + 40 * hash(i * 5.3f), hash(i * 7.1f) * TAU, .6f + hash(i + 11f)) }
    private val fog = Array(6) { i -> floatArrayOf(hash(i * 3.3f + 1), hash(i * 4.1f + 2), 120f + 90 * hash(i * 2.2f), hash(i * 6.7f) * TAU) }
    private val dust = Array(34) { i -> floatArrayOf(hash(i * 9.1f), hash(i * 4.7f + 5), .5f + .8f * hash(i * 3.9f), .2f + .8f * hash(i * 1.3f)) }

    init {
        Gdx.input.setCatchKey(Input.Keys.BACK, true)
        Gdx.input.inputProcessor = object : InputAdapter() {
            override fun touchDown(sx: Int, sy: Int, pointer: Int, button: Int): Boolean {
                if (pointer != 0) return false
                viewport.unproject(touch.set(sx.toFloat(), sy.toFloat()))
                onDown(touch.x, touch.y)
                return true
            }

            override fun touchDragged(sx: Int, sy: Int, pointer: Int): Boolean {
                if (pointer != 0) return false
                viewport.unproject(touch.set(sx.toFloat(), sy.toFloat()))
                onDrag(touch.x, touch.y)
                return true
            }

            override fun touchUp(sx: Int, sy: Int, pointer: Int, button: Int): Boolean {
                if (pointer != 0) return false
                onUp()
                return true
            }

            override fun keyDown(keycode: Int): Boolean {
                if (keycode == Input.Keys.BACK || keycode == Input.Keys.ESCAPE) {
                    host.exitToMap()
                    return true
                }
                return false
            }
        }
    }

    // ======================================================================
    // Input
    // ======================================================================

    private fun onDown(x: Float, y: Float) {
        buttons.firstOrNull { it.hit(x, y) }?.let { press(it.id); return }
        if (phase == Phase.AIM && y > boxBottom - 40 && y < boxTop + 20) {
            dragging = true
            armed = false
            dragStart.set(x, y)
        }
    }

    private fun onDrag(x: Float, y: Float) {
        if (!dragging) return
        val dx = dragStart.x - x
        val dy = dragStart.y - y
        pull = sqrt(dx * dx + dy * dy)
        armed = pull > DEAD_ZONE
        if (!armed) return
        // shot direction = opposite of the gesture; physics angle (y pointing down)
        val deg = Math.toDegrees(atan2(-dy, dx).toDouble()).coerceIn(angleMin, angleMax)
        val pw = powerMin + (((pull - DEAD_ZONE) / PULL_RANGE).coerceIn(0f, 1f)) * (powerMax - powerMin)
        val a = ParamGrid.snap(angleSpec, deg)
        val p = ParamGrid.snap(powerSpec, pw)
        if (a != aimAngle || p != aimPower) host.haptic(Haptic.TICK)
        aimAngle = a
        aimPower = p
    }

    private fun onUp() {
        if (!dragging) return
        dragging = false
        if (armed) launch()
        armed = false
        pull = 0f
    }

    private fun press(id: Btn) {
        when (id) {
            Btn.BACK, Btn.MAP -> host.exitToMap()
            Btn.RESET, Btn.RETRY -> resetShot()
        }
    }

    // ======================================================================
    // Shot sequence
    // ======================================================================

    private fun launch() {
        sim = Simulation(level, mapOf("angle_deg" to aimAngle, "power" to aimPower), this)
        prevX = level.launcher.x
        prevY = level.launcher.y
        acc = 0f
        clock = 0f
        trailN = 0
        flightStart = time
        phase = Phase.FLIGHT
        flash = ""
        host.haptic(Haptic.LAUNCH)
    }

    private fun resetShot() {
        if (phase == Phase.FLIGHT) sim?.let { copyShot(); if (it.running) failures++ }
        sim = null
        phase = Phase.AIM
        clock = 0f
        outcome = Status.RUNNING
        flash = ""
        dragging = false
    }

    private fun copyShot() {
        val n = min(trailN, TRAIL)
        lastShotN = 0
        for (k in 0 until n) {
            val i = (trailHead - n + k + TRAIL) % TRAIL
            lastShot[lastShotN * 2] = trail[i * 2]
            lastShot[lastShotN * 2 + 1] = trail[i * 2 + 1]
            lastShotN++
        }
    }

    private fun update(dt: Float) {
        when (phase) {
            Phase.AIM -> clock = 0f
            Phase.FLIGHT -> {
                val s = sim ?: return
                acc += dt
                while (acc >= DT) {
                    prevX = s.x
                    prevY = s.y
                    val more = s.step()
                    acc -= DT.toFloat()
                    pushTrail(s.x, s.y)
                    if (!more) { endFlight(s); return }
                }
                clock = (s.elapsed + acc).toFloat()
            }
            Phase.OUTRO -> {
                outroT += dt
                clock += dt
                if (outroT >= OUTRO) phase = Phase.RESULT
            }
            Phase.RESULT -> {
                outroT += dt
                clock += dt
            }
        }
    }

    private fun pushTrail(x: Double, y: Double) {
        trail[trailHead * 2] = x.toFloat()
        trail[trailHead * 2 + 1] = y.toFloat()
        trailHead = (trailHead + 1) % TRAIL
        trailN++
    }

    private fun endFlight(s: Simulation) {
        outcome = s.status
        stars = s.stars
        endX = px(s.x)
        endY = py(s.y)
        copyShot()
        phase = Phase.OUTRO
        outroT = 0f
        if (outcome == Status.WIN) {
            host.onLevelCompleted(level.id, stars)
            host.haptic(Haptic.SUCCESS)
        } else {
            failures++
            host.haptic(Haptic.FAIL)
        }
    }

    // --- SimListener (called during step()) ---------------------------------

    override fun onPhoton(photonIndex: Int) {
        val p = level.photons[photonIndex]
        val t = (sim?.elapsed ?: 0.0)
        burstX[burstI] = px(p.x + (p.motion?.takeIf { it.axis == 'x' }?.offset(t) ?: 0.0))
        burstY[burstI] = py(p.y + (p.motion?.takeIf { it.axis == 'y' }?.offset(t) ?: 0.0))
        burstT[burstI] = time
        burstC[burstI] = photonIndex % 3
        burstI = (burstI + 1) % burstT.size
        happyUntil = time + .35f
        host.haptic(Haptic.PHOTON)
    }

    override fun onContact(obstacleIndex: Int, event: ContactEvent) {
        if (level.obstacles[obstacleIndex].type != "barrier") return
        if (event == ContactEvent.PASS) {
            flash = txt.flashPass
        } else {
            flash = txt.flashBlocked
            barrierHitT = time
        }
        flashT = time
    }

    // ======================================================================
    // Rendering
    // ======================================================================

    override fun resize(width: Int, height: Int) {
        viewport.update(width, height, true)
        w = viewport.worldWidth
        h = viewport.worldHeight
        boxS = min(w - 2 * MARGIN, h * .56f)
        boxX = (w - boxS) / 2
        boxTop = h - TOP_BAR - 8
        val pxPerUnit = width / w
        if (abs(pxPerUnit - fontsPx) > .01f) {
            fonts?.dispose()
            fonts = Fonts(pxPerUnit)
            fontsPx = pxPerUnit
        }
    }

    override fun render(delta: Float) {
        val dt = min(delta, .1f)
        time += dt
        update(dt)
        ScreenUtils.clear(Pal.bg.r, Pal.bg.g, Pal.bg.b, 1f)
        viewport.apply()
        cv.begin(cam)
        updatePose()
        drawBackground()
        drawBoxFrame()
        drawGuides()
        drawObstacles()
        drawPhotons()
        drawPortal()
        drawLauncher()
        drawTrail()
        quarky.draw(pose, time)
        drawBursts()
        drawForeground()
        buttons.clear()
        drawTopBar()
        drawPanel()
        cv.end()
    }

    private val fringeLock get() = if (outcome == Status.WIN && phase >= Phase.OUTRO) min(1f, outroT / .6f) else 0f
    private val decoherence get() = if (outcome != Status.WIN && outcome != Status.RUNNING && phase >= Phase.OUTRO) min(1f, outroT / .5f) * max(0f, 1 - (outroT - OUTRO) / 1.5f) else 0f

    private fun updatePose() {
        val r = QUARKY_R
        pose.r = r
        pose.alpha = 1f
        pose.fizzle = 0f
        pose.ghosts = .35f
        pose.mouth = Mouth.SMILE
        pose.eyes = if (time < happyUntil) Eyes.HAPPY else Eyes.NORMAL
        val lx = px(level.launcher.x)
        val ly = py(level.launcher.y)
        val aimRad = Math.toRadians(aimAngle).toFloat()
        val dirX = cos(aimRad)
        val dirY = -sin(aimRad)
        when (phase) {
            Phase.AIM -> {
                val f = if (armed) ((pull - DEAD_ZONE) / PULL_RANGE).coerceIn(0f, 1f) else 0f
                pose.x = lx - dirX * f * r * 1.1f
                pose.y = ly - dirY * f * r * 1.1f
                pose.ang = atan2(dirY, dirX)
                pose.stretch = .14f * f
                pose.lookX = dirX
                pose.lookY = dirY
                if (armed) { pose.eyes = Eyes.SQUINT; pose.mouth = Mouth.FLAT }
            }
            Phase.FLIGHT -> {
                val s = sim ?: return
                val u = (acc / DT).toFloat().coerceIn(0f, 1f)
                pose.x = px(prevX + (s.x - prevX) * u)
                pose.y = py(prevY + (s.y - prevY) * u)
                pose.ang = atan2(-s.vy, s.vx).toFloat()
                pose.stretch = .06f + .12f * s.speed.toFloat()
                pose.lookX = cos(pose.ang)
                pose.lookY = sin(pose.ang)
                pose.ghosts = .6f
                if (time - flightStart < .3f) pose.eyes = Eyes.WIDE
            }
            Phase.OUTRO, Phase.RESULT -> {
                val u = min(1f, outroT / OUTRO)
                if (outcome == Status.WIN) {
                    val (tx, ty) = targetPos()
                    val e = u * u * (3 - 2 * u)
                    pose.x = endX + (tx - endX) * e
                    pose.y = endY + (ty - endY) * e
                    pose.r = r * (1 - .75f * e)
                    pose.alpha = if (phase == Phase.RESULT) 0f else 1 - e * .9f
                    pose.eyes = Eyes.HAPPY
                    pose.stretch = .15f * (1 - e)
                    pose.ghosts = 0f
                } else {
                    pose.x = endX
                    pose.y = endY
                    pose.fizzle = u
                    pose.alpha = if (phase == Phase.RESULT) 0f else 1f
                    pose.eyes = Eyes.WIDE
                    pose.mouth = Mouth.O
                    pose.ghosts = 0f
                }
            }
        }
    }

    private fun targetPos(): Pair<Float, Float> {
        val tg = level.target
        val o = tg.motion?.offset(clock.toDouble()) ?: 0.0
        val isX = tg.motion?.axis == 'x'
        return px(tg.x + if (isX) o else 0.0) to py(tg.y + if (isX) 0.0 else o)
    }

    // --- "C" background: 3-layer parallax, portal rays, fringes -------------

    private fun drawBackground() {
        val s = cv.shapes()
        s.rect(0f, 0f, w, h / 2, Pal.bgBottom, Pal.bgBottom, Pal.bg, Pal.bg)
        s.rect(0f, h / 2, w, h / 2, Pal.bg, Pal.bg, Pal.bgTop, Pal.bgTop)
        val (tx, ty) = targetPos()
        val qx = (pose.x - w / 2)
        val qy = (pose.y - h / 2)
        cv.additive(true)
        cv.glow(tx, ty, 300f, Pal.key, .09f)
        cv.glow(px(level.launcher.x), py(level.launcher.y), 240f, Pal.accent, .04f)
        // layer 1: distant bokeh
        for (b in bokeh) {
            val x = b[0] * w - qx * .03f + sin(time * .1f * b[4] + b[3]) * 12
            val y = b[1] * h - qy * .02f + cos(time * .08f * b[4] + b[3]) * 10
            cv.glow(x, y, b[2], if (b[4] > 1.1f) Pal.accent else Pal.key, .05f)
        }
        // soft light rays from the portal
        val sh = cv.shapes()
        for (i in 0 until 5) {
            val an = Math.PI.toFloat() * .55f + i * .5f + sin(time * .15f + i) * .04f
            val len = 760f
            val wd = .035f + .02f * sin(time * .3f + i * 2)
            val c0 = RAY.set(Pal.key.r, Pal.key.g, Pal.key.b, .05f)
            val c1 = RAY_END.set(Pal.key.r, Pal.key.g, Pal.key.b, 0f)
            sh.triangle(tx, ty, tx + cos(an - wd) * len, ty + sin(an - wd) * len, tx + cos(an + wd) * len, ty + sin(an + wd) * len, c0, c1, c1)
        }
        // layer 2: fog
        for (f in fog) {
            cv.glow(f[0] * w - qx * .06f + sin(time * .12f + f[3]) * 30, f[1] * h + cos(time * .1f + f[3]) * 20, f[2], if (f[3] > 3f) Pal.accent else Pal.key, .045f)
        }
        cv.additive(false)
        drawFringes()
        drawScan()
    }

    /** Sharp interference fringes (B style) in the cavity: they lock on success and decohere on failure. */
    private fun drawFringes() {
        val lock = fringeLock
        val deco = decoherence
        val sp = 34f
        val peak = .04f * (.85f + 1.1f * lock) * (1 - .35f * deco)
        val drift = sin(time * .4f) * sp * .5f * (1 - lock)
        val strips = 16
        val sh = boxS / strips
        for (row in 0 until strips) {
            val jit = (hash(row * 13.1f + kotlin.math.floor(time * 12)) - .5f) * sp * 1.8f * deco
            val va = .55f + .45f * sin(Math.PI.toFloat() * (row + .5f) / strips)
            var x = -sp + ((drift + jit) % sp)
            while (x < boxS) {
                val x0 = max(0f, x)
                val x1 = min(boxS, x + sp * .5f)
                if (x1 > x0) {
                    val e = Canvas.gauss(((x0 + x1) / 2 - boxS / 2) / (boxS * .32f))
                    cv.color(Pal.key, peak * e * va)
                    cv.shapes.rect(boxX + x0, boxBottom + row * sh, x1 - x0, sh + .5f)
                }
                x += sp
            }
        }
    }

    private fun drawScan() {
        if (outcome != Status.WIN || phase < Phase.OUTRO) return
        val u = outroT / 1.4f
        if (u >= 1f) return
        val y = boxTop - u * boxS
        val s = cv.shapes()
        val a0 = SCAN.set(Pal.accent.r, Pal.accent.g, Pal.accent.b, 0f)
        val a1 = SCAN_END.set(Pal.accent.r, Pal.accent.g, Pal.accent.b, .07f)
        s.rect(boxX, y, boxS, 30f, a1, a1, a0, a0)
        cv.line(boxX, y, boxX + boxS, y, .8f, Pal.accent, .28f)
    }

    /** Instrument bezel: thin frame, corners, graduations. */
    private fun drawBoxFrame() {
        val x0 = boxX
        val y0 = boxBottom
        val x1 = boxX + boxS
        val y1 = boxTop
        for ((ax, ay, bx, by) in listOf(floatArrayOf(x0, y0, x1, y0), floatArrayOf(x1, y0, x1, y1), floatArrayOf(x1, y1, x0, y1), floatArrayOf(x0, y1, x0, y0))) {
            cv.line(ax, ay, bx, by, 1f, Pal.hudMuted, .28f)
        }
        val c = 14f
        for ((cx, cy, sx, sy) in listOf(floatArrayOf(x0, y0, 1f, 1f), floatArrayOf(x1, y0, -1f, 1f), floatArrayOf(x1, y1, -1f, -1f), floatArrayOf(x0, y1, 1f, -1f))) {
            cv.line(cx, cy, cx + sx * c, cy, 1.5f, Pal.accent, .7f)
            cv.line(cx, cy, cx, cy + sy * c, 1.5f, Pal.accent, .7f)
        }
        for (i in 1 until 10) {
            val u = i / 10f
            cv.line(x0, y0 + u * boxS, x0 + 4, y0 + u * boxS, 1f, Pal.hudMuted, .25f)
            cv.line(x0 + u * boxS, y0, x0 + u * boxS, y0 + 4, 1f, Pal.hudMuted, .25f)
        }
    }

    // --- "invisible physics" layer: thin guides, dotted lines ---------------

    private fun drawGuides() {
        if (phase != Phase.AIM) return
        // ghost of the previous shot
        var k = 0
        while (k < lastShotN) {
            cv.disc(px(lastShot[k * 2].toDouble()), py(lastShot[k * 2 + 1].toDouble()), .9f, Pal.hudMuted, .22f)
            k += 4
        }
        aimGuide(aimAngle, powerFrac, Pal.accent, if (dragging && armed) .85f else .45f)
        // "first segment" hint after 5 failures (gameplay-mechanics)
        val hint = level.hint
        if (failures >= 5 && hint != null) {
            val ha = (hint["angle_deg"] as Number).toDouble()
            val hp = (hint["power"] as Number?)?.toDouble() ?: powerMax
            aimGuide(ha, if (powerMax > powerMin) ((hp - powerMin) / (powerMax - powerMin)).toFloat() else 1f, Pal.mid, .6f)
        }
    }

    private fun aimGuide(angleDeg: Double, frac: Float, c: Color, a: Float) {
        val rad = Math.toRadians(angleDeg).toFloat()
        val dx = cos(rad)
        val dy = -sin(rad)
        val x0 = px(level.launcher.x)
        val y0 = py(level.launcher.y)
        val len = 36f + 120f * frac
        var d = LAUNCHER_R + 16f
        while (d < LAUNCHER_R + 16f + len) {
            val fade = 1 - (d - LAUNCHER_R - 16f) / len
            cv.disc(x0 + dx * d, y0 + dy * d, 1.3f, c, a * fade)
            d += 9f
        }
    }

    // --- "matter" layer (flat B rendering) ----------------------------------

    private fun drawObstacles() {
        for (o in level.obstacles) {
            val half = (o.length ?: 0.0) / 2
            val rad = Math.toRadians(o.angleDeg)
            val (ox, oy) = placed(o)
            // a wall may stick out of the box (physics only sees the inside): clip it to the frame
            val ux = cos(rad) * half
            val uy = sin(rad) * half
            val t0 = clipT(ox, oy, ux, uy, -1.0)
            val t1 = clipT(ox, oy, ux, uy, 1.0)
            val ax = px(ox + ux * t0)
            val ay = py(oy + uy * t0)
            val bx = px(ox + ux * t1)
            val by = py(oy + uy * t1)
            when (o.type) {
                "barrier" -> drawBarrier(o, ax, ay, bx, by)
                "mirror" -> {
                    cv.slab(ax, ay, bx, by, 4f, Pal.metal)
                    cv.slab(ax, ay, bx, by, 1.2f, Pal.accentHi, .9f)
                }
                else -> {
                    val t = max(3.5f, ((o.r ?: SEGMENT_HALF_THICKNESS) * boxS).toFloat())
                    cv.slab(ax, ay, bx, by, t, Pal.wall)
                    // rim of the lit face + shadow of the other face
                    val (nx, ny) = normal(ax, ay, bx, by)
                    cv.slab(ax - nx * (t - .75f), ay - ny * (t - .75f), bx - nx * (t - .75f), by - ny * (t - .75f), .75f, Pal.key, .75f)
                    cv.slab(ax + nx * t * .5f, ay + ny * t * .5f, bx + nx * t * .5f, by + ny * t * .5f, t * .5f, Color.BLACK, .25f)
                }
            }
        }
    }

    /** Parameter t ∈ [0, 1] (signed) of the point (ox, oy) + t·(ux, uy) furthest inside the unit box. */
    private fun clipT(ox: Double, oy: Double, ux: Double, uy: Double, sens: Double): Double {
        var t = 1.0
        for ((p, d) in arrayOf(ox to ux * sens, oy to uy * sens)) {
            if (d > 1e-9) t = min(t, (1 - p) / d) else if (d < -1e-9) t = min(t, -p / d)
        }
        return sens * max(0.0, t)
    }

    private fun placed(o: Obstacle): Pair<Double, Double> {
        val m = o.motion ?: return o.x to o.y
        val off = m.offset(clock.toDouble())
        return if (m.axis == 'x') (o.x + off) to o.y else o.x to (o.y + off)
    }

    private fun normal(ax: Float, ay: Float, bx: Float, by: Float): Pair<Float, Float> {
        val dx = bx - ax
        val dy = by - ay
        val l = sqrt(dx * dx + dy * dy).coerceAtLeast(1e-4f)
        return (-dy / l) to (dx / l)
    }

    /** Quarky's energy compared with the barrier threshold at this instant. */
    private fun energy() = sim?.takeIf { phase == Phase.FLIGHT }?.speed ?: aimPower

    private fun drawBarrier(o: Obstacle, ax: Float, ay: Float, bx: Float, by: Float) {
        val thr = Simulation.effectiveThreshold(o, clock.toDouble())
        val open = energy() >= thr
        val hit = max(0f, 1 - (time - barrierHitT) / .5f)
        val col = if (open) Pal.accent else Pal.mix(Pal.key, Pal.danger, .55f + .45f * hit)
        val t = 7f
        val (nx, ny) = normal(ax, ay, bx, by)
        // barrier field: flat fill + shaded half + sharp edges
        cv.slab(ax, ay, bx, by, t, col, if (open) .16f else .26f + .2f * hit)
        cv.slab(ax + nx * t * .5f, ay + ny * t * .5f, bx + nx * t * .5f, by + ny * t * .5f, t * .5f, Color.BLACK, .16f)
        cv.slab(ax - nx * (t - 1), ay - ny * (t - 1), bx - nx * (t - 1), by - ny * (t - 1), 1f, col)
        cv.slab(ax + nx * (t - 1), ay + ny * (t - 1), bx + nx * (t - 1), by + ny * (t - 1), 1f, col, if (open) .5f else 1f)
        if (!open) {
            // threshold hatching: doubles the colour (readable with colour blindness)
            val n = 7
            for (i in 1 until n) {
                val u = i / n.toFloat()
                val cx = ax + (bx - ax) * u
                val cy = ay + (by - ay) * u
                cv.line(cx - nx * t, cy - ny * t - 3, cx + nx * t, cy + ny * t + 3, 1f, col, .5f)
            }
        }
        // emitters at both ends
        val dx = bx - ax
        val dy = by - ay
        val l = sqrt(dx * dx + dy * dy).coerceAtLeast(1e-4f)
        for (sgn in intArrayOf(-1, 1)) {
            val ex = if (sgn < 0) ax else bx
            val ey = if (sgn < 0) ay else by
            val mx = ex + sgn * dx / l * 5
            val my = ey + sgn * dy / l * 5
            cv.slab(mx - nx * (t + 6), my - ny * (t + 6), mx + nx * (t + 6), my + ny * (t + 6), 4.5f, Pal.metal)
            cv.slab(mx - nx * (t + 3), my - ny * (t + 3), mx + nx * (t + 3), my + ny * (t + 3), .8f, col, .8f)
        }
    }

    private fun photonPos(i: Int): Pair<Float, Float> {
        val p = level.photons[i]
        val m = p.motion ?: return px(p.x) to py(p.y)
        val off = m.offset(clock.toDouble())
        return if (m.axis == 'x') px(p.x + off) to py(p.y) else px(p.x) to py(p.y + off)
    }

    /** Photon collected during this flight — it only counts (and stays taken) if the target is reached. */
    private fun photonCounted(i: Int): Boolean {
        val s = sim ?: return false
        return s.collected[i] && (phase == Phase.FLIGHT || outcome == Status.WIN)
    }

    private fun drawPhotons() {
        for (i in level.photons.indices) {
            val collected = photonCounted(i)
            if (collected) continue
            val (x, y) = photonPos(i)
            val e = i % 3
            val col = Pal.energy[e]
            val k = (level.photons[i].r * boxS).toFloat() / 9.5f
            val missed = phase == Phase.RESULT && outcome == Status.WIN
            val pulse = 1 + .08f * sin(time * 4 + i) + if (missed) .25f * max(0f, sin(time * 5)) else 0f
            cv.additive(true)
            cv.glow(x, y, 11f * k * pulse, col, .3f)
            cv.additive(false)
            val n = Pal.energyRays[e]
            for (j in 0 until n) {
                val an = j.toFloat() / n * TAU + time * .4f
                cv.line(x + cos(an) * 6 * k, y + sin(an) * 6 * k, x + cos(an) * 9.5f * k, y + sin(an) * 9.5f * k, .9f, Pal.mix(col, Pal.white, .3f), .8f)
            }
            // flat diamond + light facet
            val d = 3.8f * k * 1.41f
            cv.color(col)
            cv.shapes.triangle(x, y + d, x - d, y, x + d, y)
            cv.shapes.triangle(x, y - d, x - d, y, x + d, y)
            cv.color(Pal.white, .75f)
            cv.shapes.triangle(x, y + d, x - d, y, x, y)
            // random sparkles
            for (j in 0 until 3) {
                val cyc = time * 1.3f + i * .37f + j * .33f
                val n2 = kotlin.math.floor(cyc)
                val ph = cyc - n2
                val an = hash(n2 * 7 + j + i) * TAU
                val dd = (6 + hash(n2 * 3 + j + i * 2) * 8) * k
                val sz = sin(ph * Math.PI.toFloat()) * 3.4f
                cv.glint(x + cos(an) * dd, y + sin(an) * dd, sz, Pal.white, .95f * sin(ph * Math.PI.toFloat()))
            }
        }
    }

    /** Portal: rotating flat concentric discs, glowing core, particles drawn in. */
    private fun drawPortal() {
        val (x, y) = targetPos()
        val r = (level.target.r * boxS).toFloat() * .55f
        val flare = if (outcome == Status.WIN && phase >= Phase.OUTRO) max(0f, 1 - abs(outroT - OUTRO) / .5f) else 0f
        cv.additive(true)
        cv.glow(x, y, r * 3.6f, Pal.key, .12f + .3f * flare)
        cv.additive(false)
        cv.disc(x, y, r * 2.35f, Pal.key, .12f)
        val rings = arrayOf(Triple(1.15f, 3, .7f), Triple(1.62f, 5, -.45f), Triple(2.12f, 9, .28f))
        val cols = arrayOf(Pal.key, Pal.mid, Pal.accent)
        val widths = floatArrayOf(2.2f, 1.5f, 1f)
        for ((i, ring) in rings.withIndex()) {
            val (rf, n, sp) = ring
            val rr = r * rf * (1 + .035f * sin(time * 2 + i * 1.3f))
            val rot = time * sp * (1 + flare * 5)
            val seg = TAU / n
            for (j in 0 until n) cv.arc(x, y, rr, rot + j * seg, rot + j * seg + seg * .62f, widths[i], cols[i])
        }
        val cr = r * (.95f + .08f * sin(time * 3)) * (1 + flare * .7f)
        cv.disc(x, y, cr * .8f, Pal.key)
        cv.disc(x, y, cr * .42f, Pal.white)
        for (i in 0 until 12) {
            val ph = (time * .45f + i / 12f) % 1f
            val rad = r * 2.6f * (1 - ph) + r * .3f
            val an = i * 2.39f + ph * 3.2f
            cv.disc(x + cos(an) * rad, y + sin(an) * rad, 1.1f, if (i % 3 == 0) Pal.accentHi else Pal.keyHi, sin(ph * Math.PI.toFloat()) * .8f)
        }
    }

    /** Launcher: accelerator ring, coils, continuous energy gauge, oriented nozzle. */
    private fun drawLauncher() {
        val x = px(level.launcher.x)
        val y = py(level.launcher.y)
        val ang = -Math.toRadians(aimAngle).toFloat()
        val en = if (phase == Phase.AIM) powerFrac else 0f
        val rr = LAUNCHER_R
        cv.ring(x, y, rr, 6.5f, Pal.metal)
        cv.ring(x, y, rr, 1.2f, Pal.mix(Pal.key, Pal.white, .2f), .35f + .5f * en)
        for (i in 0 until 8) {
            val a = i / 8f * TAU + ang + TAU / 16
            val e = if (dragging && armed) (.5f + .5f * sin(time * 12 - i * .9f)) * en else 0f
            val cx = x + cos(a) * rr
            val cy = y + sin(a) * rr
            cv.color(Pal.coil)
            cv.shapes.rect(cx - 4.6f, cy - 3.2f, 4.6f, 3.2f, 9.2f, 6.4f, 1f, 1f, Math.toDegrees(a.toDouble()).toFloat())
            if (e > .02f) cv.disc(cx, cy, 1.4f, Pal.keyHi, e)
        }
        // energy gauge (continuous) behind the nozzle
        val span = 1.6f
        val a0 = ang + Math.PI.toFloat() - span / 2
        cv.arc(x, y, rr + 9, a0, a0 + span, 3.4f, Pal.key, .2f)
        if (phase == Phase.AIM) cv.arc(x, y, rr + 9, a0, a0 + span * max(.02f, powerFrac), 3.4f, Pal.key, .95f)
        // nozzle
        val cx = cos(ang)
        val cy = sin(ang)
        val nx = -cy
        val ny = cx
        val s = cv.shapes()
        cv.color(Pal.metal)
        val p1x = x + cx * (rr + 1) + nx * 5.5f; val p1y = y + cy * (rr + 1) + ny * 5.5f
        val p2x = x + cx * (rr + 12) + nx * 3.4f; val p2y = y + cy * (rr + 12) + ny * 3.4f
        val p3x = x + cx * (rr + 12) - nx * 3.4f; val p3y = y + cy * (rr + 12) - ny * 3.4f
        val p4x = x + cx * (rr + 1) - nx * 5.5f; val p4y = y + cy * (rr + 1) - ny * 5.5f
        s.triangle(p1x, p1y, p2x, p2y, p3x, p3y)
        s.triangle(p1x, p1y, p3x, p3y, p4x, p4y)
        cv.line(p2x, p2y, p3x, p3y, 1.4f, Pal.keyHi, .5f + .5f * en)
        // muzzle flash
        if (phase == Phase.FLIGHT) {
            val u = (time - flightStart) / .45f
            if (u < 1f) {
                val fx = x + cx * (rr + 12)
                val fy = y + cy * (rr + 12)
                cv.ring(fx, fy, 4 + u * 24, 2 * (1 - u) + .4f, Pal.white, (1 - u) * .9f)
                cv.additive(true)
                cv.glow(fx, fy, 18 * (1 - u) + 4, Pal.keyHi, (1 - u) * .8f)
                cv.additive(false)
            }
        }
    }

    /** Quarky's trail: a simple line (B style) that fades out. */
    private fun drawTrail() {
        if (phase != Phase.FLIGHT && phase != Phase.OUTRO) return
        val n = min(trailN, TRAIL_DRAWN)
        var lx = Float.NaN
        var ly = Float.NaN
        for (k in 0 until n) {
            val i = (trailHead - n + k + TRAIL) % TRAIL
            val x = px(trail[i * 2].toDouble())
            val y = py(trail[i * 2 + 1].toDouble())
            val fade = if (phase == Phase.OUTRO) max(0f, 1 - outroT / .6f) else 1f
            if (!lx.isNaN() && abs(x - lx) < 40 && abs(y - ly) < 40) cv.line(lx, ly, x, y, 2f, Pal.key, .55f * (k.toFloat() / n) * fade)
            lx = x; ly = y
        }
    }

    private fun drawBursts() {
        for (b in burstT.indices) {
            val u = (time - burstT[b]) / .5f
            if (u < 0f || u >= 1f) continue
            val col = Pal.energy[burstC[b]]
            val x = burstX[b]
            val y = burstY[b]
            cv.additive(true)
            cv.ring(x, y, 4 + u * 20, 1.6f * (1 - u) + .3f, col, (1 - u) * .9f)
            for (i in 0 until 8) {
                val an = i / 8f * TAU + .3f
                val d = 4 + u * 22
                cv.glint(x + cos(an) * d, y + sin(an) * d, 2.6f * (1 - u), Pal.white, 1 - u)
            }
            cv.glow(x, y, 14 * (1 - u) + 2, col, (1 - u) * .7f)
            cv.additive(false)
        }
    }

    /** Layer 3: foreground dust, then grain and vignette (≤ 3%). */
    private fun drawForeground() {
        val qx = pose.x - w / 2
        for (d in dust) {
            val x = ((d[0] * w - qx * .1f + time * 3 * d[3]) % w + w) % w
            val y = ((d[1] * h + time * 5 * d[3]) % h + h) % h
            cv.disc(x, y, d[2], Pal.hud, .1f)
        }
        val b = cv.sprites()
        b.setColor(0f, 0f, 0f, .03f)
        b.draw(cv.vignette, -w * .1f, -h * .1f, w * 1.2f, h * 1.2f)
        b.setColor(1f, 1f, 1f, .03f)
        val o = (time * 997) % 128
        b.draw(cv.grain, 0f, 0f, w, h, o / 128f, 0f, o / 128f + w / 128f, h / 128f)
    }

    // --- HUD (bezel) -----------------------------------------------------------

    private fun drawTopBar() {
        val f = fonts ?: return
        val yc = h - TOP_BAR / 2 - 10
        // back to the map
        roundButton(Btn.BACK, MARGIN + 18, yc) { x, y ->
            cv.line(x + 3, y + 7, x - 4, y, 1.8f, Pal.hud)
            cv.line(x - 4, y, x + 3, y - 7, 1.8f, Pal.hud)
        }
        // Photon counter of the current shot (they become the stars)
        for (i in 0 until 3) {
            val x = MARGIN + 52f + i * 17
            val got = i < level.photons.size && photonCounted(i)
            val col = Pal.energy[i % 3]
            val d = 5.5f
            if (got) {
                cv.color(col)
                cv.shapes.triangle(x, yc + d, x - d, yc, x + d, yc)
                cv.shapes.triangle(x, yc - d, x - d, yc, x + d, yc)
            } else {
                cv.line(x, yc + d, x + d, yc, 1.2f, Pal.hudMuted, .7f)
                cv.line(x + d, yc, x, yc - d, 1.2f, Pal.hudMuted, .7f)
                cv.line(x, yc - d, x - d, yc, 1.2f, Pal.hudMuted, .7f)
                cv.line(x - d, yc, x, yc + d, 1.2f, Pal.hudMuted, .7f)
            }
        }
        // level title
        text(f.uiBold, info.title, w / 2, yc + 12, Pal.hud, Align.center)
        text(f.monoSmall, info.subtitle.uppercase(), w / 2, yc - 6, Pal.hudMuted, Align.center)
        // restart
        roundButton(Btn.RESET, w - MARGIN - 18, yc) { x, y ->
            cv.arc(x, y, 7f, .5f, 5.3f, 1.8f, Pal.hud)
            val ax = x + cos(.5f) * 7
            val ay = y + sin(.5f) * 7
            val s2 = cv.shapes()
            cv.color(Pal.hud)
            s2.triangle(ax + 4f, ay + 1f, ax - 3f, ay + 3.5f, ax - 1f, ay - 4f)
        }
    }

    private inline fun roundButton(id: Btn, x: Float, y: Float, glyph: (Float, Float) -> Unit) {
        cv.disc(x, y, 18f, Pal.bezel, .9f)
        cv.ring(x, y, 18f, 1f, Pal.hudMuted, .45f)
        glyph(x, y)
        buttons.add(Button(id, x - 18, y - 18, 36f, 36f))
    }

    private fun drawPanel() {
        val f = fonts ?: return
        val x0 = MARGIN
        val x1 = w - MARGIN
        val top = boxBottom - 14
        val bottom = MARGIN
        cv.color(Pal.bezel, .9f)
        cv.shapes.rect(x0, bottom, x1 - x0, top - bottom)
        for ((ax, ay, bx, by) in listOf(floatArrayOf(x0, bottom, x1, bottom), floatArrayOf(x1, bottom, x1, top), floatArrayOf(x1, top, x0, top), floatArrayOf(x0, top, x0, bottom))) {
            cv.line(ax, ay, bx, by, 1f, Pal.hudMuted, .22f)
        }
        val pad = 16f
        if (phase == Phase.RESULT) drawResult(f, x0 + pad, x1 - pad, top - pad, bottom + pad)
        else drawReadouts(f, x0 + pad, x1 - pad, top - pad, bottom + pad)
    }

    private fun drawReadouts(f: Fonts, left: Float, right: Float, top: Float, bottom: Float) {
        var y = top
        text(f.monoSmall, txt.readingsHeader, left, y, Pal.hudMuted)
        text(f.mono, "${txt.angle} ${signed(aimAngle)}°", right, y, Pal.hud, Align.right)
        y -= 40
        val en = energy()
        meter(f, left, right, y, txt.energy, fmt(en), en, null, Pal.key)
        y -= 44
        val barrier = level.obstacles.firstOrNull { it.type == "barrier" }
        if (barrier != null) {
            val thr = Simulation.effectiveThreshold(barrier, clock.toDouble())
            val m = barrier.thresholdMotion
            val base = barrier.energyThreshold ?: 0.6
            val band = if (m != null) (base - abs(m.amplitude)) to (base + abs(m.amplitude)) else null
            meter(f, left, right, y, txt.threshold, fmt(thr), thr, band, Pal.danger, en)
            val open = en >= thr
            text(f.monoSmall, if (open) txt.passes else txt.blocked, right, y + 17, if (open) Pal.accent else Pal.danger, Align.right)
            y -= 40
        }
        val msg = when {
            phase == Phase.AIM && failures >= 5 && level.hint != null -> txt.hint
            phase == Phase.AIM -> txt.aimHelp
            time - flashT < 1.6f && flash.isNotEmpty() -> flash
            else -> ""
        }
        if (msg.isNotEmpty()) wrapped(f.ui, msg, left, max(bottom + 34, y), right - left, Pal.hud)
    }

    /** Horizontal instrument gauge, scale 0 → 1.1. */
    private fun meter(f: Fonts, left: Float, right: Float, y: Float, label: String, value: String, v: Double, band: Pair<Double, Double>?, c: Color, compare: Double? = null) {
        text(f.monoSmall, label, left, y + 17, Pal.hudMuted)
        text(f.mono, value, right - 60, y + 18, Pal.hud, Align.right)
        val by = y - 2
        val wdt = right - left
        fun sx(u: Double) = left + (u / SCALE_MAX).toFloat().coerceIn(0f, 1f) * wdt
        cv.line(left, by, right, by, 1f, Pal.hudMuted, .35f)
        for (i in 0..11) {
            val tx = sx(i / 10.0)
            cv.line(tx, by - 3, tx, by + (if (i % 5 == 0) 4 else 2), 1f, Pal.hudMuted, .35f)
        }
        if (band != null) {
            cv.color(c, .18f)
            cv.shapes.rect(sx(band.first), by - 3, sx(band.second) - sx(band.first), 6f)
        }
        if (compare == null) cv.line(left, by, sx(v), by, 3f, c)
        else cv.line(sx(compare), by - 6, sx(compare), by + 6, 1.5f, Pal.key, .8f)
        cv.line(sx(v), by - 7, sx(v), by + 7, 3f, c)
    }

    private fun drawResult(f: Fonts, left: Float, right: Float, top: Float, bottom: Float) {
        var y = top
        val win = outcome == Status.WIN
        text(f.monoSmall, txt.resultHeader, left, y, Pal.hudMuted)
        y -= 18
        val head = when (outcome) {
            Status.WIN -> txt.outcomeWin
            Status.TIMEOUT -> txt.outcomeTimeout
            else -> txt.outcomeLost
        }
        text(f.title, head, left, y, Pal.hud)
        if (win) {
            for (i in 0 until 3) cv.star(right - 12 - (2 - i) * 28f, y - 9, 11f, i < stars, if (i < stars) Pal.key else Pal.hudMuted, if (i < stars) 1f else .7f)
        }
        y -= 34
        val line = when {
            win && stars == 3 -> txt.msgPerfect
            win -> txt.msgWin
            outcome == Status.TIMEOUT -> txt.msgTimeout
            else -> txt.msgLost
        }
        y = wrapped(f.ui, line, left, y, right - left, Pal.hud) - 12
        if (win && info.codex.isNotEmpty()) {
            y = wrapped(f.ui, info.codex, left, y, right - left, Pal.mid) - 4
            text(f.monoSmall, txt.codexSignature, right, y, Pal.hudMuted, Align.right)
        }
        // actions
        val bw = (right - left - 12) / 2
        val bh = 44f
        val byy = bottom
        actionButton(Btn.RETRY, left, byy, bw, bh, txt.retry, primary = !win || stars < 3, f = f)
        actionButton(Btn.MAP, left + bw + 12, byy, bw, bh, if (win) txt.next else txt.map, primary = win && stars == 3, f = f)
    }

    private fun actionButton(id: Btn, x: Float, y: Float, bw: Float, bh: Float, label: String, primary: Boolean, f: Fonts) {
        if (primary) {
            cv.color(Pal.key)
            cv.shapes.rect(x, y, bw, bh)
        } else {
            cv.line(x, y, x + bw, y, 1.2f, Pal.hudMuted, .7f)
            cv.line(x + bw, y, x + bw, y + bh, 1.2f, Pal.hudMuted, .7f)
            cv.line(x + bw, y + bh, x, y + bh, 1.2f, Pal.hudMuted, .7f)
            cv.line(x, y + bh, x, y, 1.2f, Pal.hudMuted, .7f)
        }
        text(f.mono, label, x + bw / 2, y + bh / 2 + 6, if (primary) Pal.ink else Pal.hud, Align.center)
        buttons.add(Button(id, x, y, bw, bh))
    }

    private fun text(font: BitmapFont, s: String, x: Float, y: Float, c: Color, align: Int = Align.left) {
        val b = cv.sprites()
        font.color = c
        layout.setText(font, s, c, 0f, align, false)
        font.draw(b, layout, x, y)
    }

    /** Multi-line text; returns the y below the block. */
    private fun wrapped(font: BitmapFont, s: String, x: Float, y: Float, width: Float, c: Color): Float {
        val b = cv.sprites()
        layout.setText(font, s, c, width, Align.left, true)
        font.draw(b, layout, x, y)
        return y - layout.height - 6
    }

    override fun dispose() {
        cv.dispose()
        fonts?.dispose()
    }

    private companion object {
        const val MIN_W = 390f
        const val MIN_H = 760f
        const val MARGIN = 16f
        const val TOP_BAR = 84f
        const val QUARKY_R = 13f
        const val LAUNCHER_R = 24f
        const val DEAD_ZONE = 14f
        const val PULL_RANGE = 150f
        const val OUTRO = .8f
        const val TRAIL = 512
        const val TRAIL_DRAWN = 45
        const val SCALE_MAX = 1.1
        val RAY = Color()
        val RAY_END = Color()
        val SCAN = Color()
        val SCAN_END = Color()

        fun fmt(v: Double) = String.format(java.util.Locale.ROOT, "%.2f", v)
        fun signed(v: Double) = if (v > 0) "+${v.toInt()}" else if (v < 0) "−${(-v).toInt()}" else "0"
    }
}
