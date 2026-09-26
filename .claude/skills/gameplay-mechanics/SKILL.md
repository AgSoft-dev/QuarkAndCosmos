---
name: gameplay-mechanics
description: Validated game mechanics for Quark & Cosmos — the 7 beta concepts and their order (single source), launch/bounce physics loop, orientation and power control of objects (lab experiment), in-flight actions, difficulty by layout, and 3-star scoring by collecting Photons along the trajectory (Cut the Rope model). Load before any level spec, object-setting UI, or scoring logic.
---

# Gameplay Mechanics — Quark & Cosmos

## Beta scope — the 7 Quantum concepts (single source)

The closed-test build covers the **first world only (Quantum scale)**, ~1 level per concept (7 concepts → 7 levels, within the 5–10 range). No level mixes several concepts in the beta (see "Progression structure").

Introduction order (numbers = play order, not the order of physical discovery). The world opens on the most immediate concept to read (a threshold you clear or not) so the player gets used to launching in a closed box without gravity before being asked to understand a choice of path.

| # | Concept id | Concept | Mechanic |
|---|---|---|---|
| 1 | `tunnel` | Tunnel effect | a barrier crossed under a timing/gauge condition |
| 2 | `superposition` | Superposition of states | a splitter turns Quarky into two ghost copies flying at the same time; the tap "measures" and Quarky becomes the copy closest to the detector — the target only accepts a measured Quarky, so the interaction is never optional |
| 3 | `intrication` | Quantum entanglement | a linked pair at a distance: acting on one changes the other instantly |
| 4 | `incertitude` | Heisenberg uncertainty principle | aiming precision vs speed control |
| 5 | `quantification` | Energy quantisation | a notched launcher, no continuous setting |
| 6 | `spin` | Quantum spin | a binary toggle that changes the interaction with some fields |
| 7 | `dualite` | Wave–particle duality | wave/particle toggle; the wave-mode bounce foreshadows — without duplicating — the classical reflection fully taught at the Macro scale with mirrors |

Concept ids are data keys (level files, Codex, save) and stay in French. Player-facing names are localised (`android/app/src/main/res/values*/strings.xml`).

Decoherence was removed from the beta scope (design feedback: redundant with superposition/the detector, not enough teaching value of its own). It remains an option for the full release if a more distinct angle is found. The other 4 scales are outside this build's scope.

## Core loop (established in Stage 2)

Slingshot drag-and-release: the player pulls Quarky back then lets go; physics (gravity where the scale has it, plus any fields) does the rest until the target or a failure. See the mockup [`design/mockups/index.html`](../../../design/mockups/index.html).

**Touch mapping (Android, user decision 2026-09-26): linear slingshot.** The drag starts anywhere in the play area and its two axes are independent: the horizontal pull away from the shot sets the energy (by length), the vertical slide turns the aim at a fixed rate (≈ 6 px per degree, down aims up) from its current value. Release launches; a release without a pull only keeps the new angle. Replaces the angle-from-drag-direction mapping, too twitchy on short pulls and pinned at the edges of narrow angle ranges.

## Object control — the "lab experiment" paradigm

Consistent with the premise of the `storytelling` skill (Quarky born from a lab experiment): before launching, the player can set some objects of the scene like lab instruments, not just place them.

- **Orientation**: rotating the object (mirror, magnet, electromagnet...) to change the reflection/deflection angle.
- **Power/intensity**: a slider or dial setting a field's strength (electromagnet intensity, spring angle, etc.) rather than a simple on/off.
- These settings are part of solving the puzzle just like the launch — a level can have a single valid combination (precision) or several solutions (tolerance range), depending on the intended difficulty.

**Blocking dependency**: this mechanic can only be implemented/tested seriously once the Stage 3 physics engine exists, because the engine must generate and validate levels (check that at least one orientation/power combination solves the level). Don't build a real setting UI before that — the Stage 2 mockup can keep fixed, non-adjustable objects meanwhile.

## Base rule — in-flight action (every concept, from the beta)

Finding (design feedback): a launch where everything is set before the shot (angle, power, dials) is solved like an ideal-trajectory problem — close to Angry Birds, but without the "real-time" tension of Cut the Rope (timing the cut, moving obstacles, order of actions). Decision: **every Quantum-world concept includes at least one variable that depends on time during the flight**, not just pre-launch settings. Two generic building blocks, reusable by every concept:

