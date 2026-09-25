# DA v2 — proof of concept (Stage 1, gate §1.1)

Open `index.html` in a browser (a single file with no build step; the only external resource is Google Fonts, and the page falls back to system fonts without it).

## What's on the page

1. **Three style frames of the same Quantum level** (`quantique_tunnel_1.json`, schema v2: partition with a barrier window, 3 real Photons, the file's hint shot), animated live. The **Boucle** mode chains success, success, failure. **Succès** and **Échec** force the outcome.
   - **A — Neon detector**: vector shapes + one additive bloom pass, a bubble-chamber trail, spiral tracks of charged particles along the cavity edges. This is the closest to the brief.
   - **B — Flat "Monument" lab**: flat fills (crescent shadow, facets), 4 colours, flat concentric discs around the portal, hard-edged fringes, bloom 0.18. It tests whether volume stays readable without gradients.
   - **C — Cinematic volumetric**: heavy bloom, 3 parallax layers tied to Quarky's position (distant bokeh → fringes/fog → foreground dust), god rays from the portal, grain and vignette at 3%.
   - The environment reacts to the result: on success the fringes lock into place and a scan line "resolves" the cavity; on failure the background decoheres into noise and Quarky fizzles out. The result appears as an instrument readout (HUD title), never as a pop-up over the play area.
   - Under each frame, a live measurement of background luminance compared with the matter layer (rule ≤ 20%).
2. **Quarky v2 sheet**: annotated anatomy, real sizes of 32/48/96 px, Quantum mutation (phase copies), the 8 procedural states, wave vs particle mode (Dualité). There's an A/B/C selector for rendering the sheets.
3. **Diegetic objects catalogue** (Quantum beta only): launcher, mirror, prism/splitter, potential barrier, entangled pair, Stern–Gerlach magnet, portal, Photon. Each is shown at rest and active.
4. **Colour contract**: key `#f472b6`, accent `#67e8f9`, background `#0a0612`, threshold `#fb923c`. WCAG contrast is computed in JS (all HUD pairs ≥ 4.5:1). There's a deuteranopia/protanopia simulation (Machado 2009) of frame A captured live, plus a ΔE table between pairs.

## Decisions requested

- **Gate §1.1**: pick **A**, **B**, **C** or a mix (e.g. "C's background + A's matter").
- **§1.2**: **Quarky v2** (glowing core + jelly membrane, eyes kept): **yes / no**.

## Data source and compromises

- Everything comes from `stage3-physics-engine/levels/quantique_tunnel_1.json` (schema v2): launcher (0.1, 0.5), portal (0.86, 0.5, r 0.05), a vertical partition at x 0.5 (`wTop` / `wBot`) with a barrier window 0.20 high (threshold 0.6 ± 0.45, period 1.0 s, shown in real time), and the file's 3 Photons (p1 oscillates in y).
- The demo shot is the file's `hint` (−4°, power 0.45) at the engine's real speed; it passes through the window and collects all 3 Photons. The failure replays the same angle at power 0.40, which the engine bounces off the barrier.
- The barrier is a zero-thickness segment in the engine; it is drawn 14 px thick so it can be read.
- Mid-energy Photon ↔ high-energy Photon: ΔE is low in deuteranopia (≈ 12). The redundant cue is the number of rays (4/6/8).

`screens/`: 2 reference captures (the three frames at 1440 px, frame A at 390 px).
