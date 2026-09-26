# ADR-0008 — Quantum concept fixes (§2.2)

- **Status:** accepted (user decision, 2026-09-26, sprint S4)
- **Gate:** `todo.md` §2.2 ("User approves the fixed Quantum mechanics")

## Context
The Stage 3 audit (`todo.md` §0) found several Quantum mechanics that teach the wrong rule or no rule of their own: the tunnel barrier lets Quarky through when its speed reaches a threshold (classical passage *over* a barrier, the opposite of tunnelling); quantisation is a notched power setting that every other level already uses; duality's wave mode is a bounce with an angle offset; uncertainty shows a single line; spin's pole attracts/repels with a narrow solution; entanglement's tap is not tied to the linked pair. `todo.md` §2.2 proposed a fixed mechanic per concept for a high-school audience; the reasoning and the Codex rules are in the `physics-pedagogy` skill.

## Decision
The user approves the §2.2 fixed mechanics for the Quantum world:

- **Tunnel:** the barrier has a **visible thickness**. A barrier thinner than a threshold is crossed although Quarky's energy is below its height; a thick one is never crossed. The player chooses among **2–3 barriers** of different thickness. The oscillating element becomes a **breathing thickness**.
- **Quantisation — rung-lock:** the launcher has energy **rungs E1…E4**; locks accept **one exact rung** (not a threshold); Photons are **colour-matched** to rungs.
- **Duality:** wave mode **diffracts through a slit narrower than Quarky**; particle mode **bounces**.
- **Uncertainty:** **two linked bars** (position cone ↔ speed spread) and a **trajectory cone preview** instead of one line.
- **Spin:** **Stern–Gerlach deflection** (spin up one way, spin down the other), pre-launch choice + one flip in flight, with a **widened parameter space**.
- **Entanglement:** the tap acts on the **near crystal** and the **far gate** reacts.

Already implemented and unchanged by this ADR: two-ghost superposition ([ADR-0002](ADR-0002-two-ghost-superposition.md)) and the `TAP_MIN_TIME` tap floor (0.1 s).

## Consequences
- Implementation is **S5** (`todo.md`): engine handlers, generator templates, validator, `docs/physics-spec.md`, regenerated levels/metas/goldens, then the Kotlin port. Until then the shipped levels keep the current mechanics described in `gameplay-mechanics`.
- **Tunnel 1**, played by the Android POC, changes layout and handler: its golden trajectories and `:core-physics` are updated in the same S5 work.
- Codex lines for the fixed concepts are rewritten against the `physics-pedagogy` drafts (English and French) with a `physics-reviewer` pass; the shipped text is not changed by this ADR.
- ~~Open: four rungs vs the three Photon ray counts~~ — decided below.

## Follow-up decisions (user, 2026-09-26)

- **Tunnel model (user decision 2026-09-26: "the most physical option that helps the gameplay"):** every barrier has a **height V above the launcher's maximum energy**, so no crossing is ever a classical climb. Real transmission falls like e^(−2κd) with κ ∝ √(V − E): it drops fast with the thickness d and rises as the energy E gets closer to V. The game turns it into a sharp rule at a fixed transmission: Quarky crosses iff **√(V − E) · d ≤ k**, i.e. its energy reaches the **tunnel threshold E_t(d) = V − (k/d)²**. So a thin barrier has a low threshold, a thicker one a higher threshold, and one thick enough to put E_t above the maximum energy is never crossed. Both levers stay: *which barrier* (thickness) and *how much energy*. The breathing barrier (thickness over time) makes E_t oscillate — the current Tunnel 1's oscillating threshold is exactly this, read in the HUD as "tunnel threshold".
- **Uncertainty model (user decision 2026-09-26: "a cone of probability"):** the precision dial sets a **cone of probability** for the direction and, in inverse proportion, a spread for the speed. The actual shot is **drawn inside that cone** (and inside the speed spread) from a distribution peaked on the centre line, truncated at the drawn edges, with a **seeded deterministic draw** per attempt so replays and golden trajectories stay reproducible. The validator proves the level on the **whole cone**: at least one dial/aim setting where every trajectory of the cone (sampled edges + centre, both speed extremes) reaches the target. The skill is to pick a precision where both spreads fit the gap; a wide cone is a gamble, not a guaranteed loss.
- **Quantisation rungs (user decision 2026-09-26): 4 rungs E1…E4 are kept.** The Photon colour-blind double gets a fourth step: **4 / 6 / 8 / 10 rays** for E1 / E2 / E3 / E4, and a fourth energy colour chosen with `art-direction` in S5 and run through the palette validator (candidate `#fef08a`: normal-vision ΔE ≥ 15 against the three existing colours; the worst colour-blind pair stays the existing violet/cyan one, already doubled by the rays). Because 8 vs 10 rays is hard to count at Photon size, E4 also carries a thin outer ring, so no rung relies on colour or a close ray count alone.
- **Codex:** every shipped statement is corrected against the `physics-pedagogy` skill now (Codex lines EN/FR, Tunnel in-game strings, handler docstrings), worded so it stays true for the current and the S5 mechanics.