1. **Oscillating element** — the position of an obstacle (or the target) varies over time (e.g. a sinusoidal back and forth). The player must then aim correctly AND make the flight time match the right moment of the oscillation, not just aim at a fixed point.
2. **Action triggered in flight ("tap")** — a single player gesture during the flight (not a continuous control) that flips a state at the chosen instant: open a linked gate, switch wave/particle, flip a polarity. It is the equivalent of cutting the rope at the right time in Cut the Rope — one gesture, whose *timing* is the whole difficulty. The Stage 3 solver treats the tap instant as one more parameter (searched on a grid), so solvability stays guaranteed and checkable like the angle/power. A tap before `TAP_MIN_TIME` (0.1 s) is ignored by the game and stays available (a tap at launch would be a disguised pre-launch setting).

Pre-launch settings (lab-style dials, see the previous section) stay valid and stack with these mechanics — the goal is to add variables, not replace existing ones. Every beta concept has an oscillating element, an in-flight trigger, or both: see the level templates in `levels-builder/src/quarkcosmos_levels/concepts/generator.py`.

## Progression structure per world

Three phases, in this order, for organising the levels within one world (scale):

1. **Sequential introduction** — each physics concept of the world (the table above for the Quantum beta) is introduced one at a time, in its own intro level, never two new concepts at once.
2. **Intra-concept difficulty progression** — several levels raising the difficulty on one concept before moving to the next (see the rule already set in `art-direction`: same visual vocabulary, add constraints rather than changing style).
3. **Cross-concept mix** — levels combining 2+ concepts already learned in the same world, for richer/more complex puzzles.

### Difficulty = layout, never just Photon placement (Stage 3 decision)

Design feedback: moving Photons on an identical layout doesn't make a level richer, only more demanding in precision. **Every difficulty step changes the layout to explore the mechanic further**, with the same visual vocabulary:

1. **Discover** — a single instance of the mechanic, immediately visible effect.
2. **Sequence** — the mechanic used **twice, both ways** during the same flight. This is where the tap becomes real timing (a window *between* two contacts), like cutting the rope in Cut the Rope.
3. **Chain** — three instances, or two plus a moving element: aim, power and timing interact.

Quantum world (`levels-builder/src/quarkcosmos_levels/concepts/generator.py`, one function per concept and difficulty):

| Concept | 1 — discover | 2 — sequence | 3 — chain |
|---|---|---|---|
| Tunnel effect | one barrier (a window in a wall), oscillating threshold | two barriers in series: a speed that hits a trough at both ("resonance") | barrier → mirror → barrier |
| Superposition | one splitter: two ghost copies (transmitted / reflected), tap = measure, Quarky becomes the copy closest to the detector; measure before the other copy crashes | two-mirror loop, the copies cross: keep one **or** the other (two routes); the detector sweeps, so the tap instant chooses | two splitters, **two measurements** in the same flight, each in its window |
| Entanglement | a gate opened by the tap | **anti-correlated** pair: cross A (open before the tap), tap, cross B | gate M acts as a **mirror** while closed, then the same tap opens B |
| Uncertainty | precision vs speed, moving target | a narrow slit (precision → slowness) in front of a drifting target | two aligned slits, faster target |
| Quantisation | energy notches, one barrier | two barriers: only 2 notches pass | three barriers + mirror: only one notch passes |
| Spin | one pole | two + poles: attracted at A, flip the spin **between** A and B | poles +, −, +: read each pole's sign to know where to flip |
| Duality | a surface crossed as a wave | **particle** bounce on s1, then **wave** crossing of s2 | two particle bounces then a wave crossing, moving target |

**Two-ghost superposition (user decision, replaces the splitter-deflector; [ADR-0002](../../../docs/decisions/ADR-0002-two-ghost-superposition.md))**: Photons collected by a copy only count if it survives the measurement; the target only accepts a measured Quarky; a copy crashing before the measurement breaks the superposition (decoherence, the launch fails). The "In real physics…" Codex page states that the outcome of a real measurement is random.

Each level declares `must_contact` (the expected sequence of interactions). The validator rejects any level where a winning launch bypasses the mechanic (`bypass_solutions` must be 0).

