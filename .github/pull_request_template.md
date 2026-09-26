## Summary
<!-- What changes and why, in a few lines. -->

## Stage & scope
- Stage: <!-- 1 art direction / 2 mockup / 3 level builder / 4 audio / 5 Android / repo -->
- Scope: <!-- BETA / FULL -->
- `[GATE]` decision involved: <!-- none, or the todo.md item + the user's decision -->

## Checklist
- [ ] `cd levels-builder && ruff check . && python3 -m pytest -q` green (if the builder or `content/` changed)
- [ ] Levels / metas / goldens regenerated and committed (if the engine or a template changed)
- [ ] `cd android && ./gradlew :core-physics:test` green (if `android/` or the goldens changed)
- [ ] New player-facing text added in **English and French**
- [ ] Skill / ADR / `todo.md` updated if a design decision changed
- [ ] Screenshots (EN + FR) for visual changes
