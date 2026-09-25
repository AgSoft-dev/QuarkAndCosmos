# Quark & Cosmos — Roadmap & TODO

> Working plan for the Android game and its Python level builder. It's built from an audit of `CLAUDE.md`, the 3 skills (`art-direction`, `storytelling`, `gameplay-mechanics`), the Stage 2 HTML mockups and the Stage 3 engine (`stage3-physics-engine/`) as of 2026-09-25.
>
> **Rules for using this file**
> - The stage-gating rule from `CLAUDE.md` still applies. Items tagged **[GATE]** need an explicit decision from the user before anything downstream starts. Items for a future stage stay planning-only until the current stage is validated.
> - **Scope tags:** `[BETA]` = closed-test build (Quantum world only, 7 concepts, 7 levels). `[FULL]` = full release (4 other scales, intra-concept progression, cross-concept mix levels). Do `[BETA]` first, every time.
> - **Cloud sessions:** each `###` block is sized to be one cloud session on its own branch → PR. Blocks marked ⇄ can run in parallel. Blocks marked → depend on the block before them.

---

## 0. Audit findings (read first)

What already works well, and what this plan builds on:
- The two-layer visual rule ("matter" vs "invisible physics") is strong. Keep it as the backbone of the art direction.
- Portal-target and sparkling-Photon concepts, the lab-mentor narrative and the Codex framed as the scientist's logbook are all good, reusable decisions.
- The in-flight "tap" and oscillating elements are the right answer to "Angry Birds without Cut the Rope's tension".
- The Python engine is small, has no dependencies, is deterministic and runs from a CLI. That's a solid base.

