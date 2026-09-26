---
name: storytelling
description: Validated narrative universe for Quark & Cosmos — premise (a particle leaving a lab out of curiosity), Quarky's personality, the scientist's role, light/adventure tone, and integration with the educational Codex; player-facing text is written in English and French. Load before writing any in-game text, win pop-up, dialogue, or Codex content.
---

# Storytelling — Quark & Cosmos

## Premise

Quarky is an experimental particle born **at the quantum scale**, at the heart of a lab apparatus, during a successful experiment (not an accident, not a dangerous leak) — consistent with the game's name ("Quark" → "Cosmos"). Curious by nature, Quarky grows and freely explores towards ever **larger** scales, until literally leaving the apparatus (reaching the Macro scale = the first time Quarky sees the lab and the scientist), then carries on towards the infinitely large. Each change of scale is a deliberate step of the exploration, not an escape.

**Tone**: light, curious, benevolent adventure — never an existential threat, dramatic peril or punishing stakes. Closer to "first trip away from home" than "escape".

**Pronouns**: the French text treats Quarky as feminine ("elle", "Née au cœur d'une expérience…"). The English pronoun is not decided yet: English copy uses "Quarky" and avoids pronouns where it can.

## The scientist

A character who stays at the lab, never hostile nor worried in a dramatic sense — rather an amused, benevolent mentor who follows Quarky's adventure from afar (measuring instruments, echoes, messages) without ever holding Quarky back. This is the in-world source of the educational pop-ups: the scientist "comments" on what Quarky has just discovered, like a parent or teacher watching a student set off exploring.

- Name/gender to be decided later (not blocking). French copy uses inclusive forms ("le/la scientifique"); English copy says "the scientist".
- Never gives orders or scolds — only marvels, explains, encourages.

## Codex integration

The end-of-level "Did you know?" pop-up becomes **a line from the scientist**, not a detached box. Structure: an amused/surprised remark on what Quarky just did → a link to the real world (e.g. "You used a gravitational slingshot, like the Voyager 2 probe in 1979!"). The Scientific Codex (unlockable encyclopedia) is presented as **the scientist's logbook**, filled in as Quarky makes discoveries.

Codex lines live in `content/codex/<lang>/<scale>.json` (one file per language, keyed by concept id). Every line is written in **English and French**; neither is a literal translation of the other if a more natural phrasing exists, but both carry the same meaning and the same physics.

## Narrative arc by scale — increasing order (Quantum → Cosmological)

Current decision (replaces the ambiguous Option A "hourglass" / Option B "reversed linear"): **a single progression, by increasing scale**, consistent with the game's name. Growing curiosity rather than escape: at each scale, Quarky is not trying to get away from something, but to answer a question raised at the previous scale.

1. **Quantum (start)**: Quarky is "born" at the heart of the experiment — first contact with the player, a universe still abstract/closed (see `art-direction`). Popularisation needs special care here: it is the very first scale the player sees, hence the most disorienting — the mechanics (superposition, tunnel effect) must read without any jargon.
2. **Atomic/Molecular**: Quarky explores the matter the apparatus itself is made of.
3. **Macro**: Quarky literally leaves the apparatus — first appearance of the lab and the scientist, an emotional turning point (surprise, wonder) rather than a dramatic reveal.
4. **Space**: curiosity for what lies beyond the lab, then beyond the Earth.
5. **Cosmological (end)**: no "boss" in a threatening sense — culminating wonder (e.g. contemplating/crossing a black hole as the peak of curiosity, not a trial to overcome).

Each next scale is motivated by a naive, positive question from Quarky ("what is all this made of?", "what if I go even further?"), never by a constraint or a danger to flee.

**Note**: this replaces the Option A/B reference for the narrative. If a non-linear progression (free "hourglass" unlocking) comes back on the level design side, the thread above stays the reference order for writing texts/Codex.

## To decide later (not blocking)

- Names of the scientist and of Quarky (if a final name replaces the code name), and Quarky's English pronoun.
- Are there other particles/characters met along the way, or is Quarky the only protagonist?
- Codex text tone: popularisation register to define precisely (length, language level) once the pop-up mockups are tested.

## Status

Direction validated: exploration out of curiosity, benevolent lab origin at the quantum scale, light/adventure tone, progression by increasing scale (Quantum → Cosmological). Don't reintroduce a threatening/dramatic register, or a Macro/Cosmos starting point, without an explicit user decision.

## Changelog

- 2026-09-26 — Translated to English; player-facing text is bilingual (English + French), Codex lines moved to `content/codex/<lang>/` (S1, [ADR-0007](../../../docs/decisions/ADR-0007-repo-english-app-bilingual.md)).
