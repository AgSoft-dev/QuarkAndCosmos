# Quark & Cosmos — Android POC

First playable build: **welcome → scales → Quantum world map → Tunnel effect level 1**. Portrait, Android 8.0+ (`minSdk 26`), art direction v2 ("B + C background", Quarky v2). The app is in **English and French**: it follows the device language (and the per-app language setting on Android 13+).

## Open and run in Android Studio

1. **File ▸ Open…** and pick this `android/` folder (not the repository root).
2. Let the Gradle sync run. If Android Studio asks, install the proposed **Android 16 (API 36)** platform.
   - JDK: Android Studio's bundled JDK is fine (Settings ▸ Build Tools ▸ Gradle ▸ Gradle JDK = JDK 17 or newer).
   - If the assistant offers to upgrade to AGP 9, **decline for now**: AGP 9 integrates Kotlin differently and the scripts would need changes.
3. Create an emulator if needed (Device Manager): a portrait phone, **API 26 or newer** image (x86_64).
4. **app** configuration ▸ Run.
5. To see French: set the emulator's system language to Français, or (Android 13+) Settings ▸ Apps ▸ Quark & Cosmos ▸ Language.

Content is not copied into this folder: the `copyContent` task takes the levels from `../content/levels/quantique/` and the Codex lines from `../content/codex/<lang>/` at every build. Keep the repository structure as is.

Command line: `./gradlew :app:installDebug` (phone or emulator connected), `./gradlew :core-physics:test`.

## Modules

| Module | Role | Dependencies |
|---|---|---|
| `:core-physics` | **Pure** Kotlin port of the Python engine (`levels-builder/src/quarkcosmos_levels/core`): JSON level v3, fixed step, handlers. Tested against the golden trajectories. | kotlinx-serialization-json |
| `:game` | **libGDX** game view (JVM): `LevelScreen` (slingshot aim, whole-`DT` loop, rendering, result reading), procedural rendering (`render/`). Strings come from the shell through `GameText`. | `:core-physics`, libGDX, FreeType |
| `:app` | Android shell: `MainActivity` (Compose menus), `GameActivity` (libGDX), `Progress` (DataStore), haptics, EN/FR resources. | `:game`, Compose, DataStore |

The physics knows neither libGDX nor Android; the game view knows neither activities nor saving (`GameHost` interface).

## Strings

- `app/src/main/res/values/strings.xml` — English (default).
- `app/src/main/res/values-fr/strings.xml` — French. Same keys; use ` ` before `: ! ?`.
- The level screen's strings go through `GameText` (`game/.../GameHost.kt`), built in `GameActivity`.
- Codex lines: `content/codex/en/quantique.json` and `content/codex/fr/quantique.json`, keyed by concept.

## What the POC covers

- **Welcome**: Quarky v2 idling in the instrument's eyepiece, "Play".
- **Scales**: the 5 scales in journey order; only Quantum is open (stars / 21 and levels done / 7), the others show "Soon".
- **Quantum map**: 7 nodes (order of the `gameplay-mechanics` skill), Quarky on the current node, stars per level; only Tunnel effect is playable, the 6 others are locked.
- **Tunnel effect 1**:
  - linear slingshot from anywhere in the box: pull left to set the energy, slide up/down to aim (6 units per degree, from the current angle), release to shoot; angle and energy snap to the `param_space` grid validated by the Python engine;
  - the bottom panel shows Quarky's energy against the barrier's oscillating threshold (PASSES / BLOCKED);
  - 3 Photons = 3 stars, in a single flight; the result reads as an instrument reading, with the lab logbook line;
  - ghost of the previous shot, "first segment" hint after 5 failures;
  - haptics: aim notch, shot, Photon, success/failure.
- **Save**: best stars per level, kept between launches.

## Known limits (on purpose for a POC)

- A single playable level; the handlers of the 6 other concepts are not ported yet (an unported obstacle throws `UnsupportedObstacle`).
- No real bloom (additive halos instead); frame budget still to measure on a low-end phone (`todo.md` §4.2, spike).
- No audio (Stage 4), no Codex screen, no settings.
- The play box is square (the physics lives in a unit box): the art direction's "narrow vertical box" will need a non-square box in the engine.
- Oscillations start at release (spec §3): before the shot, the apparatus is idle.
