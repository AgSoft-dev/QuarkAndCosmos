# ADR-0005 — Golden trajectories between Python and Kotlin

- **Status:** accepted (2026-09-26)
- **Gate:** `todo.md` §4.3

## Context
Level solvability and stars are proven by the Python builder. The Android runtime must reproduce the same physics, or a validated level may become unsolvable in the game.

## Decision
Python stays the reference; Kotlin is the runtime port. For every ported level, `python3 -m quarkcosmos_levels golden` records a few launches (reference solution, partial win, lost, timeout) with the position at every step. The Kotlin `GoldenTest` replays them and requires positions within 1e-6 and the same outcome, Photons and contacts. The Kotlin code follows Python's order of operations (`Math.hypot`, `Math.toRadians`, `Math.rint`).

## Consequences
A Python test fails when goldens are stale; porting a concept means porting its handlers **and** adding its levels to `GOLDEN_LEVELS`. Covered today: Tunnel 1–3.