Flat surfaces (mirrors, gates, windows) rather than discs for any intended bounce: "angle of incidence = angle of reflection" is predictable for the player (and it is high-school optics), whereas a bounce on a disc amplifies the smallest aiming error.

**Beta vs full release scope**: phase 3 (cross-concept mix) and the full phase 2 difficulty progression are reserved for the **full release**. The **beta/closed test** is a lighter version: fewer levels per concept (possibly one per concept), little or no intra-concept difficulty ramp, and **no mix level**. How many of the 21 generated levels ship in the closed test is an open `[GATE]` in `todo.md` §0.

## Scoring — 3 stars by collection (Cut the Rope model)

Current decision (replaces the earlier "efficiency/attempts" version): 3 collectibles are placed along a plausible path between the launcher and the target. Each collectible touched during Quarky's flight, in the **same attempt** that reaches the target, earns 1 star. Missing the target or having to relaunch cancels the collectibles picked up during that attempt — everything must be done in a single successful flight.

- **Collectible name: "Photon"** — not "Quark", to avoid confusion with the game's name and the mascot's (Quarky). Can be revisited, but use this name by default in every text/asset (in French too).
- Visual: a small sparkling particle, consistent with the "matter" layer of `art-direction` (art direction v2: colour = energy, doubled by the number of rays) — smaller and more discreet than Quarky or the target, so it doesn't clutter the readability of the intended path.
- A level stays "completed" (target reached) even with 0 Photons — Photons only set the number of stars, never the completion itself.
- **1-2-3 star distribution (Stage 3 decision)**: "ray tracing" (a dense fan of launches over angle/power/tap instant) measures every valid launch of a level. Among them, the share earning at least *k* stars follows a **truncated gaussian** `exp(−k²/2σ²)`, k = 1..3: many valid launches earn 1 star, few earn 3. **σ shrinks with difficulty** (2.2 / 1.6 / 1.2 for difficulties 1 / 2 / 3), so the number of paths/timings earning 3 stars narrows. The generator places the Photons to match this target; a Photon may oscillate (the "oscillating element" block) when valid paths overlap and only timing can tell them apart. Review report: `python3 -m quarkcosmos_levels report` (JSON + CSV + HTML with mini-maps), see `levels-builder/README.md`.
- **The 3rd star rewards a smarter route, not just a more precise one.** Several layouts produce alternative routes that use the mechanic more (e.g. ping-pong between two entangled gates, a particle bouncing between two barriers before tunnelling, a second chance as a wave after a missed bounce). Placement tries the best path of each route as the reference: a rare, rich route is the natural candidate for the 3rd Photon. Cut the Rope principle: you win easily, then see a Photon hinting that a finer path exists.
- **Why come back for 3 stars** (game side, Stage 5): instant restart; ghost of the previous best attempt; after a first win, the missing Photon "pulses" to signal another path exists; the concept's "In real physics…" Codex page only unlocks with 3 stars (the reward is understanding more, consistent with the `storytelling` tone).
- **Stars unlock what comes next (full release)**: the star total unlocks the next levels and worlds. Thresholds to calibrate on closed-test data, with the base rule: never require 3 stars everywhere (a world's threshold ≈ 2 stars on average over the previous world), so curiosity, not frustration, brings players back to a level. The beta has no lock.
- **Stage 3 dependency**: the placement of the 3 Photons per level must be proven solvable by the level generator/validator (at least one trajectory able to collect all 3 then reach the target) — it decides their final position, never a hand placement.

## Status

Direction validated for the mechanics above (launch loop, lab-style object settings, Photon scoring, in-flight action, difficulty by layout, two-ghost superposition). Implemented in the level builder for the 7 concepts × 3 difficulties; the Android POC plays Tunnel 1.

## Changelog

- 2026-09-26 — Touch mapping: linear slingshot (energy = horizontal pull, aim = vertical slide).
- 2026-09-26 — Translated to English; the beta concept list moved here from `CLAUDE.md` (single source); paths updated to the `levels-builder/` layout (S1).
- 2026-09-25 — Two-ghost superposition; difficulty by layout (21 levels); ray-traced star distribution; `TAP_MIN_TIME`.
