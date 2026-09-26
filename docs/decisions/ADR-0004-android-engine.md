# ADR-0004 — Android engine: libGDX + Kotlin/Compose shell

- **Status:** accepted (user decision, 2026-09-26)
- **Gate:** `todo.md` §4.2

## Context
The game needs a 60 fps 2D view with additive light, procedural drawing and haptics, plus ordinary menus, on phones from Android 8 up.

## Decision
- **libGDX** for the level view (`android/game`, pure JVM, also runs on desktop for scripted captures).
- A thin **Kotlin/Compose** shell for the menus (welcome, scales, world map), saving (DataStore) and localisation (`android/app`).
- Physics in a separate pure-Kotlin module (`android/core-physics`), see ADR-0005.
- minSdk 26 (Android 8.0), targetSdk/compileSdk 36, portrait, JVM 17.

## Consequences
Two UI toolkits, bridged by `GameHost` / `LevelInfo` / `GameText`. The low-end phone spike and a real bloom pass stay open (`todo.md` §4.5). Details: `android-architecture` skill.
