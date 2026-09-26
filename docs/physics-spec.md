# Simulation spec — Quantum world

The deterministic contract that **every** implementation of the game's physics (Android runtime, HTML viewer, future mockups) must reproduce, so that the solvability validated by the builder stays true in the game. Reference: `levels-builder/src/quarkcosmos_levels/core/` (`simulate.py`, `shapes.py`, `vec.py`) and `concepts/handlers.py`. If this document and the Python code disagree, **the code wins** and this document must be fixed in the same PR.

The Stage 2 mockup (`design/mockups/index.html`) has its own hand-written JS physics: it is **not** an implementation of this spec (see "Known drifts").

This document describes the engine's **current** behaviour, simplifications included. The planned fixes (tunnel effect, notched quantisation, bounce only when approaching, continuous collision) are [GATE] decisions in `todo.md`: they will change this spec once validated.

## 1. Frame and units

- Normalised closed box `[0, 1] × [0, 1]`, **no gravity**. `y` grows downwards (screen convention: `wTop` has a smaller `y` than `wBot`).
- Time in simulated seconds. Speeds in box units per second.
- Angles in degrees: `from_angle(a, m) = (m·cos a, m·sin a)`, `angle_of(v) = atan2(v.y, v.x)` in degrees. With `y` pointing down, a positive angle aims downwards.
- Double-precision floats (IEEE 754).

## 2. Constants

| Name | Value | Role |
|---|---|---|
| `DT` | `0.01` | fixed step, **never** tied to the frame rate |
| `MAX_STEPS` | `300` | beyond it: `timeout` failure (~3 s of flight) |
| `COLLISION_EPS` | `0.004` | margin added to every contact test |
| `TAP_MIN_TIME` | `0.1` | earliest tap instant searched by the solver |
| `MAX_WALL_BOUNCES` | `1` | default `max_wall_bounces` (the shipped JSON always writes it explicitly) |
| `SEGMENT_HALF_THICKNESS` | `0.012` | half-thickness of a segment without `r` |
| default disc radius | `0.03` | disc obstacle without `r` |
| default target radius | `0.045` | |
| default Photon radius | `0.02` | |
| default energy threshold | `0.6` | `barrier` obstacle without `energy_threshold` |

The renderer may run at any frame rate: it accumulates real time and runs as many **whole** `DT` steps as needed (the remainder carries over to the next frame, never simulated as a fractional step).

## 3. Initial state (launch)

- Position: `launcher.(x, y)`.
- Velocity: `from_angle(angle_deg, power)`; `power` is `1.0` when absent from the parameters.
- `precision` case (incertitude concept):
  - `snap = 2 + (1 − precision) · 28`;
  - `eff_angle = round(angle_deg / snap) · snap`, with Python's **banker's rounding** (half → even; in Kotlin `Math.rint`, not `Math.round`);
  - `power = max(0.15, 1.2 − precision)`;
  - velocity `= from_angle(eff_angle, power)`.
