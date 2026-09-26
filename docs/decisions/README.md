# Architecture & design decisions (ADRs)

One file per decision that closed a `[GATE]` in `todo.md` or changed a contract. Format: context → decision → consequences. An ADR is never rewritten after the fact: a later decision supersedes it with a new file.

| ADR | Date | Decision |
|---|---|---|
| [0001](ADR-0001-art-direction-v2.md) | 2026-09-25 | Art direction v2: flat "B" matter + cinematic "C" background, Quarky v2, portrait |
| [0002](ADR-0002-two-ghost-superposition.md) | 2026-09-25 | Superposition = two ghost copies, a tap measures |
| [0003](ADR-0003-level-json-meta-split.md) | 2026-09-25 | Shipped level JSON / dev meta split (schema v2) |
| [0004](ADR-0004-android-engine.md) | 2026-09-26 | Android: libGDX game view + Kotlin/Compose shell, minSdk 26 |
| [0005](ADR-0005-golden-trajectories.md) | 2026-09-26 | Python is the physics reference; Kotlin replays golden trajectories within 1e-6 |
| [0006](ADR-0006-android-poc-before-audio.md) | 2026-09-26 | Android POC (Stage 5) before audio (Stage 4) |
| [0007](ADR-0007-repo-english-app-bilingual.md) | 2026-09-26 | Repository in English; app in English + French; §5.1 layout |
| [0008](ADR-0008-quantum-concept-fixes.md) | 2026-09-26 | Quantum concept fixes (§2.2): tunnel thickness, rung-lock quantisation, slit diffraction, uncertainty cone, Stern–Gerlach spin, near-crystal entanglement |

Earlier game-design decisions (tap floor `TAP_MIN_TIME`, 3-star model, 7 beta concepts) are recorded in the skills (`gameplay-mechanics`) and `todo.md` §0.
