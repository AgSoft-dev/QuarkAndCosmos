---
name: art-direction
description: Validated art direction for Quark & Cosmos (Stage 1, art direction v2 "a lab seen through an instrument": flat matter + cinematic background, Quarky v2) — palette per scale, Quarky's character design and its 5 evolutions, the two-visual-layer rule (objects vs physics fields), and level design conventions. Load before producing any mockup, asset, level screen, or any visual/UX decision on this project.
---

# Art direction — Quark & Cosmos

**Art direction v2 (validated): "a retro-futuristic physics lab seen through an instrument".** Each scale is what an instrument would show at that magnification (Quantum = detector cavity / bubble chamber). The HUD is the instrument's eyepiece. Dark worlds, never a pastel/childish setting; physics as a thin vector overlay.

Living reference: [`design/art-direction-v2/index.html`](../../../design/art-direction-v2/index.html) (frames A/B/C, Quarky v2 sheet, objects, colour contract). The combination chosen below is **B + C background**; the Android level screen (`android/game`) is its first full implementation. Decision record: [ADR-0001](../../../docs/decisions/ADR-0001-art-direction-v2.md).

## Chosen rendering — "B + C background"

User decision (Phase 1 gate §1.1): **mostly B** (the most readable), with **C's background**.

- **Matter and objects = B style, "flat lab" (Monument Valley)**: flat fills, 3–4 colours per scene, volume given by a **shadow crescent**, **facets** and a highlight dot (no heavy radial gradient), ~1.5 px outline. **Light** bloom (≈ 0.18, physics ≈ 0.08). Portal as rotating flat concentric discs; sharp-edged fringes; Quarky's trail as a simple line; negative space embraced.
- **Background = C style, "volumetric cinema"**: **3 parallax layers** tied to Quarky's position (distant bokeh → fringes/fog → foreground dust), soft light rays from the portal, **grain and vignette ≤ 3%**. The background stays **below** the matter: background luminance ≤ 20% of the matter's, no high-frequency detail behind the play area.
- **Mobile budget**: vector shapes + **a single bloom pass** (¼ resolution, 2 blurs), one colour grade per scale, no real-time light per object.
- **The environment reacts to the outcome**: success = the fringes lock into a sharp pattern and a scan line "resolves" the cavity; failure = the background decoheres into noise and Quarky dissolves. The result is shown as an instrument reading (HUD title), never as a pop-up over the play area.
- **Orientation: portrait** (confirmed when art direction v2 was validated; Quantum stays a narrow vertical box).

## Core rule: two non-negotiable visual layers

1. **"Matter" layer** — Quarky and every manipulable object (mirror, splitter, barrier, magnet, spring, target, obstacles). Flat B rendering: flat fills + shadow crescent/facets + highlight dot, ~1.5 px coloured outline. The most contrasted layer on screen.
2. **"Invisible physics" layer** — predicted trajectories, field lines, fringes, gravitational halos/domes. Always thin (~0.75–1 px), dotted or with arrows, monochrome per force type, overlaid on the matter layer, pulsing in the direction of flow, and **less bloomed** than the matter.

This separation is also a teaching signal: the player instantly tells "what can be touched" from "what physics shows".

**Per-force rule**: one force = one dedicated colour + a single line style (solid/dotted/arrow), repeated identically everywhere in the game.

## Quarky — the character

Visual DNA constant across every evolution: soft jelly/plush body, big expressive eyes (dark pupils, white highlight), gummy specular highlight, ~1.5 px coloured outline, a slight cool *rim light* that detaches Quarky from the dark background.

**Quarky v2 (validated, Phase 1 gate §1.2)**: a **luminous** particle creature — a **glowing core** inside a **jelly membrane**, keeping the big eyes (emotional anchor). Rendered in B style (flat fills + shadow crescent), the core is the only "luminous" element of the matter.
- Silhouette = a round drop + two eyes: readable at **48 px** (still at 32 px).
- 8 **procedural** states (speed-driven squash & stretch, no sprites): idle, aiming tension, launch, flight, collect, near miss, success (drawn into the portal), failure (dissolves).
- **Quantum mutation = 2–3 flickering ghost phase copies**, without solid pupils (the "real" Quarky stays identifiable). They are also the **superposition copies** in the game (see `gameplay-mechanics`): the copy lost at the measurement fades out with its trail.
- **Duality**: particle = sharp body; wave = the body dissolves into concentric ripples following the trajectory.

The **Macro form is the canonical form** — the other 4 scales are *mutations* of this same base, not different characters.

## The 5 scales

Continuous colour progression from small to large: pink → yellow/orange → green → violet → deep indigo.

