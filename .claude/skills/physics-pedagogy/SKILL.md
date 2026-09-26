---
name: physics-pedagogy
description: Physics pedagogy of Quark & Cosmos — high-school (lycée, 15–18) target, "one concept = one intuitive rule the player can predict before launching", Core/Enrichment curriculum labels, and for each of the 7 Quantum concepts the high-school one-liner, the approved fixed mechanic (ADR-0008), the in-level feedback (invisible-physics layer), the Codex real-world anchor and the "In real physics…" simplification note. Also the forbidden simplifications, the Codex writing rules (scientist's voice, ≤ 280 characters, English and French), the before/during/after educational loop and the physics-review checklist. Load before writing or reviewing any Codex text, concept spec, mechanic change, engine handler docstring or hypothesis card, and whenever a physics claim reaches the player.
---

# Physics pedagogy — Quark & Cosmos

The game teaches physics by making the player **use** it, never memorise it. This skill is the reference for what each concept means for a high-school player, how the mechanic embodies it, and what the Codex may and may not claim. The mechanics themselves (loop, tap, difficulty, stars) live in `gameplay-mechanics`; the scientist's voice lives in `storytelling`; the visual layers live in `art-direction`.

## Target and principles

- **Audience: lycée / high school, 15–18.** Vocabulary of a Seconde–Terminale physics class (energy, speed, wave, magnet, light). Any other term is explained in the same sentence or avoided.
- **One concept = one intuitive rule the player can predict before launching.** If the player can't say "if I do X, then Y" before the shot, the mechanic is too opaque. The rule is shown by the level (the invisible-physics layer), not by text.
- **The puzzle is solved by using the physics.** A winning shot must go through the mechanic (`must_contact`, 0 bypass: see `gameplay-mechanics`).
- **Every Codex fact is scientifically correct, even when the mechanic simplifies.** The game may be deterministic where nature is probabilistic, may exaggerate scales, may make a choice the player controls; the Codex never states the simplification as a fact. Each concept has an **"In real physics…"** note saying exactly where the game simplifies.
- **Every Codex entry ends on a real-world anchor**: a device, an experiment, a date.

### Forbidden simplifications

These are errors, not simplifications. The `physics-reviewer` agent rejects them in any text (Codex, strings, docstrings, specs):

| Concept | Forbidden | Why |
|---|---|---|
| Tunnel | "with enough energy you get through the wall" | That is classical passage *over* a barrier. Tunnelling is crossing **without** enough energy. |
| Superposition | "a deflector / a switch that picks one path" | Both paths exist until the measurement. |
| Superposition | "the measurement result is chosen" (stated as physics) | A real outcome is random; only the game lets timing decide. |
| Entanglement | "acting here pushes / sends a signal over there" | Correlations are instant but carry no message and can't be steered. |
| Entanglement | "nobody knows why it's that fast" (as if a signal travels) | Nothing travels; the correlation is built in. |
| Uncertainty | "the instrument is clumsy / measuring disturbs it" as the whole story | The limit is a property of the particle, not of a bad instrument. |
| Uncertainty | "aiming precisely makes you slower" | The trade-off is precision of position vs **spread** of speed (momentum), not the speed value. |
| Quantisation | "a notched setting" alone | Any dial can have notches; quantisation means **only exact energies exist** (an atom's levels). |
| Spin | "the particle really spins like a top / is a tiny magnet with any orientation" | Measured along an axis, spin gives only two answers. "Like a tiny compass" is allowed as an image, flagged in the note. |
| Duality | "sometimes it is a wave, sometimes a particle, it chooses" | A quantum object propagates like a wave and is detected like a particle; the experiment reveals one aspect. |

## Curriculum labels — Core / Enrichment (proposal)

> **Proposal only.** The curriculum mapping is a separate open `[GATE]` (`todo.md` §2.1: labels + external physics-teacher review). Nothing below is shown to players until that gate is closed. Planned player-facing labels: "On the syllabus" / "Au programme" and "Going further" / "Pour aller plus loin".

- **Core** = in the French *programme de Seconde / 1ère / Terminale* (spécialité physique-chimie) or an equivalent international high-school curriculum.
- **Enrichment** = beyond the curriculum, but explainable in one sentence with high-school words.

| # | Concept id | Proposed label | Curriculum hook (to check in §2.1) |
|---|---|---|---|
| 1 | `tunnel` | Enrichment | energy, potential barrier (idea only) |
| 2 | `superposition` | Enrichment | — |
| 3 | `intrication` | Enrichment | — |
| 4 | `incertitude` | Enrichment | diffraction as the wave-side intuition (Terminale) |
| 5 | `quantification` | **Core** | atomic energy levels, photon energy E = hν, spectra (1ère spécialité) |
| 6 | `spin` | Enrichment (magnetism is Core) | magnetic field, compass |
| 7 | `dualite` | **Core** | diffraction, the photon, wave–particle duality (Terminale spécialité) |

## The 7 Quantum concepts

Order and ids from `gameplay-mechanics` (single source). Concept ids stay French data keys. Status of each mechanic: **approved** by the user on 2026-09-26 ([ADR-0008](../../../docs/decisions/ADR-0008-quantum-concept-fixes.md)); superposition and `TAP_MIN_TIME` are already implemented, the other fixes are implemented in S5 (`todo.md`). Until then the shipped levels use the "current" mechanics described in `gameplay-mechanics`.

Codex drafts below are **drafts for review**, not shipped text: the shipped lines stay in `content/codex/{en,fr}/quantique.json` until an S5/Codex PR replaces them (with a `physics-reviewer` pass and, per §2.1, a teacher review). Each draft is ≤ 280 characters in both languages. Hypothesis cards are for the before-level step of the loop (not implemented).

### 1 — `tunnel` — Tunnel effect

- **One-liner:** a tiny particle can sometimes cross a wall it doesn't have the energy to climb; the thinner the wall, the more often.
- **Rule the player predicts:** thin wall → I get through; thick wall → I bounce, whatever my power.
- **Approved mechanic:** the barrier has a **visible thickness**. A barrier thinner than a threshold is crossed although Quarky's energy is below its height; a thick one is never crossed. The player chooses which of 2–3 barriers of different thickness to aim at. The oscillating element becomes a **breathing barrier** (its thickness varies over time), so the arrival instant matters.
- **Implementation guidance (S5):** every barrier is taller than the launcher's maximum energy, so *every* crossing is a tunnel crossing (never a classical climb). Optional, closer to reality: the threshold thickness grows slightly with speed (a particle closer to the top tunnels more easily), which keeps the power dial meaningful.
- **In-level feedback:** probability fringes light up on the far side of a barrier when the crossing will succeed; the barrier's thickness is drawn as matter (flat fill), the fringes as invisible physics.
- **Codex anchor:** scanning tunnelling microscope (STM, Nobel 1986), flash memory.
- **In real physics…** crossing is a matter of probability, which falls very fast (exponentially) as the barrier gets thicker; the game turns it into a sharp rule: thin = always, thick = never.
- **Hypothesis card:** EN "What happens if the wall is thinner?" · FR « Et si le mur était plus fin ? »
- **Codex draft:**
  - EN: "You didn't have the energy to climb that wall, yet here you are on the other side. Tiny particles do this, now and then, and more often when the wall is thin. My tunnelling microscope relies on it to see single atoms."
  - FR: « Tu n'avais pas l'énergie de franchir ce mur, et pourtant te voilà de l'autre côté. Les toutes petites particules le font parfois, et d'autant plus souvent que le mur est fin. Mon microscope à effet tunnel s'en sert pour voir les atomes un par un. »

### 2 — `superposition` — Superposition of states

- **One-liner:** until you look, it's on both paths at once.
- **Rule the player predicts:** after the splitter there are two of me; whichever copy is nearest the detector when I tap becomes the real one.
- **Mechanic (implemented, [ADR-0002](../../../docs/decisions/ADR-0002-two-ghost-superposition.md)):** a flat splitter makes two ghost copies (transmitted / reflected) flying at the same time; the tap measures and Quarky becomes the copy nearest the detector; the target only accepts a measured Quarky; a copy crashing before the measurement breaks the superposition (the launch fails).
- **In-level feedback:** both trails drawn; the losing copy fades out with its trail.
- **Codex anchor:** double-slit experiment, qubits in quantum computers.
- **In real physics…** the result of a measurement is random: only the odds are known in advance. The game lets the detector and the tap instant decide, so the puzzle stays playable.
- **Hypothesis card:** EN "What happens if you look before the copies split?" · FR « Et si tu regardais avant que les copies se séparent ? »
- **Codex draft:**
  - EN: "Until I looked, you were travelling both paths at once. Measuring made one of them real. Quantum computers play the same game: their qubits hold 0 and 1 together until they are read."
  - FR: « Tant que je ne regardais pas, tu suivais les deux chemins à la fois. La mesure a rendu l'un des deux réel. Les ordinateurs quantiques jouent au même jeu : leurs qubits valent 0 et 1 en même temps, jusqu'à la lecture. »

### 3 — `intrication` — Quantum entanglement

- **One-liner:** two linked particles: measure one, and you instantly know the other, however far apart.
- **Rule the player predicts:** when I tap the crystal near me, the gate far away changes at the same instant (and, in an anti-correlated pair, into the opposite state).
- **Approved mechanic:** the twin-crystal gate is kept, but the tap acts on the **near crystal** and the **far gate** reacts. `tap_time < TAP_MIN_TIME` stays forbidden (implemented). Difficulty 2 keeps the anti-correlated pair. Full release: two pairs with anti-correlated states.
- **In-level feedback:** a filament flash (`#c4b5fd`) between the near crystal and the far gate at the tap instant.
- **Codex anchor:** quantum cryptography; the 2022 Nobel Prize (Aspect, Clauser, Zeilinger).
- **In real physics…** you can't choose what the measurement gives, so you can't use entanglement to send a message or to open a door far away; only the results are linked. The game lets the tap set the far gate so it becomes a playable action.
- **Hypothesis card:** EN "What happens to the far gate if you touch the near crystal?" · FR « Que devient la porte lointaine si tu touches le cristal proche ? »
- **Codex draft:**
  - EN: "The crystal here and the gate over there behaved as one. Measure one of two entangled particles and you know the other at once, however far away, yet no message travels between them. Testing this earned Aspect, Clauser and Zeilinger the 2022 Nobel Prize."
  - FR: « Le cristal ici et la porte là-bas se sont comportés comme un seul objet. Mesure l'une de deux particules intriquées et tu connais l'autre aussitôt, même très loin, sans qu'aucun message ne voyage. Aspect, Clauser et Zeilinger ont eu le Nobel 2022 pour l'avoir testé. »

### 4 — `incertitude` — Heisenberg uncertainty principle

- **One-liner:** the more precisely you know *where* it is, the less precisely you know *how fast* it goes, and the other way round.
- **Rule the player predicts:** a narrow aim makes my speed fuzzy; a sure speed makes my aim fuzzy.
- **Approved mechanic:** the precision dial is shown as **two linked bars** (position cone ↔ speed spread); the preview draws the **cone** of possible trajectories instead of a single line. The target oscillates.
- **In-level feedback:** the trajectory cone widens/narrows live as the dial moves; the two bars move in opposite directions.
- **Codex anchor:** why an electron can't sit still inside an atom (squeezed into so small a space, its speed can't be zero); limits of measurement at the atomic scale.
- **In real physics…** the trade-off is between position and momentum (mass × velocity), Δx·Δp ≥ h/4π, and it only matters for tiny particles. The game maps it onto the aim and the launch speed, on a scale where it would really be unnoticeable.
- **Hypothesis card:** EN "What happens to the speed if you aim very precisely?" · FR « Que devient la vitesse si tu vises très précisément ? »
- **Codex draft:**
  - EN: "The more tightly you pinned down where you'd go, the fuzzier your speed became. For an electron that's a law of nature, not a clumsy instrument. It's even why an electron can't sit perfectly still inside an atom."
  - FR: « Plus tu fixais précisément où aller, plus ta vitesse devenait floue. Pour un électron, c'est une loi de la nature, pas un instrument maladroit. C'est même pour ça qu'un électron ne peut pas rester parfaitement immobile dans un atome. »

### 5 — `quantification` — Energy quantisation

- **One-liner:** energy comes in fixed steps, like the rungs of a ladder, never in between.
- **Rule the player predicts:** this lock opens only for E2; E1 or E3 bounce off.
- **Approved mechanic (rung-lock):** the launcher has **energy rungs E1…E4** (no continuous power). Locks (barriers/gates) accept **one exact rung**, not a threshold: too little and too much both bounce. Photons are **colour-matched** to rungs: a Photon is collected only by a Quarky on its rung (colour = energy, doubled by the number of rays, see `art-direction`).
- **In-level feedback:** the launcher coils light up rung by rung; a Photon changes colour when it matches the current rung; each lock shows the rung it accepts.
- **Codex anchor:** neon signs, lasers, spectral lines (each element's barcode of colours).
- **In real physics…** it is the energy of a particle *bound* in an atom that is quantised; a free particle can move at any speed. The launcher's rungs stand for an atom's energy levels, and a jump between two levels gives out a photon of energy E = hν, hence one exact colour.
- **Hypothesis card:** EN "What happens if you launch between two rungs?" (answer: you can't) · FR « Et si tu lançais entre deux barreaux ? »
- **Codex draft:**
  - EN: "Only a few energies were allowed: E1, E2, E3, E4, nothing in between. Atoms work the same way, and each jump between two levels gives out light of one exact colour. That's why a neon sign glows red-orange instead of every colour at once."
  - FR: « Seules quelques énergies étaient permises : E1, E2, E3, E4, rien entre les deux. Les atomes fonctionnent pareil, et chaque saut entre deux niveaux émet une lumière d'une couleur précise. Voilà pourquoi une enseigne au néon brille rouge-orangé, et pas de toutes les couleurs. »

### 6 — `spin` — Quantum spin

- **One-liner:** particles behave a bit like tiny compasses that, once measured, only ever point up or down.
- **Rule the player predicts:** spin up → the magnet sends me up; spin down → it sends me down; a tap flips my spin once.
- **Approved mechanic (Stern–Gerlach):** a Stern–Gerlach magnet deflects spin up one way and spin down the other. Pre-launch spin choice + one flip in flight. The parameter space is **widened** (no hard-coded angle), so the aim and the flip instant are real choices.
- **In-level feedback:** an ↑/↓ arrow on Quarky (colour-blind double); field lines of the magnet drawn in the invisible-physics layer, splitting into two branches.
- **Codex anchor:** the Stern–Gerlach experiment (silver atoms, 1922); MRI scanners; hard-drive read heads.
- **In real physics…** spin is not a real rotation, and the deflection comes from a magnetic field that is stronger on one side than the other. The flip Quarky makes with a tap is done in an MRI scanner with a radio pulse.
- **Hypothesis card:** EN "Up or down: where will the magnet send you?" · FR « En haut ou en bas : où l'aimant va-t-il t'envoyer ? »
- **Codex draft:**
  - EN: "The magnet sent you up or down, never in between: your spin only has two answers. Stern and Gerlach saw the same split with silver atoms in 1922. Today MRI scanners flip the spins of the protons in your body to see inside it."
  - FR: « L'aimant t'a envoyée en haut ou en bas, jamais entre les deux : ton spin n'a que deux réponses. Stern et Gerlach ont vu la même séparation avec des atomes d'argent en 1922. Aujourd'hui, l'IRM bascule le spin des protons du corps pour voir à l'intérieur. »

### 7 — `dualite` — Wave–particle duality

- **One-liner:** light and matter behave both as waves and as particles, depending on the experiment.
- **Rule the player predicts:** as a particle I bounce off the grating; as a wave I pass through a slit narrower than me and spread out.
- **Approved mechanic:** particle mode = bounce off the grating; wave mode = **diffracts through a slit narrower than Quarky** and spreads (a fan). The tap (particle → wave) matters because the slit lies past the first obstacle; `tap_time < TAP_MIN_TIME` stays forbidden (implemented).
- **In-level feedback:** ripple rings around Quarky in wave mode; a diffraction-fan preview behind the slit.
- **Codex anchor:** electron diffraction (Davisson–Germer, 1927); electron microscopes; photovoltaic panels (light absorbed as photons).
- **In real physics…** a quantum object doesn't switch mode on command: it always travels like a wave and is always detected as a particle, in one spot. Diffraction is strong when the slit is about as wide as the wavelength; Quarky's size stands in for that wavelength.
- **Hypothesis card:** EN "Can you fit through a slit narrower than yourself?" · FR « Peux-tu passer par une fente plus étroite que toi ? »
- **Codex draft:**
  - EN: "As a particle you bounced off; as a wave you slipped through a slit narrower than you and spread out. Electrons do it too: in 1927 Davisson and Germer saw them diffract off a nickel crystal, just like light."
  - FR: « En particule tu as rebondi ; en onde tu es passée par une fente plus étroite que toi, et tu t'es étalée. Les électrons le font aussi : en 1927, Davisson et Germer les ont vus diffracter sur un cristal de nickel, comme la lumière. »

## Codex writing rules

- **Voice:** the scientist of `storytelling` — amused, benevolent, never orders or scolds. Structure: a remark on what Quarky just did → the physics in one sentence → a real-world anchor.
- **Length:** ≤ 280 characters per pop-up line, **in each language**; the full Codex page ≤ 120 words (`todo.md` §1.5).
- **Two languages, written natively:** English and French are each written as natural text, not a literal translation of the other, but they carry **the same physics and the same anchor**. French keeps Quarky feminine and the scientist's inclusive forms; English copy uses no pronoun for Quarky.
- **Accuracy:** every factual claim (names, dates, devices) is checkable; no forbidden simplification; the simplification lives in the "In real physics…" note, never in the fact.
- **Words:** high-school vocabulary. Allowed without explanation: energy, speed, wave, particle, atom, electron, magnet, light, colour. Anything else (qubit, momentum, diffraction) is explained or backed by the in-level visual.
- **Data keys stay French** (`dualite`, `intrication`…); only the text is localised. Shipped lines live in `content/codex/{en,fr}/quantique.json` (`check-codex` fails if a language is missing).

## Educational loop (guidance, not implemented)

The target shape of one level, from `todo.md` §2.3. As of 2026-09-26 only the after-level line exists (one Codex line per concept); the rest is guidance for S9 (Android beta) and the Codex work.

1. **Before the level** — a one-sentence, skippable **hypothesis card** from the scientist: "What happens if…?" / « Et si… ? ». It asks; it never explains the answer.
2. **During the level** — **no text.** The invisible-physics layer (`art-direction`: thin lines, one colour and one line style per force) *is* the teaching: fringes, cones, field lines, fans.
3. **After the level** — the scientist's "Did you know?" / « Le saviez-vous ? » line (≤ 280 characters), which unlocks a Codex page: illustration + one-liner + a high-school formula where one exists + real-world anchor + "In real physics…" / « Dans la vraie physique… ». The "In real physics…" page unlocks with 3 stars (`gameplay-mechanics`).
4. Optional per-world quiz (1 question, 3 answers) unlocking a cosmetic; it never gates progression.

## Review checklist (`physics-reviewer`)

Apply to every Codex line, player-facing string, handler docstring and concept spec:

1. **Correct:** every claim is true in real physics; no item of the forbidden-simplifications table.
2. **Simplification declared:** the concept has an "In real physics…" note that names what the mechanic changes (probability → rule, choice → random, etc.).
3. **Predictable rule:** the mechanic can be stated as "if I do X, then Y" before the launch, and the level shows it (in-level feedback present in the invisible-physics layer).
4. **Mechanic ↔ text:** the handler in `levels-builder/src/quarkcosmos_levels/concepts/handlers.py` does what the text promises (e.g. no tunnel text on a barrier that tests `speed ≥ threshold`).
5. **High-school level:** no unexplained jargon; one idea per line.
6. **Anchor:** a real device, experiment or date, and it is right (names, years).
7. **Bilingual parity:** English and French both present, both ≤ 280 characters, same physics, same anchor, natively written; no English pronoun for Quarky.
8. **Voice:** the scientist's tone (`storytelling`): marvels, explains, never scolds or dramatises.
9. **Scope:** Quantum beta only; flag anything that depends on an open `[GATE]` (§2.1 labels, beta scope) instead of settling it.

## Status

Created 2026-09-26 (S4). The **fixed Quantum mechanics are approved** by the user ([ADR-0008](../../../docs/decisions/ADR-0008-quantum-concept-fixes.md)); implementation is S5. The Core/Enrichment labels are a proposal pending the §2.1 `[GATE]`. The Codex drafts above are unreviewed drafts; the shipped Codex text is unchanged.

## Changelog

- 2026-09-26 — Created (S4): target and principles, forbidden simplifications, Core/Enrichment proposal, per-concept tables with the approved §2.2 fixes (ADR-0008), EN/FR Codex drafts and hypothesis cards, Codex writing rules, §2.3 loop as guidance, review checklist.
