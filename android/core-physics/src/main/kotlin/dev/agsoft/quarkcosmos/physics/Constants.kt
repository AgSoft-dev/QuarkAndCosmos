package dev.agsoft.quarkcosmos.physics

// Constants of the deterministic contract (docs/physics-spec.md §2), identical
// to levels-builder/src/quarkcosmos_levels/core/simulate.py and shapes.py.

/** Fixed step, never tied to the frame rate. */
const val DT = 0.01
/** Beyond it: `timeout` failure (~3 s of flight). */
const val MAX_STEPS = 300
const val COLLISION_EPS = 0.004
/** Earliest in-flight tap: an earlier tap is ignored (and stays available). */
const val TAP_MIN_TIME = 0.1
const val MAX_WALL_BOUNCES = 1
const val SEGMENT_HALF_THICKNESS = 0.012
const val DEFAULT_DISC_RADIUS = 0.03
const val DEFAULT_TARGET_RADIUS = 0.045
const val DEFAULT_PHOTON_RADIUS = 0.02
const val DEFAULT_ENERGY_THRESHOLD = 0.6
/** Tunnel model (concepts/tunnel.py, ADR-0008): E_t(d) = TUNNEL_HEIGHT − (TUNNEL_K / d)². */
const val TUNNEL_HEIGHT = 1.2
const val TUNNEL_K = 0.019
