# ADR-0003 — Shipped level / dev meta split

- **Status:** accepted (2026-09-25); extended by ADR-0007 (schema v3)

## Context
The exported level carried validator data (full reference solution, `must_contact`, tolerances) into the game payload.

## Decision
Two files per level: the shipped level (geometry, Photons, `param_space`, `hint.params`) and a dev-only meta (`must_contact`, solvability, tolerances, bypasses, reference solution, star profile). `schema_version` in both, bumped on every incompatible change.

## Consequences
The game never sees dev data; `read_level` joins `must_contact` back for validation. Field reference: `docs/level-schema.md`.
