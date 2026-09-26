# ADR-0002 — Superposition as two ghost copies

- **Status:** accepted (user decision, 2026-09-25)
- **Gate:** `todo.md` §0 / §2.2

## Context
Superposition was modelled as a deterministic splitter chosen by impact point: it read as "a deflector", not "two paths at once", and barely got harder with difficulty.

## Decision
A flat beam splitter creates a transmitted and a reflected ghost copy that fly at the same time. A tap **measures**: Quarky becomes the copy closest to a detector, the other vanishes with its Photons. The target only accepts a measured Quarky, so the interaction is never optional. A copy crashing before the measurement is a decoherence failure.

## Consequences
Multi-body simulation step (`physics-spec.md` §7 bis); winning shots drop to 17% → 10% → 6% across difficulties with 0 bypasses. The Kotlin port still has to implement the multi-body step (`todo.md` §4.5).
