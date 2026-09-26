# Design

Stage 1–2 design work (see the status table in `CLAUDE.md`). Plain HTML files, open them in a browser; no build step.

| Folder | What | Status |
|---|---|---|
| `art-direction-v2/` | Art direction v2 proof of concept: three style frames, Quarky v2 sheet, object catalogue, colour contract ([README](art-direction-v2/README.md)) | reference board (decision: [ADR-0001](../docs/decisions/ADR-0001-art-direction-v2.md)) |
| `mockups/` | Stage 2 interactive mockups: world map, a Macro level, a Quantum level (`index.html`), Quantum object studies (`quantique-elements.html`) | frozen; its hand-written physics is **not** the reference (`docs/physics-spec.md` is) |

These pages are frozen design artifacts: their comments are in English, but their on-screen demo text stays in French as it was reviewed. The game's player-facing text lives in `android/app/src/main/res/values*/strings.xml` and `content/codex/<lang>/` (English + French).

The rules these pages illustrate are in the `art-direction` skill (`.claude/skills/art-direction/SKILL.md`).
