# ADR-0006 — Android POC before audio

- **Status:** accepted (user decision, 2026-09-26)

## Context
The stage order in `CLAUDE.md` is 1 art direction, 2 mockup, 3 physics engine, 4 audio, 5 Android. The user wanted a first app in hand before the audio stage.

## Decision
Build the Android POC (Stage 5 scope: welcome, scales, Quantum map, Tunnel 1 playable, stars saved) ahead of Stage 4 audio. The stages are not renumbered; audio stays to do.

## Consequences
`CLAUDE.md`'s status table shows Stage 5 as "POC done" while Stage 4 is "not started". Audio hooks (events already emitted by the simulation) will be wired when Stage 4 runs.