| Scale | Colour | Quarky mutation | Level topology | Gravity | Signature obstacle | Setting |
|---|---|---|---|---|---|---|
| Quantum (10⁻¹⁵ m) | Pink `#f472b6` | Flickering ghost phase copies (superposition) | Closed, vertical, narrow box (portrait) | None | Barrier/tunnel | Near-black detector cavity, 3-layer parallax (C background), no grid |
| Atomic/Molecular (10⁻⁹ m) | Yellow `#facc15` | Orbiting electron ring + blue satellite (charge) | Radial/orbital around a nucleus | Central attraction | +/- ions | Near-black, no grid |
| Macro (1 m) | Green `#4ade80` | Canonical form | Horizontal corridor | Fixed vertical (down) | Spring/mirror/electromagnet | Black background, very discreet technical grid, neon-edged platforms |
| Space (10⁹ m) | Violet `#a78bfa` | Mini solar-sail fins + star trail | Open plane, no floor | Multiple wells | Giant planet (gravitational slingshot) | Classic starry black |
| Cosmological (10²² m) | Indigo `#818cf8` | Slightly deformed (skewed) silhouette | The grid itself is curved | Warps space | Opaque black hole (gravitational lensing) | The only scale where the setting reacts visually to gameplay (climax/final boss) |

### Colour contract — Quantum

| Role | Colour |
|---|---|
| Scale key | `#f472b6` |
| Complementary (cool) accent | `#67e8f9` |
| Deep background | `#0a0612` |
| Threshold / danger | `#fb923c` |
| Derived (medium energy, entanglement filament) | `#c4b5fd` |
| HUD text / secondary text | `#f7eef9` / `#b9a7c9` (≥ 4.5:1 on the background) |

Colour blindness (deuteranopia/protanopia): no information by colour alone. Mandatory doubles: line style per force, ↑/↓ spin and +/− glyphs, **the Photon's number of rays (4/6/8) for its energy** (medium/high Photons are close in deuteranopia). The other scales will get their contract (key + accent + background + threshold) in the same format.

## Target and Photon — rendering

- **Target = portal**, not a plain static golden disc. Concept: a teleportation halo — animated concentric rings (slow rotation + pulse), a glowing core that draws the eye, in the current scale's colour (no universal gold). It reinforces the narrative idea that Quarky changes state/place on reaching it, consistent with the "journey across scales" of the `storytelling` skill. Animated as soon as the renderer allows it.
- **Photon = glint**, not just a dot pulsing in size. Concept: small sparks/highlights appearing and disappearing randomly around the Photon's body (like glitter), on top of the halo — the goal is to read "reward to collect" at first glance, before even understanding the level's mechanic. It stays smaller/more discreet than the target and Quarky (see `gameplay-mechanics`); the glint must never compete in readability with the intended path.
- Both stay in the "matter" layer (flat B rendering: flat fills + shadow crescent) — the glint/portal animation are added on top. Photon: colour = energy (E = hν), doubled by the number of rays.

## Level design — progression rules

- **Constant session length** across the 5 scales — not a differentiating axis.
- **Difficulty = the only progression axis**, on two simultaneous levels:
  1. Global curve across scales (Quantum/Macro as intro → Cosmological as climax).
  2. Intra-scale progression: at least 3 levels per scale, from a single obstacle/rule to a combination of constraints. Style and visual vocabulary never change from one level to the next within a scale — only the quantity/combination of elements grows.
- Composition/camera per scale: fixed and tight (Quantum/Atomic) → lateral tracking (Macro) → free zoom (Space) → zoom + distortion (Cosmological).

## HUD & UI

**Instrument eyepiece**: thin-line frame around the play area, readings in a **monospace** font (JetBrains Mono) and interface in a **humanist** font (Fira Sans), both under the OFL licence (their character sets must cover English and French). Unchanged positions: star counter top left, round reset button top right, floating object selector at the bottom. Dark semi-transparent pill background (`#0f1524` @ 90%, or the scale's eyepiece colour). Text lengths differ between English and French: layouts must fit the longer of the two (check both when adding a string).

## Status

Stage 1 (graphic identity & art direction) validated, **art direction v2 included**. Don't reopen the choices above without an explicit user decision — reuse them as is for any Stage 2+ mockup (HTML/JS), asset, or technical spec.

## Changelog

- 2026-09-26 — Translated to English; reference page moved to `design/art-direction-v2/` (S1).
- 2026-09-25 — **v1 → v2**:
  - **Rendering**: illustrated gradient matter (Cut the Rope style) → **flat B matter** (flat fills, shadow crescent, facets) + **C cinematic background** (3-layer parallax, grain/vignette ≤ 3%), a single bloom pass.
  - **Quarky**: same DNA (jelly, big eyes, gummy highlight) → **Quarky v2**: glowing core + membrane, 8 procedural states, phase copies = superposition copies.
  - **Frame**: abstract setting → **instrument** (detector cavity for Quantum), HUD = eyepiece, OFL mono + humanist fonts.
  - **New**: colour contract per scale (key + accent + background + threshold), background luminance rule (≤ 20% of the matter), environment reacting to the outcome.
  - **Unchanged**: key palette per scale, two-layer rule, per-force rule, portal and glinting Photon, portrait.
