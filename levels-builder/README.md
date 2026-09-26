# Level builder (`quarkcosmos_levels`)

Generates, validates and exports the Quantum world levels: 7 concepts (listed in the `gameplay-mechanics` skill) × 3 difficulties. Python ≥ 3.10, no runtime dependency.

Each difficulty is a **different layout** that pushes the mechanic further (1 discover, 2 sequence, 3 chain; table per concept in the `gameplay-mechanics` skill), not the same layout with other Photons.

```bash
cd levels-builder
pip install -e ".[dev]"
python3 -m quarkcosmos_levels list                  # available concepts
python3 -m quarkcosmos_levels generate-all          # rewrites content/levels/quantique/*.json + meta/*.meta.json (~2-3 min)
python3 -m quarkcosmos_levels validate ../content/levels/quantique/<level>.json   # solvability report (reads the meta too)
python3 -m quarkcosmos_levels solve ../content/levels/quantique/<level>.json      # best solution
python3 -m quarkcosmos_levels check-codex           # every concept has a Codex line in EN and FR
ruff check . && python3 -m pytest -q                # lint + tests (~2-3 min)
```

`qc-levels <command>` is the same CLI as an installed script.

## Layout

```
src/quarkcosmos_levels/
  core/       vec.py, shapes.py, simulate.py      — the deterministic simulation (docs/physics-spec.md)
  concepts/   handlers.py, generator.py           — collision rule per concept, level templates
  solver/     validator.py, stars.py              — grid search, tolerances, Photon placement
  export/     levels.py, codex.py, golden.py, report.py (+ report_template.html)
  cli.py, paths.py
meta/         dev-only metadata of each shipped level
reports/      difficulty report (CSV / JSON / HTML)
tests/        pytest suite; tests/golden/ = golden trajectories for the Kotlin port
```

Outputs outside this folder: `../content/levels/quantique/` (the shipped pack) and `../content/codex/<lang>/` (player-facing Codex lines, EN + FR, written by hand).

## Export format

Each level is exported as **two files**: the shipped level (`content/levels/quantique/<name>.json`, read by the game) and its dev meta (`levels-builder/meta/<name>.meta.json`). The field reference and the version history are in [`docs/level-schema.md`](../docs/level-schema.md). `validate`/`solve` read a level through `read_level`, which joins `must_contact` back from the meta; without a meta the level can still be simulated but bypasses are no longer checked (warning on stderr). The simulation contract the game must reproduce is [`docs/physics-spec.md`](../docs/physics-spec.md).

## What an exported level guarantees

- **Solvable**: at least one combination of the `param_space` grid reaches the target.
- **No bypass**: each level declares `must_contact`, the ordered (obstacle, event) sequence that defines using the mechanic (e.g. `[["s1", "bounce"], ["s2", "wave"]]`). Any winning launch that doesn't follow it counts in `bypass_solutions`, which must be 0.
- **3 Photons** placed automatically (never by hand, see below). All 3 can be collected in a single flight.
- **Tolerance** ≥ 5%: the share of the grid that succeeds (`tolerance`, `three_star_tolerance` in the meta). Below that, the level is unplayable by finger.
- **Real in-flight tap**: a tap before `TAP_MIN_TIME` (0.1 s) is not searched. Tapping at launch would be a pre-launch setting.
- **`schema_version`** first in both files, bumped on every incompatible format change.

The tests also check that the committed JSON (levels **and** metas) is identical to the generator output, that no dev field is shipped, that no level carries player text, that every concept has a Codex line in every language, and that there is no orphan file. After any change to the engine or a template, rerun `generate-all` (and `golden`).

## Star distribution and difficulty report

Photons are placed by `solver/stars.py`: a dense fan of launches ("ray tracing") measures every valid launch, and the share earning at least *k* stars should follow a truncated gaussian `exp(−k²/2σ²)`. σ shrinks with difficulty (`SIGMA_BY_DIFFICULTY`), so the 3-star window gets narrower. When valid paths overlap, a Photon may oscillate so that only the right timing collects it.

```bash
python3 -m quarkcosmos_levels report                   # difficulties 1 2 3, every concept
python3 -m quarkcosmos_levels report --concepts tunnel spin --difficulties 1 2 3 4
```

Writes to `reports/`:
- `difficulty_report.csv` / `.json`: measured vs target per level × difficulty (≥1/≥2/3★ shares, tolerance, distinct paths, oscillating Photons, 3★ gap);
- `difficulty_report.html`: progression curves per concept, a mini-map of each level (valid paths coloured by star count, difficulty selector, hover = launch parameters) and the full table. Plotly is loaded from a CDN.

**⚠ 3★ ceiling**: the 3-star share stays > 5 pts above target. The level's valid paths are too similar for Photons to tell them apart: the level's geometry needs enriching (more possible paths), not the placement.

Tuning: `SIGMA_BY_DIFFICULTY`, `PHOTON_MOTIONS`, `MOTION_PENALTY`, `TIER_WEIGHTS` in `solver/stars.py`; `CEILING_GAP` in `export/report.py`.

## Simulation

Fixed step `DT = 0.01`, 300 steps max, closed box without gravity. "Suffered" bounces (box walls + `wall` obstacles) are capped by `max_wall_bounces` (1 by default, 0 for most difficulty 2-3 levels: touching a wall = particle lost). An obstacle handler (`concepts/handlers.py`) fires **once per contact** and its event (`bounce`, `deflect`, `pass`, `wave`, …) is logged in `SimResult.contacts`.

Shapes (`core/shapes.py`): disc (`x, y, r`) or flat segment (`x, y, length, angle_deg`) for mirrors, gates, windows and walls. Obstacle types: `wall`, `mirror` (intended bounce, not counted), `barrier`, `splitter`, `detector`, `gate` (closed before the tap), `gate_anti` (open before the tap), `pole`, `surface`. Obstacle ids are data keys and stay as generated.

Oscillations (obstacles, target, Photons) are phase-locked to the launch instant: the apparatus "starts" when Quarky leaves. The game must reproduce this convention, otherwise the solvability validated here no longer holds.

## Golden trajectories (contract with the Android runtime)

The Android runtime (`android/core-physics`, Kotlin) ports this engine exactly. So they never drift apart, `export/golden.py` records a few launches per ported level (reference solution, partial win, one bounce too many, timeout) with the position at every step:

```bash
python3 -m quarkcosmos_levels golden        # writes tests/golden/<level>.golden.json
```

`tests/test_golden.py` fails if these files no longer match the engine (regenerate them after any physics or Tunnel level change), and the Kotlin `GoldenTest` replays them within 1e-6. Covered levels: `GOLDEN_LEVELS` (Tunnel 1-3 for the POC), to extend together with the Kotlin handlers. See [ADR-0005](../docs/decisions/ADR-0005-golden-trajectories.md).