Problems found in the current engine and levels (checked by running `cli.py validate` on all 7 levels):
- [x] **3-star system not actually implemented:** 6/7 levels had **1 Photon** (only `intrication` had 3), so 3 stars couldn't be earned. `gameplay-mechanics` requires 3 per level. *Done: the validator now places 3 Photons along the most robust solution (`place_photons`), and all 7 levels reach 3/3.*
  - [x] Follow-up: in 5/7 levels every winning shot also collected all 3 Photons. *Done: `engine/stars.py` places Photons by ray tracing so the share of valid shots earning ≥ k stars follows a truncated gaussian `exp(−k²/2σ²)`, with σ shrinking with difficulty. `python3 cli.py report` writes CSV/JSON/HTML (progression curves + level mini-maps) for review.*
  - [ ] Difficulty ceilings (see the report's ⚠ flags): superposition (from diff. 2), intrication (diff. 2), incertitude (3 distinct paths only), dualité, quantification and spin (diff. 3) can't narrow the 3-star window to target, because their valid paths are too alike. Fix in level geometry (difficulty-2/3 templates with more path diversity), not in placement.
  - [x] The generator used to vary only Photon placement with difficulty. *Done: 3 distinct layouts per concept (1 discover → 2 sequence → 3 chain), 21 levels, 0 bypasses (`must_contact`), and the 3rd star favours richer alternative routes. See the table in `gameplay-mechanics`.*
  - [ ] **[GATE] Beta scope:** `CLAUDE.md` says ~1 level per concept (7). Ship 7 (difficulty 1 only), 14, or all 21 in the closed test?
  - [x] Superposition barely gets harder (25% → 26% → 21% winning shots): a splitter snaps every shot onto the same arm, so there's little to scale. It needs the two-ghost redesign (§2.2). *Done (user decision): two-ghost superposition. Now 17% → 10% → 6% winning shots, 0 bypasses.*
  - [ ] Remaining 3★ ceilings at difficulty 3: quantification (a single notch works, so few distinct paths) and spin (fixed deflections). See the report.
  - [ ] Oscillations are phase-locked to the launch (the apparatus "starts" with the shot). Confirm this in the game design, or add a launch-timing parameter to the solver.
  - [ ] Full release: stars unlock the next levels/worlds (threshold ≈ 2★ average on the previous world, never 3★ everywhere); calibrate on closed-test data.
- [x] **Degenerate in-flight taps:** the best solution for `dualite` and `intrication` was `tap_time = 0.0`. Tapping at launch makes the tap equivalent to a pre-launch setting, which defeats the rule "every concept depends on time during flight". *Done: `TAP_MIN_TIME = 0.1 s`; earlier taps are excluded from the search, and a test enforces it. Game side (decided): a tap before 0.1 s is ignored and the tap stays available.*
  - [x] Follow-up: in `dualite`, any tap before contact worked (a window, not a timing). *Done: difficulties 2–3 put the tap window between two contacts (particle bounce, then wave crossing).*
- [x] **Brittle / over-tight levels:** `tunnel` had 2 solutions in the whole grid, `quantification` had 9 and `dualite` had 7. `spin` restricted the angle to `[-12, -11]` (the solution was effectively hard-coded). *Done: `tolerance` and `three_star_tolerance` are in the report and the JSON, and a test requires ≥ 5%. Tunnel went from 4% to 21% with continuous power sampling, spin's angle range is now `[-20, 0]`, and all 7 levels are between 14% and 62%.*
- [ ] **Physics mis-vulgarisation (tunnel):** the code and the Codex line ("Assez d'énergie, et même un mur n'est plus vraiment un mur" — "with enough energy, even a wall isn't really a wall") describe *classically going over* a barrier. Quantum tunnelling is the opposite: the particle gets through **without** enough energy, with a probability that drops fast as the barrier gets thicker. See §2.
- [x] **Superposition modelled as a deterministic splitter** chosen by impact point. That reads as "a deflector", not as "two paths at once". See §2 for a mechanic that shows both branches. *Done: a flat beam splitter makes a transmitted and a reflected ghost; a tap measures (nearest copy to a detector wins, its Photons only); target needs a measured Quarky; a copy crashing before the measure = decoherence fail. Spec: `docs/physics-spec.md` §7 bis.*
- [ ] **`quantification` isn't distinct:** discrete power "notches" (`choice` values) are already used by every other level, so the concept has no mechanic of its own.
- [x] **Handlers re-applied on every step of contact:** a spin pole deflected N × `kick_deg` (N depending on speed), and a barrier re-checked its oscillating threshold on every step. Handlers now fire once per contact. The old `spin` level was only solvable because of this bug, so its target was moved and its angle range widened.
- [x] **Stale references:** `concepts.py` / `generator.py` still say "8 concepts", `concepts.py` documents a `trap` event left over from the removed Décohérence concept, and `gameplay-mechanics` says "ex. 8 concepts pour le Quantique".
- [x] **No tests, no `pyproject.toml`, no level schema version, no README.** *Done: `tests/` (38 tests, including a check that the committed JSON is identical to the generator output), `pyproject.toml`, `schema_version: 1`, and `stage3-physics-engine/README.md`.*
  - [x] Follow-up (§4.1): the JSON export still ships `param_space` and the full reference solution in the game payload; split it into `level.json` / `level.meta.json`. *Done: `schema_version: 2`. `levels/<nom>.json` (shipped: geometry, Photons, `max_wall_bounces`, `param_space` for the dials, `hint.params`) + `levels/meta/<nom>.meta.json` (dev: `must_contact`, solvability, tolerances, bypasses, full reference solution, star profile). `cli.py validate` re-reads `must_contact` from the sibling meta. Tests check both files against the generator, no dev field in the shipped file, no stale file.*
- [x] **No agents exist** (`.claude/agents/` is missing), no `.claude/settings.json`, and no CI. *CI done (`.github/workflows/level-engine.yml` runs the tests). Done: `.claude/agents/` has `physics-reviewer` (read-only), `level-designer`, `level-qa` and `art-director`, each naming its skills and the stage it may act on (`android-dev` waits for Stage 5). `.claude/settings.json` allows `python3 cli.py *`, `python3 -m pytest*`, `pip install -e*`, with a SessionStart hook that installs pytest in cloud sessions only (never blocks the session).*
- [x] **The Stage 2 mockup's physics is separate JS code**, not the Stage 3 rules. It will drift from the engine. We need one source of truth for the physics (see §4.3). *Done (minimal step): `docs/physics-spec.md` specifies the deterministic contract (fixed `DT`, step order, shapes, handlers, oscillations, tap, `max_wall_bounces`) with the mockup's known drifts listed; the mockup's script now says it is not the source of truth. Replacing it with a JSON-driven viewer and golden trajectories stays in §4.1/§4.3.*

---

## Phase 1 — Art direction v2: from "cute" to "cinematic lab" `[GATE]`

> Note: `art-direction` is marked validated and says not to reopen it without an explicit user decision. This request *is* that decision, but only for the rendering style. The palette per scale, the two-layer rule and Quarky's DNA are **kept**. The change is illustrated/Cut-the-Rope-style matter → **luminous neon vector + volumetric glow**.

### 1.1 Style bible ⇄
- [x] Write a 1-page style thesis: **"a retro-futuristic physics lab seen through an instrument"**. Every scale is what a lab instrument would show at that magnification: particle-detector bubble chamber → electron microscope → the lab bench itself → orbital telescope → deep-field cosmology. The *instrument* is the diegetic frame and the HUD is its bezel. *Done: in `art-direction` (DA v2).*
- [x] Reference board with specific traits to borrow:
  - *Monument Valley*: flat-shaded geometry, a strict palette of 3–4 colours per scene, negative space.
  - *God of Light*: additive glow beams, light as the main actor, dark backgrounds.
  - *Alto's Odyssey*: layered parallax silhouettes, a colour grade that shifts with time/scale, calm ambient motion.
  - *Osmos / Lumino City*: a sense of scale, soft depth of field.
- [x] Rendering recipe (must be cheap on mobile):
  - Vector shapes + one **additive bloom** pass (downsampled, 2 blur iterations).
  - A **single colour-grade LUT per scale**.
  - Film grain / vignette at ≤ 3% opacity.
  - No per-object real-time lights.
- [x] Update the two-layer rule for glow: **matter** = solid core + soft rim glow and specular highlight (volume stays readable). **Invisible physics** = thin additive lines that pulse along their direction of flow, never bloomed as strongly as the matter layer. *Done: in `art-direction` (DA v2).*
- [x] Colour contract per scale: the existing key colour (`#f472b6`, `#facc15`, `#4ade80`, `#a78bfa`, `#818cf8`) plus 1 complementary accent, 1 deep background, 1 "danger/threshold" colour. Check contrast ≥ 4.5:1 for HUD text and do a colour-blind pass (deuteranopia and protanopia). Force colours must also differ by **line style**, which the existing rule already requires. *Done for Quantum (key `#f472b6`, accent `#67e8f9`, background `#0a0612`, threshold `#fb923c`, all HUD pairs ≥ 4.5:1); the other scales get theirs when their world is designed.*
- [x] **[GATE]** User picks between 2–3 style frames (same Quantum level, 3 treatments) before any asset production. *Decided: mostly **B** (flat lab, most readable) with **C's background** (3-layer parallax, grain/vignette ≤ 3%); portrait kept. POC: `stage1-art-direction/poc-v2/`.*
- [ ] Produce the combined "B + C background" style frame (and the object states idle / hover / dragged / active / disabled) as the reference sheet for assets.

### 1.2 Quarky v2 ⇄
- [x] Redesign as a **luminous particle-creature**: a glowing core with a jelly outer membrane, big expressive eyes kept (the emotional anchor). Silhouette readable at 48 px. *Approved by the user (Quarky v2: yes); spec in `art-direction`.*
- [ ] Per-scale mutation sheet with the existing mutations kept but rendered with light:
  - Quantum: 2–3 ghosted phase-copies, flickering.
  - Atomic: electron ring plus a charge satellite that glows + / −.
  - Macro: canonical form with a real specular highlight.
  - Orbital: solar-sail fins and a light trail.
  - Cosmic: a lensed/skewed silhouette.
- [x] Expression set (8 states): idle, aim-tension, launch, in-flight, collect, near-miss, success-warp, fail-fizzle. Each is ≤ 12 frames or procedural (squash/stretch driven by velocity). *Procedural, shown in the POC.*
- [x] Wave mode vs particle mode (Dualité): particle = sharp body. Wave = body dissolves into concentric ripples that travel along the trajectory.

### 1.3 Diegetic objects — "lab instruments" catalogue ⇄
Each object gets a design sheet with: idle / hover / dragged / active / disabled states, the adjustment handle (rotation ring, intensity dial), the force-line style, and its sound cue.

- [ ] **Launcher**: a mini particle accelerator (ring + charging coils). Charging notches glow one by one, which is also the visual vocabulary for *Quantification*.
- [ ] **Mirror / reflector**: a polished glass plate with a thin emissive edge. The Macro version is a bench optic on a mount.
- [ ] **Prism / beam splitter**: a crystal with internal refraction lines. It's also the new *Superposition* splitter (see §2).
- [ ] **Potential barrier (tunnel)**: a translucent energy wall whose **thickness** is shown visually and has animated "probability fringes".
- [ ] **Entangled pair**: twin crystals linked by a faint, never-straight filament. They flash in sync.
- [ ] **Spin field / Stern–Gerlach magnet**: an asymmetric magnet with field lines. Arrow colour means up / down.
- [ ] **Ion emitter (+/−)** `[FULL]`: a charged sphere with radial field lines. Red/blue are forbidden as the *only* cue: add + / − glyphs.
- [ ] **Gravity well / planet** `[FULL]`: a sphere with a visible funnel grid distortion. Orbital path preview in dashed violet.
- [ ] **Black hole** `[FULL]`: pure black disc, lensing shader on the background, accretion ring.
- [ ] **Portal target**: keep the existing concept (rotating concentric rings, a core that pulls you in) and add a **warp transition** that becomes the scale-change cinematic.
- [ ] **Photon collectible**: keep the sparkle. Add a **colour = energy** encoding (see §2 Quantification: E = hν).

### 1.4 Per-scale environment & level aesthetics ⇄
| Scale | Instrument frame | Background layers (parallax 3) | Ambient FX | Camera | Grade |
|---|---|---|---|---|---|
| Quantum | Bubble-chamber / detector cavity | Near-black void → faint interference fringes → drifting virtual-particle pairs | Probability "fog" that shimmers when Quarky is superposed | Fixed, tight, portrait | Magenta / cool |
| Atomic | Electron-microscope view | Lattice of atoms (blurred) → electron clouds → nucleus glow | Orbital shells pulse at the "energy level" frequency | Fixed, radial | Amber |
| Macro | The lab bench (first reveal of the scientist) | Bench silhouettes → equipment → window light | Dust motes in light shafts | Lateral travelling | Green / warm neutral |
| Orbital | Telescope eyepiece | Starfield → planet limb → nebula | Solar wind streaks | Free zoom | Violet |
| Cosmic | Deep-field / spacetime grid | Galaxies → warped grid → CMB-like noise | The grid bends with gravity (gameplay-reactive) | Zoom + distortion | Indigo |

- [ ] Rule: **the background must never compete with the trajectory**. Keep background luminance ≤ 20% of the matter layer, with no high-frequency detail behind the play area.
- [ ] Rule: **the environment reacts to the result.** On success the background briefly "resolves" (fringes lock into a clean pattern). On failure it decoheres (noise). This is cheap, feels good and teaches something.
- [ ] Scale-transition cinematic (5–8 s, skippable): zoom out through the portal. Quantum cavity → atom → the apparatus on the bench → the lab window → Earth → the cosmic web. This is the game's signature moment and should be shown in the store trailer.
- [x] HUD skin as the **instrument bezel**: a thin line frame, readout typography (one monospaced display font + one humanist UI font, both OFL-licensed), and star counter / reset / object tray kept in their current positions. *Done in `art-direction` (JetBrains Mono + Fira Sans).*
- [x] Update the `art-direction` skill with v2 once validated (keep a short "v1 → v2 decisions" changelog).

### 1.5 Narrative polish ⇄
- [ ] **[GATE]** Name the scientist. Proposal: gender-neutral and short (e.g. "Dr. Lume"). Also lock Quarky's final name.
- [ ] Write the 5 "naïve questions" that open each scale (e.g. Quantum → Atomic: "Qu'est-ce qui est fait de moi ?" — "What am I made of?").
- [ ] A Codex entry template (see §2.3) written in the scientist's voice. Length ≤ 280 characters per pop-up, and the Codex page ≤ 120 words.

---

## Phase 2 — High-school physics alignment

> Target: **lycée / high school** (15–18). Principle: *one concept = one intuitive rule the player can predict before launching*. The puzzle is solved by using the physics, never by memorising it. Every Codex entry ends with a real-world anchor (a device, an experiment, a historical mission).

### 2.1 Curriculum mapping `[GATE]`
- [ ] Label each concept **Core** (in the French *programme de Seconde / 1ère / Terminale* or an equivalent international curriculum) or **Enrichment** (beyond the curriculum but explainable with a single sentence). Show this label in the Codex ("Au programme" / "Pour aller plus loin").
- [ ] Have a physics teacher review the 7 beta Codex entries before the closed test. Budget for 1 external reviewer.

### 2.2 Concept → mechanic → feedback tables

#### Quantum world `[BETA]` (keep the 7 concepts in the `CLAUDE.md` order; fix the ones flagged)
| # | Concept | Level | High-school "one-liner" | Puzzle mechanic (fixed) | In-level feedback | Codex anchor |
|---|---|---|---|---|---|---|
| 1 | Tunnel effect | Enrichment | "A tiny particle can sometimes cross a wall it doesn't have the energy to climb. The thinner the wall, the more often." | **Fix:** the barrier has a visible *thickness*. Thin barriers let Quarky through below the energy threshold, thick ones never do. Keep it deterministic but *teach the trend*: the player picks which of 2–3 barriers of different thickness to aim at. The oscillating element becomes a barrier that "breathes" (thickness varies over time). | Probability fringes light up on the far side when a crossing will succeed | Tunnel microscope (STM), flash memory |
| 2 | Superposition | Enrichment | "Until you look, it's in both places at once." | **Fix:** after the splitter, Quarky becomes **2 ghost copies** that both travel. A *detector* the player taps in flight "measures" and collapses to the copy nearest that detector. The partition that blocks the direct path is kept, so the interaction stays mandatory. | Both trails drawn; the one that loses fades out | Double-slit experiment, qubits |
| 3 | Entanglement | Enrichment | "Two linked particles: measure one, and you instantly know the other." | Keep the twin-crystal gate, but the tap acts on the **near** crystal and the **far** gate reacts. **Forbid** `tap_time < t_min`. Full release: 2 pairs whose states are anti-correlated. | Filament flash between the pair | Quantum cryptography, 2022 Nobel (Aspect) |
| 4 | Heisenberg uncertainty | Enrichment | "The more precisely you know *where*, the less precisely you know *how fast*, and the other way round." | Keep the precision dial, but show it as **two linked bars** (position cone ↔ speed spread) and preview the *cone* of possible trajectories instead of one line. The target oscillates. | Trajectory preview widens/narrows live | Electron microscope resolution limits |
| 5 | Energy quantisation | **Core** (Terminale: atomic energy levels, E = hν) | "Energy comes in fixed steps, like the rungs of a ladder, never in between." | **Fix:** make it distinct. The launcher has **rung levels E1…E4**, and the barrier/gates only accept an exact rung (a lock tuned to one energy, not a threshold). Photons are colour-coded by energy; you collect the one that matches your current rung. | Launcher coils light up rung by rung; a Photon changes colour when matched | Neon lights, lasers, spectral lines |
| 6 | Spin | Enrichment (magnetism core) | "Particles behave like tiny compasses pointing up or down." | Stern–Gerlach magnet: spin up is deflected up, spin down is deflected down. Pre-launch spin choice plus one flip in flight. Widen the param space (the current `[-12, -11]` angle is a hard-coded solution). | Arrow on Quarky; field lines curve accordingly | MRI, hard-drive read heads |
| 7 | Wave–particle duality | **Core** (Terminale: diffraction, the photon) | "Light and matter are both waves and particles, depending on how you look." | Particle = bounces off the grating. Wave = **diffracts through a slit narrower than Quarky** and spreads. The tap timing matters because the slit is past the first obstacle. Forbid `tap_time < t_min`. | Ripple rings; a diffraction fan preview | Electron diffraction, photovoltaic panels |

#### Full-release worlds `[FULL]` (planning only; no specs until the Quantum beta ships)
| Scale | Core concept (high school) | Mechanic | Collectible tie-in |
|---|---|---|---|
| Atomic | **Coulomb's law** F ∝ q₁q₂/r² | Ion emitters attract/repel Quarky (charged); the player sets the *sign* and the *distance* | Photons sit on equipotential lines |
| Atomic | **Electron energy levels** (a follow-up to quantisation) | Jump between orbits by absorbing a Photon of the right colour | Photon colour = ΔE |
| Atomic/Molecular | **Van der Waals / intermolecular forces** (short-range, weak) | "Sticky" surfaces that grab Quarky only when very close and slow; used to perch and relaunch | Photons behind sticky corners |
| Atomic/Molecular | **Covalent bonds / molecular geometry** (enrichment) | Snap atoms into a molecule to build a bridge | — |
| Macro | **Energy conservation** Ec + Ep = constant (+ friction losses) | Ramps and springs; an energy bar HUD shows Ec ↔ Ep swapping in real time | Photons at heights that are only reachable with exact energy |
| Macro | **Elastic potential energy / springs** (Hooke) | Spring compression dial | — |
| Macro | **Optics: reflection & refraction** (Snell–Descartes) | Mirrors (angle in = angle out) and prisms (refraction index); the laser is now a *light* beam, not Quarky | Photons literally on the light path |
| Macro | **Electromagnetism** (the Lorentz force, qualitatively) | Electromagnet with an intensity dial | — |
| Macro | **Momentum conservation** (collisions) | Billiard-style transfer to another body | — |
| Orbital | **Universal gravitation** F ∝ m₁m₂/r², **Kepler** | Place/choose planets; slingshot | Photons along an ellipse |
| Orbital | **Angular momentum conservation** | A "skater" effect: the orbit speeds up closer in; a tap extends the solar sail to change radius | Photons at perihelion |
| Orbital | **Circular orbit velocity / escape velocity** | Launch power notches: too low = crash, right = orbit, too high = escape | — |
| Cosmic | **Gravitational lensing** (general relativity, enrichment) | Aim *around* a black hole and let spacetime bend the path | Photons along the Einstein ring |
| Cosmic | **Expansion of the universe / redshift** | Photons redden as the level "expands" over time; collect them before they fade | Timer through redshift |
| Cosmic | **Dark matter** (enrichment) | An invisible mass you infer from how visible objects move | — |

- [ ] **[GATE]** User approves the fixed Quantum mechanics (tunnel thickness, 2-ghost superposition, rung-lock quantisation, slit diffraction) before the Stage 3 rewrite. *2-ghost superposition: approved and implemented.*
- [ ] Rule: **every Codex fact must be scientifically correct, even when the mechanic is a simplification.** Each Codex page has a one-line "Dans la vraie physique…" ("In real physics…") note that says where the game simplified.

### 2.3 Educational feedback loop
- [ ] **Before the level:** one-sentence "hypothesis" card: the scientist asks "Que se passe-t-il si… ?" ("What happens if…?"). The player can skip it.
- [ ] **During the level:** the invisible-physics layer *is* the teaching (force lines, cones, fringes). No text.
- [ ] **After the level:** "Le saviez-vous ?" ("Did you know?") line from the scientist (≤ 280 characters) → it unlocks a Codex page (illustration + one-liner + a formula at high-school level + a real-world anchor + "Dans la vraie physique…").
- [ ] Optional quiz (1 question, 3 answers) per world; it unlocks a cosmetic. It must never gate progression.
- [ ] i18n from day 1: FR (source) + EN. Codex strings live in `content/codex/*.yaml`, not in Python.

---

## Phase 3 — Game design refinement (Cut the Rope × Angry Birds)

### 3.1 Core loop (per level, target 30–90 s)
- [ ] **Read** (2–5 s): the level fits on one screen, with a portal, Photons and objects visible. First-time objects pulse once.
- [ ] **Tune** (optional): rotate / set dials on lab instruments. Snap to readable notches (15° / 5 intensity steps) to avoid pixel-hunting.
- [ ] **Aim & launch**: slingshot drag with a trajectory preview **limited to the first segment** (Angry Birds keeps the skill in the shot by only showing the start of the arc). The preview length is a difficulty lever: long in world 1, shorter later.
- [ ] **Act in flight**: exactly one tap action per level in the beta (Cut the Rope's "cut at the right time"). Show a subtle timing indicator ring on the interactive object.
- [ ] **Resolve**: success warp or a gentle failure. **Instant retry** (≤ 300 ms, no menu, one-tap reset). Failure has no penalty (fits the storytelling tone).
- [ ] **Reward**: stars → Codex → next level. Near-miss feedback ("so close!") when Quarky passes within 1.5× the target radius.

### 3.2 Stars & collectibles
- [ ] **3 Photons in every level, always** (fixes the audit finding). Placement rules for the generator:
  1. Photon 1 is **on the obvious path** (teaches collecting).
  2. Photon 2 requires **using the concept well** (e.g. only reachable by the wave-mode path).
  3. Photon 3 requires **mastery/timing** (a late tap, an edge of the tolerance window).
  All three must be collectable in *one* flight, and the validator must prove it.
- [ ] Photons are placed **on physically meaningful points of a solution trajectory** (apex, post-reflection segment, the far side of the barrier), sampled from the solver's trails, not placed at random.
- [ ] Optional per-world secret: one **"Quark d'or"** hidden collectible per world, off the main path, that unlocks a Codex bonus page. `[FULL]`
- [ ] Star gates between worlds (e.g. 70% of stars to unlock the next world) `[FULL]`. The beta has no gates.

### 3.3 Tactile & juice checklist
- [ ] Haptics (Android `HapticFeedbackConstants` / `VibrationEffect`): a light tick for each drag notch, a medium thump on launch, a crisp tick on Photon collect, a double pulse on success. Toggle in settings.
- [ ] Squash & stretch on Quarky (velocity-based), anticipation on drag, overshoot on release.
- [ ] Hit-stop of 40–60 ms on key events (tunnel crossing, collapse, portal).
- [ ] Camera: micro-shake on impacts only (≤ 2 px), with an accessibility toggle.
- [ ] Audio stings per event, tuned in pitch per scale (Stage 4, but reserve the hooks now).
- [ ] Touch: drag target ≥ 48 dp, drag starts from anywhere near Quarky (a 2× radius), cancel by dragging back to the origin.

### 3.4 Progression across scales
- [ ] Beta: 7 levels, linear, a Codex page per level. Onboarding in level 1 uses **no text**: a ghost hand shows the drag once.
- [ ] Full: per world, `N concepts × (1 intro + 2–3 ramp) + 3–5 mix levels + 1 showcase level` (the showcase is a setpiece at the end of the world, before the scale-change cinematic).
- [ ] Difficulty levers the generator can tune: preview length, tolerance window width, oscillation amplitude/period, obstacle count, Photon placement tier.
- [ ] Hints: after 5 fails, offer the reference solution's *first segment* (read from the shipped `hint.params`). No ads-for-hints in the beta.
- [ ] Metrics to log in the closed test: attempts per level, time to first success, star distribution, where players quit, Codex open rate.

---

## Phase 4 — Engine roadmap

### 4.1 Python level builder — hardening (Stage 3 continued) `[BETA]` →
- [ ] Package it: `pyproject.toml`, `src/quarkcosmos_levels/` layout, `ruff` + `mypy --strict` + `pytest`. Keep zero runtime dependencies (use `numpy` only if the solver needs it).
- [ ] **Level JSON schema** (`schema/level.schema.json`, JSON Schema 2020-12) with `schema_version`, validated on export and in CI. Split the output in two:
  - `level.json` (shipped in the app): geometry, objects, photons, the *public* param ranges for UI dials, `hint_first_segment`.
  - `level.meta.json` (dev only): full solution set, tolerance metrics, generator seed.
- [ ] Physics core fixes:
  - [ ] Reflect only when approaching (`dot(v, n) < 0`); push the particle out of the penetration.
  - [ ] Swept circle-vs-circle collision (continuous) or sub-stepping so that a fast Quarky never goes through thin objects.
  - [ ] Fixed timestep + a documented integration method (semi-implicit Euler) so the port can match it bit-for-bit (see §4.3).
  - [ ] Obstacles as **shapes** (circle, capsule, segment, polygon), not chains of circles (segments now exist in the engine; the old superposition "chute" circles are gone).
  - [ ] A plugin registry per concept: `concepts/<name>.py` exports `handler`, `builder`, `codex_key`, `param_space`. No hard-coded dicts in 3 places.
  - [ ] Remove the `trap` / Décohérence leftovers and fix the "8 concepts" comments.
- [ ] Validator upgrades:
  - [ ] `t_min` for taps (reject a tap before N% of the flight).
  - [ ] **Tolerance score** = the fraction of the grid that succeeds, around the best solution (the width of the success window per parameter). Target bands per difficulty (e.g. intro ≥ 8%, mastery 1–3%).
  - [ ] **Concept-usage check**: a solution only counts if the concept's mechanic fired (event log: `tunnel_crossed`, `collapsed`, `mode_switched`…). This replaces the fragile `MAX_WALL_BOUNCES = 1` heuristic.
  - [ ] **Trivial-solution check**: the level must *not* be solvable with the concept's mechanic disabled.
  - [ ] 3-star proof: at least one solution collects all 3 Photons **and** the 3-Photon window is narrower than the 1-Photon window.
  - [ ] Adaptive search (coarse grid → refine near successes) to keep generation under ~2 s per level.
- [ ] Generator: seeded procedural variations per template, auto Photon placement from the solution trails (§3.2), a difficulty knob mapped to the levers in §3.4.
- [ ] Tooling:
  - [ ] `cli.py render <level> --png` (matplotlib, dev dependency) draws the trails of the success/fail heatmap.
  - [ ] An HTML **level viewer** that loads `level.json`, replays the reference solution with the *same* physics (via the golden trajectories, §4.3) and exposes dials, which replaces the hard-coded mockup levels.
  - [ ] `cli.py build-pack --world quantique` writes `levels/quantique/pack.json` + a manifest with a hash.
- [ ] Tests: unit tests per handler, golden trajectory files (`tests/golden/*.json`: params → trail, sampled every 10 steps), a regression test that every shipped level is still solvable with tolerance ≥ threshold.

### 4.2 Android app — engine selection `[GATE]` (Stage 5 — plan only until Stage 3 is validated)
Options, ranked for *this* game (2D, vector/glow, deterministic custom physics, small APK, 60 FPS):

| Option | APK (release, arm64) | Pros | Cons | Verdict |
|---|---|---|---|---|
| **Kotlin + libGDX** | ~5–8 MB | Mature 2D, shaders for bloom, Box2D not needed (custom physics), Kotlin, JVM tests can share golden files | Older API, desktop/HTML backends need care | **Recommended** |
| Godot 4 (GDScript/C#) | ~25–35 MB (can be trimmed to ~15) | Great editor, 2D lighting/glow built in, fast iteration | Bigger APK, GDScript physics port, weaker unit-test story | Strong alternative if an editor matters |
| Jetpack Compose + Canvas / AGSL shaders | ~3–5 MB | Tiny, native UI and accessibility, AGSL for glow | Game loop and particles are DIY; AGSL needs Android 13+ | Good for the Codex/menus, risky for the game view |
| Unity | 30+ MB | Ecosystem | Overkill, APK size, licensing history | Not recommended |
| Flutter + Flame | ~10–15 MB | Fast UI | Dart physics port, custom shaders are limited | Possible, not preferred |

- [ ] **[GATE]** Decide the engine. Recommended: **libGDX (game view) + a thin native Android shell** (Play services, haptics, settings), all Kotlin.
- [ ] Spike (2 days, time-boxed): render the Quantum level with bloom + 200 particles on a low-end device (e.g. an Android Go-class phone with 2 GB RAM) and measure frame time.

### 4.3 Single source of truth for physics
- [ ] Decision: **Python = authoring + validation; Kotlin = runtime**, with the same deterministic algorithm, kept in sync by **golden trajectory tests** run in both CI jobs (Python generates `tests/golden/*.json`, a Kotlin JUnit test replays it and asserts positions within 1e-6).
- [x] Specify the physics in `docs/physics-spec.md`: timestep, integration, collision order, event semantics, tap timing. Both implementations cite it. *Done: the Python engine is the reference; the spec describes its current behaviour, [GATE] fixes will update it.*
- [ ] Alternative considered: running the Python engine on-device via Chaquopy. Rejected: APK size (+15 MB) and startup cost.

### 4.4 Android implementation plan (Stage 5) →
- [ ] Module layout (Gradle):
  - `:core-physics` (pure Kotlin, no Android dependency: simulate, handlers, level model; unit-tested with the golden files).
  - `:core-content` (level/Codex loading, schema version check).
  - `:game` (libGDX: scenes, rendering, input, FX).
  - `:app` (Android shell: activity, haptics, settings, save).
  - `:feature-codex` (Compose UI).
- [ ] Input: slingshot drag with `GestureDetector`-level smoothing, a rotation ring for dials (angle snap), single-tap in-flight action with a generous window (± 1 frame of input latency compensation), cancel-drag.
- [ ] Rendering pipeline: batch sprites and shapes → a matter-layer FBO → a downsampled bloom (2 passes) → a composite + LUT grade. Invisible-physics lines drawn after bloom (so they stay crisp).
- [ ] Performance budget: **16.6 ms/frame**, physics ≤ 1 ms, draw calls ≤ 50, overdraw ≤ 2.5×, no allocation in the game loop (object pools for particles/trail points), textures in one atlas ≤ 2048².
- [ ] Trajectory preview computed from the *same* `core-physics` (a truncated simulation), cached while the drag doesn't change.
- [ ] Save: progress + stars + Codex in `DataStore` (Proto). Cloud save `[FULL]`.
- [ ] APK size budget: **< 20 MB** (beta target < 12 MB). Measures: R8 full mode, resource shrinking, an AAB with per-ABI splits, vector/procedural FX instead of PNG sequences, OGG/Opus audio at 96 kbps, SDF fonts.
- [ ] Accessibility: a colour-blind-safe palette variant, reduced motion (disable shake/bloom pulse), text scaling in the Codex, TalkBack labels on menus.
- [ ] Analytics for the closed test: privacy-respecting event log (Firebase or a self-hosted alternative, **[GATE]**), with opt-in consent for minors (a high-school audience means GDPR-K / COPPA rules apply).
- [ ] Distribution: Play Console internal test track → closed test. Target API = the current Play requirement, `minSdk` 24.
- [ ] CI: GitHub Actions builds the debug APK, runs JVM tests + golden tests + lint on every PR, and uploads the APK as an artifact.

---

## Phase 5 — Repository architecture, skills & agents

### 5.1 Repository layout (target)
```
/CLAUDE.md                 # short: scope, stage gate, pointers only
/todo.md                   # this file
/docs/
  physics-spec.md          # the deterministic sim contract (Python ⇄ Kotlin)
  level-schema.md
  decisions/ADR-000x-*.md  # one ADR per GATE decision (engine, DA v2, physics fixes)
/design/                   # Stage 1–2: style frames, mockups, reference board
  mockups/                 # (move stage2-mockup/ here)
/levels-builder/           # (rename stage3-physics-engine/) Python package
  src/quarkcosmos_levels/{core,concepts,solver,export,cli}/
  tests/ tests/golden/
/content/
  levels/quantique/*.json  # the exported pack (the artifact the app consumes)
  codex/{fr,en}/*.yaml
/android/                  # Stage 5, only created after the gate
/.claude/{skills,agents,settings.json}
/.github/workflows/{python.yml,android.yml}
```
- [ ] Rename folders from "stageN-" to a domain name (stages are a *process*, not an architecture). Keep the stage status in `CLAUDE.md`.
- [ ] `content/` becomes the contract between the builder and the app. The app never imports the Python code.

### 5.2 CLAUDE.md
- [ ] Add a **"Current stage & status" table** (Stage 1 validated / 2 validated / 3 in progress…) so the stage-gate rule can actually be checked.
- [ ] Add **commands**: how to run the builder, the tests and the viewer. Add the **definition of done** per PR (tests green, levels revalidated, skill updated if a design decision changed).
- [ ] Add a **language convention**: design docs/skills in FR (current), code identifiers in EN, comments FR or EN but consistent per module. Today the code mixes both and drops accents (`Element oscillant` vs `Élément oscillant`).
- [ ] Move the beta-scope concept list into `gameplay-mechanics` (single source) and have CLAUDE.md link to it. It's currently duplicated, and "8 concepts" is still stale in the skill.

### 5.3 Skills (refine) ⇄
- [ ] `art-direction` → v2 after the §1 gate. Split it into `SKILL.md` (rules) + `references/palette.md`, `references/objects.md`, `references/scales.md` so it loads lighter.
- [ ] `gameplay-mechanics`: remove the stale "8 concepts". Add the 3-Photon placement tiers, the `t_min` tap rule, the tolerance bands, and the core-loop timings from §3.
- [ ] `storytelling`: add the Codex template (§2.3), the scientist's voice guide with 5 good/bad examples, and a reading-level target.
- [ ] **New** `physics-pedagogy` skill: the §2 tables, the "Dans la vraie physique…" rule, the Core/Enrichment labels, and the forbidden simplifications (e.g. "tunnel = having enough energy").
- [ ] **New** `level-builder` skill: how to add a concept plugin, run validate/solve, read tolerance reports, regenerate golden files.
- [ ] **New** `android-architecture` skill: created only at Stage 5 (it holds the §4.4 decisions once validated).
- [ ] Every skill ends with a `## Statut` + `## Changelog` (date, decision, who validated).

### 5.4 Agents (create `.claude/agents/`) ⇄
- [x] `physics-reviewer`: read-only. Checks Codex text and mechanics against `physics-pedagogy`; flags scientific errors and jargon above high-school level.
- [x] `level-designer`: writes concept builders/generators, runs `validate` and the tolerance checks, and never hand-places Photons.
- [x] `level-qa`: runs the full pack validation + golden tests, and reports brittle levels (tolerance below band) and trivial solutions.
- [x] `art-director`: loads `art-direction`; produces/reviews HTML/SVG style frames; checks contrast and colour-blind safety.
- [ ] `android-dev` (Stage 5 only): Kotlin/libGDX with the performance budget from §4.4 as hard constraints.
- [x] Each agent's front-matter lists the skills to load and the **stage it's allowed to act on**, which enforces the stage-gate rule mechanically. *Done: stated in each agent's body (Claude Code front-matter has no stage field); golden tests in `level-qa` wait for §4.1.*

### 5.5 Workflow & automation
- [x] `.claude/settings.json`: allow `python3 -m pytest`, `python3 cli.py *`, `ruff`, `./gradlew test`; add a SessionStart hook that installs dev dependencies for cloud sessions. *Done for the tools that exist today (`cli.py`, pytest, `pip install -e`); add `ruff` / `./gradlew test` when they are introduced.*
- [ ] Pre-commit: ruff, mypy, JSON-schema validation of `content/levels/**`.
- [ ] CI `python.yml`: lint + tests + `build-pack` + fail if any shipped level is unsolvable or below its tolerance band.
- [ ] PR template: stage, scope tag (`BETA`/`FULL`), which skills were updated, screenshots/GIF for visual changes.
- [ ] Label issues with `stage:1..5`, `scope:beta|full`, `area:da|physics|builder|android|narrative`.

---

## Suggested execution order (cloud sessions)

1. [ ] **S1** Repo hygiene: restructure (§5.1), fix stale docs, CLAUDE.md status table, pyproject, CI skeleton. *(no design change)*
2. [ ] **S2** ⇄ Physics-core fixes + tests + golden files (§4.1 physics core).
3. [x] **S3** ⇄ Art direction v2 style frames, 3 options (§1.1–1.2) → **[GATE] user picks**. *B + C background, Quarky v2, portrait.*
4. [ ] **S4** ⇄ Physics pedagogy skill + Quantum concept fixes proposal (§2.2) → **[GATE] user approves**.
5. [ ] **S5** → Validator upgrades (t_min, tolerance, concept-usage, 3-Photon proof) + regenerate the 7 beta levels with 3 Photons each.
6. [ ] **S6** → Level viewer (HTML, reads `content/levels`), which replaces the hard-coded mockup levels; playtest the 7 levels. → **[GATE] Stage 3 validated**.
7. [ ] **S7** Stage 4 audio (not detailed here, per the stage rule).
8. [ ] **S8** → **[GATE] engine decision** → Android spike (§4.2) → `:core-physics` Kotlin port against the golden files.
9. [ ] **S9** → Android beta: game view, input, FX, Codex, save, closed-test distribution.
10. [ ] **S10** `[FULL]` Atomic world spec (the start of the next scale cycle).
