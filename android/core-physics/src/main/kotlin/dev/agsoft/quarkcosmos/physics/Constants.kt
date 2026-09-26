package dev.agsoft.quarkcosmos.physics

// Constantes du contrat déterministe (docs/physics-spec.md §2), identiques à
// stage3-physics-engine/engine/simulate.py et shapes.py.

/** Pas fixe, jamais calé sur le framerate. */
const val DT = 0.01
/** Au-delà : échec `timeout` (~3 s de vol). */
const val MAX_STEPS = 300
const val COLLISION_EPS = 0.004
/** Instant minimal d'un tap en vol : un tap plus tôt est ignoré (et reste disponible). */
const val TAP_MIN_TIME = 0.1
const val MAX_WALL_BOUNCES = 1
const val SEGMENT_HALF_THICKNESS = 0.012
const val DEFAULT_DISC_RADIUS = 0.03
const val DEFAULT_TARGET_RADIUS = 0.045
const val DEFAULT_PHOTON_RADIUS = 0.02
const val DEFAULT_ENERGY_THRESHOLD = 0.6
