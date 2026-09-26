# Quark & Cosmos

Android physics puzzle game (working title). The player travels through 5 scales of the universe (Quantum → Atomic/Molecular → Macro → Space → Cosmological); each law of physics becomes a touch puzzle mechanic.

## Method — stage gate

Move strictly stage by stage: 1 art direction/UI-UX, 2 HTML/JS mockup, 3 Python physics engine & level builder, 4 audio, 5 Android architecture. Never produce code or a spec for a future stage until the current stage is validated by the user. Items tagged `[GATE]` in `todo.md` need an explicit user decision.

Exception decided by the user (2026-09-26, [ADR-0006](docs/decisions/ADR-0006-android-poc-before-audio.md)): the Android POC (Stage 5) comes **before** audio (Stage 4), which is still to do.

### Current stage & status

| Stage | Status | Where |
|---|---|---|
| 1 — Art direction / UI-UX | **Validated** (art direction v2, 2026-09-25) | `design/art-direction-v2/`, skill `art-direction` |
| 2 — HTML/JS mockup | **Validated**, frozen | `design/mockups/` |
| 3 — Physics engine & level builder | **In progress**: 7 concepts × 3 difficulties generated and validated; open: implementing the approved Quantum concept fixes (§2.2, [ADR-0008](docs/decisions/ADR-0008-quantum-concept-fixes.md), S5), level viewer, beta-scope `[GATE]` (S5–S6) | `levels-builder/`, `content/levels/` |
| 4 — Audio | **Not started** | — |
| 5 — Android | **POC done** ahead of stage 4: welcome, scales, Quantum map, Tunnel 1 playable, EN/FR; awaiting the user's emulator check | `android/`, skill `android-architecture` |

Keep this table up to date in the PR that changes a stage's status.

## Beta scope (closed test)

The first playable build (closed test) is limited to the **first world only (Quantum scale)**, ~1 level per concept (7 concepts → 7 levels). No level mixes concepts; intra-concept progression and mix levels are for the full release. The 7 concepts, their order and their mechanics are defined once, in the `gameplay-mechanics` skill. The other 4 scales are out of scope: any scope decision (level generation, Android architecture) serves this scope before extending to other scales.

## Repository map

| Path | What |
|---|---|
| `design/` | Stage 1–2 design artifacts (art direction v2 board, mockups) |
| `levels-builder/` | Python package `quarkcosmos_levels`: simulation, level generator, validator, star placement, exporter, golden trajectories |
| `content/` | The shipped pack, contract between the builder and the app: `levels/quantique/*.json`, `codex/<lang>/*.json` |
| `android/` | Android app: `:core-physics` (Kotlin port), `:game` (libGDX), `:app` (Compose shell) |
| `docs/` | `physics-spec.md` (deterministic sim contract), `level-schema.md`, `decisions/` (ADRs) |
| `todo.md` | Roadmap and open `[GATE]` items |
| `.claude/` | Skills, agents, settings |

## Commands

```bash
# Level builder (Python ≥ 3.10, no runtime dependency)
cd levels-builder && pip install -e ".[dev]"
python3 -m quarkcosmos_levels generate-all     # regenerate content/levels + meta (~2-3 min)
python3 -m quarkcosmos_levels golden           # golden trajectories for the Kotlin port
python3 -m quarkcosmos_levels report           # difficulty report (reports/*.html)
ruff check . && python3 -m pytest -q           # lint + tests (~2-3 min)

# Android (JDK 17; the full app needs the Android SDK / Android Studio)
cd android && ./gradlew :core-physics:test     # Kotlin physics vs goldens (no SDK needed)
./gradlew :app:assembleDebug                   # debug APK
```

CI: `.github/workflows/python.yml` (ruff + pytest) and `android.yml` (golden replay + APK).

## Definition of done (every PR)

- Tests green: `ruff check . && pytest` for the builder; `:core-physics:test` when `android/` or goldens change.
- Engine or template changed → levels, metas and goldens regenerated and committed.
- Player-facing text added in **English and French**.
- A design decision changed → the skill (with a Changelog line), an ADR if it closes a `[GATE]`, and `todo.md` updated.
- The status table above updated if a stage moved.

## Language convention

- **The repository is in English**: code, identifiers, comments, docs, skills, agents, commit messages ([ADR-0007](docs/decisions/ADR-0007-repo-english-app-bilingual.md)).
- **The app is in English and French**: Android strings in `res/values/` (English, default) and `res/values-fr/`; Codex lines in `content/codex/en/` and `content/codex/fr/`.
- Data keys stay as they are, even when French (concept ids like `dualite`, level ids, obstacle ids).
- Frozen design artifacts in `design/` keep their French on-screen demo text.

## Skills

- `art-direction` — validated art direction (palette, Quarky, visual rules, level design). Load before any visual production or mockup.
- `storytelling` — validated narrative universe (premise, tone, the scientist, Codex, Quantum → Cosmological order). Load before any in-game text.
- `gameplay-mechanics` — beta concepts (single source), game loop, object control, in-flight action, 3-star system. Load before any level spec or scoring.
- `physics-pedagogy` — high-school target, per-concept one-liner / approved mechanic / feedback / Codex anchor / "In real physics…" note, forbidden simplifications, Codex rules, review checklist. Load before any Codex text, concept spec or physics claim.
- `android-architecture` — Android modules, Python ⇄ Kotlin determinism, EN/FR localisation, budgets. Load before any change to `android/`.

Agents in `.claude/agents/`: `art-director`, `level-designer`, `level-qa`, `physics-reviewer`, `android-dev`. Domain detail lives in its skill, not here.
