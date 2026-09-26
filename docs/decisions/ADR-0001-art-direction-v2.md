# ADR-0001 — Art direction v2

- **Status:** accepted (user decision, 2026-09-25)
- **Gate:** `todo.md` Phase 1 / S3

## Context
The Stage 1 art direction read as "cute" rather than "a lab seen through an instrument". Three style frames (A cinematic, B flat, C background-led) were produced in `design/art-direction-v2/index.html`.

## Decision
- Mostly **B**: flat, readable matter (Quarky, objects, Photons, portal) with a **C** cinematic background (parallax, bokeh, fringes) kept at ≤ 20% of the matter's luminance.
- **Quarky v2**: jelly membrane with a shadow crescent, glowing core, big eyes; procedural states (squash, ghosts, fizzle).
- **Portrait** orientation, box as an instrument bezel; results read as an instrument reading, never as a pop-up over the play area.

## Consequences
The `art-direction` skill holds the rules; the Android game view (`android/game`) and the Compose menus port the recipes procedurally (no bitmaps). The DA asks for a narrow vertical box while the engine box is a unit square: open `[GATE]` in `todo.md` §4.5.