- `t = 0` at release. **Every oscillation is phase-locked to this instant**: the apparatus "starts" with the shot (decision still open in `todo.md`, but it is today's validated convention).
- State: `tapped = false`, `wall_bounces = 0`, `in_contact = ∅`, `collected = ∅`, `contacts = []`.

## 4. One simulation step — strict order

For `step = 0 … MAX_STEPS − 1`, with `t = (step + 1) · DT`:

1. **Move** (explicit Euler, constant velocity between two contacts): `pos += vel · DT`.
2. **Tap(s)**: the instants `tap_time`, `tap_time_2`… are handled in order; every tap whose instant is reached (`t ≥ tap_time_k`) sets `tapped = true` and, if Quarky is in superposition, **measures** (§7 bis). A tap therefore takes effect at the first step whose end reaches the gesture's instant, **before** that step's collisions.

Steps 3 to 6 apply to **each copy** of Quarky (only one outside superposition), in copy creation order.
3. **Box walls**: for each axis, if `x ≤ 0` → `x = 0`, `vel.x = |vel.x|`; if `x ≥ 1` → `x = 1`, `vel.x = −|vel.x|` (same for `y`). A step touching one or two walls counts **one** bounce. If `wall_bounces > max_wall_bounces` → `lost:too_many_wall_bounces` failure, immediate end.
4. **Obstacles**, in the order of the `obstacles` array (the velocity leaving one handler is the input of the next):
   1. effective position `(ox, oy)` = `motion` oscillation at time `t` (§6);
   2. if the obstacle does not **touch** `pos` (§5): remove it from `in_contact`, go to the next one;
   3. if it is already in `in_contact`: go to the next one (**one handler per contact**, not per step);
   4. otherwise add it to `in_contact`, compute the effective obstacle (position `(ox, oy)`; `energy_threshold` oscillated by `threshold_motion`, §6) and call its handler (§7) → `(vel, event)`;
   5. if `type ≠ wall`: append `(id, event)` to `contacts`;
   6. if `type = wall`: `wall_bounces += 1`; if `> max_wall_bounces` → `lost:too_many_wall_bounces` failure, immediate end.
5. **Photons**: for each uncollected Photon, position oscillated at `t`; collected if `dist(pos, photon) < r + COLLISION_EPS` (strict inequality).
6. **Target**: position oscillated at `t`; **success** if `dist(pos, target) < r + COLLISION_EPS`. Photons collected on that same step count.

After `MAX_STEPS` steps without success: `timeout` failure.

`max_wall_bounces` counts "suffered" bounces (box walls + `wall` obstacles). `mirror` bounces are intended and never counted.

## 5. Shapes and contact (`shapes.py`)

- **Disc**: `(x, y, r)`. Skeleton = its centre.
- **Flat segment** (when `length` is present): centre `(x, y)`, length `length`, orientation `angle_deg` (default 0); end points `centre ± (cos a, sin a) · length/2`. Skeleton = that segment, thickness `2 · r` (default `SEGMENT_HALF_THICKNESS`).
- `closest_point`: the centre for a disc; for a segment, the projection of `pos` on `[A, B]` clamped to `[0, 1]`.
- **Contact**: `dist(pos, closest_point) < radius + COLLISION_EPS` (strict). The bounding-circle pre-rejection (`radius + EPS + length/2`) is only an optimisation, with no effect on the result.
- **Normal**: `pos − closest_point` (not normalised; `reflect` normalises it, and a zero normal leaves the velocity unchanged).
- **Reflection**: `v' = v − 2 (v·n̂) n̂`. It is applied **even if the particle is already moving away** (no `v·n < 0` test) and the position is **not** pushed out of the obstacle. Discrete collision (no continuous sweep): the `DT` step + `COLLISION_EPS` is what stops thin segments being crossed at game speeds (`power ≤ 1`, i.e. ≤ 0.01 per step).

## 6. Oscillations ("oscillating element")

- `motion = {axis, amplitude, period, phase?}` on an obstacle, the target or a Photon: the `axis` coordinate (`"x"` or `"y"`) is `base + amplitude · sin(2π · t / period + phase)`, `phase` = 0 by default.
- `threshold_motion = {amplitude, period, phase?}` on a threshold obstacle: `energy_threshold(t) = base + amplitude · sin(2π · t / period + phase)`.
- Always evaluated at the current step's `t = (step + 1) · DT`, never at render time.

## 7. Handlers (`concepts/handlers.py`)

Handler choice: first by obstacle `type`, otherwise the level concept's default handler, otherwise `wall_reflect`.

| `type` | Handler | Effect | Event |
|---|---|---|---|
| `wall`, `mirror` | `wall_reflect` | reflection (§5) | `bounce` |
| `splitter` | `superposition_splitter` | flat splitter: the current copy keeps its velocity (transmitted), a new copy leaves with the reflected velocity (§5), see §7 bis | `transmit` (current copy) / `reflect` (new copy) |
| `detector` | — | no contact (Quarky passes through it); only used for the measurement, §7 bis | — |
| `barrier` | `tunnel_barrier` | if `‖v‖ ≥ energy_threshold(t)`: velocity unchanged; otherwise reflection | `pass` / `bounce` |
| `gate` | `intrication_gate` | `tapped`: passes; otherwise reflection | `pass` / `bounce` |
| `gate_anti` | `intrication_gate_anti` | `tapped`: reflection; otherwise passes | `bounce` / `pass` |
| `pole` | `spin_pole` | `spin = spin_up` (parameter, default `true`), flipped if `tapped`; `attracts = (spin ∧ pole = "+") ∨ (¬spin ∧ pole = "−")`; `kick = kick_deg` (default 40) if it attracts, otherwise `−kick_deg`; new direction `angle_of(v) + kick`, norm kept | `deflect` |
| `surface` | `dualite_surface` | not `tapped` (particle): reflection → `bounce`. `tapped` (wave): if `interference_offset_deg mod 360 = 180` → velocity unchanged (transmission); otherwise direction `angle_of(v_reflected) + offset` (default 15), norm kept | `bounce` / `wave` |

Default handlers per concept (obstacle of an unlisted type): `superposition` → splitter, `tunnel` → barrier, `intrication` → gate, `spin` → pole, `dualite` → surface, `incertitude` / `quantification` → `wall_reflect`.

### 7 bis. Superposition (ghost copies)

- On contact with a `splitter`, Quarky becomes two copies. Each copy has its own position, velocity, `in_contact`, `contacts`, `wall_bounces` and Photons (copied at the moment of the split). A copy touching another splitter splits in turn.
- **Measurement** = a tap while several copies exist: the copy closest to a `detector` is kept (distance to the detector's skeleton, at its oscillated position; tie → the first created). The others vanish **with their Photons**. `(detector id, "measure")` is appended to the survivor's contacts. A tap without superposition measures nothing.
- The **target** only accepts a measured Quarky: while there are several copies, step 6 is skipped.
- **Decoherence**: if a copy exceeds `max_wall_bounces` during the superposition, the whole launch fails (`lost:decoherence`).

The game doesn't need `must_contact` or the `contacts` log to play: they only serve the validator (anti-bypass). The events are still useful on the game side to trigger visual/sound effects.

## 8. Tap and parameters

- **One tap per flight**, except in superposition where each splitter may ask for its own measurement (`tap_time_2`, strictly after `tap_time`). Each tap instant is a parameter like the angle: the solver searches it on the `param_space` grid, **never below `TAP_MIN_TIME`** (a tap at launch = a disguised pre-launch setting). **Game design decision (validated):** in the game, a tap before `TAP_MIN_TIME` is ignored (the gesture stays available for the rest of the flight), which guarantees that every playable launch is one the validator checked.
- In the game, the tap instant is the simulated time elapsed since release when the input is handled; it is quantised to the step (§4.2).
- Solvability, tolerances and stars are **measured on the grid** `param_space` (`range`: from `min` to `max` by `step`, values rounded to 4 decimals; `choice`: list). Continuous dials stay playable, but only grid points are guaranteed.

## 9. Data consumed by the game

The game reads `content/levels/quantique/<name>.json` (`schema_version` = 3). Field reference: [`docs/level-schema.md`](level-schema.md). It refuses a `schema_version` it doesn't know. `levels-builder/meta/*.meta.json` is reserved for dev tools. Player-facing text is not in the level: the Codex lines are in `content/codex/<lang>/`.

## 10. Checking an implementation

- Expected tolerance: positions within `1e-6`. `sin`, `cos`, `atan2`, `hypot` may differ by one ulp between math libraries; a shot grazing an edge can therefore flip, hence the ≥ 5% tolerance requirement per level.
- Method ([ADR-0005](decisions/ADR-0005-golden-trajectories.md)): reference trajectories generated by the Python engine (`levels-builder/tests/golden/*.golden.json`: parameters → position at every step, outcome, Photons, contacts) and replayed by the target implementation (`android/core-physics` `GoldenTest`). For a level without golden files yet, replaying each level's `hint.params` must reach the target with the Photons of `reference_solution.photon_ids` (meta).

## 11. Known drifts of the Stage 2 mockup

The mockup (`design/mockups/index.html`, `quantiqueSubstep`) diverges from this contract, among others:
- Photon/target margin `0.012` instead of `COLLISION_EPS = 0.004`;
- internal walls as chains of discs, tested **at every step** (not "once per contact");
- last sub-step of each frame is fractional (`min(SIM_DT, remainder)`) instead of whole steps;
- `max_wall_bounces` hard-coded to 1, level hard-coded (no JSON reading).

It remains a mockup of visual intent; replacing it with a viewer that reads the exported JSON is planned (`todo.md` §4.1, "level viewer" tool).
