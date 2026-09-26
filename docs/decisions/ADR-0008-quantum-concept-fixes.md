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
- Open for S5: whether the uncertainty shot is the cone's centre line or a seeded draw inside it; four rungs vs the three Photon ray counts (4/6/8) of the colour-blind double in `art-direction`.
