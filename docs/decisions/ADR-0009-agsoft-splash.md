# ADR-0009 — AgSoft studio splash: option A "Struck silver"

- **Status:** accepted (user decision, 2026-09-26)

## Context
The user asked for a studio logo animation at app start-up for the developer name **AgSoft**, playing on Ag (silver, element 47) as a periodic-table tile and on "soft Ag" / quicksilver. Two HTML options were produced in `design/splash-agsoft/`: A "Struck silver" (a silver tile, sheen, struck like a soft metal, reads [Ag]Soft) and B "Quicksilver drop" (a mercury drop settling into the tile).

## Decision
**Option A.** Facts shown: 47 · Ag · Silver (FR "Argent") · 107.87; tagline "argentum · soft silver" / "argentum · métal malléable". Silver is soft and malleable, so the tile is *worked* like metal, never melted.

Implementation (Android POC):
- `ui/SplashScreen.kt` (`AgSoftSplash`): one Compose `Canvas` reproducing the mockup timeline (≈ 2.45 s: trace + count to 47, sheen, strike, [Ag]Soft slide, hold, fade to `#0a0612`). No bitmap, video, blur or new dependency.
- Cold start only (first screen of `MainActivity`), a tap skips it, and with system animations off the still logo is shown briefly.
- Android 12+ system splash: background `#0a0612` with a transparent icon (`values-v31/themes.xml`), so the Compose sequence starts on a matching dark screen.

## Consequences
- Studio identity is silver, distinct from the Quantum pink; pink/cyan appear only as a hair-thin sheen fringe (decoration, no information).
- A later refinement can move the tile into the system splash as an animated vector (`core-splashscreen`) for a seamless hand-over, as the mockup caption suggests.
