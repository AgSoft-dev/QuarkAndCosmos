# ADR-0007 — Repository in English, app in English + French, §5.1 layout

- **Status:** accepted (user decision, 2026-09-26, sprint S1)

## Context
The repository mixed French and English (skills, docs and comments mostly French, `todo.md` English), and folders were named after process stages (`stage1-…`, `stage3-physics-engine`). The app's text was French only.

## Decision
- **Repository language: English** — code, comments, docs, skills, agents, commit messages.
- **Player-facing text: English + French.** Android strings in `res/values/` (English, default) and `res/values-fr/`; the libGDX view receives its strings through `GameText`; Codex lines in `content/codex/<lang>/`. Per-app language on Android 13+ via a generated locale config.
- **Layout by domain** (`todo.md` §5.1): `design/` (art direction + mockups), `levels-builder/` (Python package `quarkcosmos_levels`, `src/` layout), `content/` (the shipped pack: levels + codex), `docs/`, `android/`. Stage status lives in `CLAUDE.md`, not in folder names.
- Level schema v3: `codex_text` leaves the level file.

## Consequences
Every new player-facing string needs both an English and a French entry (tests enforce it for the Codex). Frozen design prototypes (`design/`) keep their French on-screen demo text as historical artifacts. Data keys (concept ids such as `dualite`, obstacle ids such as `cloison`) stay as they are.
