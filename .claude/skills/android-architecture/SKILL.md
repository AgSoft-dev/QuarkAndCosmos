---
name: android-architecture
description: Validated architecture of the Quark & Cosmos Android app (Stage 5 POC) — Gradle modules (:core-physics pure Kotlin, :game libGDX, :app Compose shell), Python ⇄ Kotlin determinism through golden trajectories, English/French localisation, performance and APK budgets, conventions (minSdk 26, portrait, content copied from content/). Load before any change to the android/ folder or any Android technical spec.
---

# Android architecture — Quark & Cosmos

User decision (`todo.md` §4.2 gate, [ADR-0004](../../../docs/decisions/ADR-0004-android-engine.md)): **libGDX for the game view + a thin native Kotlin shell** (Compose menus). Code in `android/`, opened as is in Android Studio. Usage: `android/README.md`.

## Modules

| Module | Contents | Must never depend on |
|---|---|---|
| `:core-physics` | Port of the Python engine: `Level` (shipped JSON v3), `Simulation` (one step = `DT`), `Shapes`, `Handlers`, `ParamGrid` | Android, libGDX |
| `:game` | libGDX (JVM): `LevelScreen`, procedural rendering in `render/` (Canvas, Quarky v2, palette); `GameHost` / `LevelInfo` / `GameText` = the bridge to the shell | Android (goes through `GameHost`) |
| `:app` | `MainActivity` (Compose: welcome, scales, map), `GameActivity` (libGDX, implements `GameHost`, builds `GameText` from resources, loads the Codex line), `Progress` (DataStore), `Catalog` | — |

Planned later (`todo.md` §4.4): `:core-content` (level/Codex loading), `:feature-codex` (Compose).

## Determinism rule (non-negotiable)

- **Python = creation + validation; Kotlin = execution** ([ADR-0005](../../../docs/decisions/ADR-0005-golden-trajectories.md)). `docs/physics-spec.md` is the contract; if they disagree, the Python code wins.
- Every physics change goes: Python engine → `python3 -m quarkcosmos_levels golden` → Kotlin port → `GoldenTest` green (positions within 1e-6 at every step, same outcome, same Photons, same contacts).
- Follow Python's order of operations (identical IEEE rounding): `Math.hypot`, `Math.toRadians`, `2 * d * n`, `Math.rint` where Python rounds.
- The game loop runs **whole** `DT` steps (accumulated real time) and only interpolates the display.
- Player settings are **snapped to the `param_space` grid** (`ParamGrid.snap`): the validator proved solvability and stars on that grid.
- Porting a concept = its handlers in `Handlers.forType` + its levels in `GOLDEN_LEVELS` (`export/golden.py`). An unported type throws `UnsupportedObstacle`.

## Localisation (English + French)

- Every player-facing string lives in `app/src/main/res/values/strings.xml` (English, default) **and** `values-fr/strings.xml` (French), same keys. French typography: ` ` before `: ! ?`.
- Compose reads them with `stringResource` / `pluralStringResource`. The libGDX view has no resources: `GameActivity` fills a `GameText` (defaults = English, used by desktop tooling). Never hard-code a string in `:game`.
- Codex lines: `content/codex/<lang>/quantique.json`, copied into `assets/codex/`; the language folder is the `codex_lang` resource (`en` / `fr`), so it follows the app locale.
- Per-app language on Android 13+: `androidResources.generateLocaleConfig = true` + `res/resources.properties` (`unqualifiedResLocale=en-US`).
- Fonts (`render/Fonts.kt`) must include every glyph used by both languages; check both layouts when adding a string (French is usually longer).

## Conventions

- `minSdk 26` (Android 8.0), `targetSdk`/`compileSdk` = current Play requirement, portrait.
- Content is never duplicated in `android/`: the `copyContent` task copies `content/levels/quantique/*.json` and `content/codex/*/*.json` into the assets at every build.
- 100% procedural rendering (no shipped image); OFL fonts (JetBrains Mono, Fira Sans) in `app/src/main/assets/fonts/`, shared by libGDX and Compose.
- In-game text follows the `storytelling` tone; rendering follows `art-direction` (art direction v2).
- A level's result = an instrument reading in the bottom panel, never a pop-up over the play area.

## Budgets (`todo.md` §4.4)

- 16.6 ms/frame, physics ≤ 1 ms, ≤ 50 draw calls, overdraw ≤ 2.5×, **no allocation in the loop** (preallocated arrays).
- APK < 20 MB (beta < 12 MB).

## Status

POC structure validated: Tunnel 1 playable in English and French, the 6 other nodes locked, no audio or Codex screen yet. The real bloom (¼-res FBO, 2 blurs) and the low-end phone measurement remain (§4.2 spike).

## Changelog

- 2026-09-26 — S1: translated to English; EN/FR localisation (`GameText`, `values-fr/`, Codex per language); content read from `content/` (schema v3).
- 2026-09-26 — POC: modules, golden replay, Tunnel 1.
