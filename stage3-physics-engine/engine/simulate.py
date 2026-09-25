"""
Boucle de simulation générique pour l'échelle Quantique : boîte fermée,
SANS gravité (cf. skill art-direction — "Gravité : absente" pour cette
échelle), vitesse initiale donnée par les paramètres de lancer, rebonds sur
les parois, et déviations/événements pilotés par le concept du niveau.

Règle de base "action en vol" (cf. skill gameplay-mechanics) : en plus des
réglages pré-tir, chaque niveau peut porter une variable qui dépend du TEMPS
pendant le vol, via deux briques génériques :
  - "motion" sur un obstacle ou la cible : position oscillante (va-et-vient).
  - "threshold_motion" sur un obstacle à seuil (tunnel/quantification) :
    seuil d'énergie oscillant.
  - "tap_time" dans les params : un seul geste du joueur pendant le vol,
    dont l'instant est un paramètre de plus recherché par le solveur (comme
    l'angle ou la puissance) — cf. concepts.py pour les handlers qui
    consultent l'état "tapped" une fois l'instant dépassé.
"""
import math
from dataclasses import dataclass, field
from . import vec
from .concepts import handler_for

DT = 0.01
# Volontairement court (~3s de vol simulé) : au-delà, un rebond aléatoire dans
# la boîte finit presque toujours par "trouver" la cible par hasard, ce qui
# validerait des trajectoires qui n'utilisent pas vraiment la mécanique du
# concept. Un temps de vol court force une trajectoire directe/à peu de
# rebonds, donc une vraie résolution du puzzle.
MAX_STEPS = 300
COLLISION_EPS = 0.004
# Instant minimal d'un tap en vol (secondes simulées). En dessous, taper
# reviendrait à un réglage pré-tir déguisé (constat d'audit : les meilleures
# solutions de dualite/intrication tapaient à t=0), ce qui contredit la règle
# "action en vol" du skill gameplay-mechanics. Le validateur écarte ces tirs.
TAP_MIN_TIME = 0.1
# Rebonds "subis" (parois de la boîte + murs internes) tolérés avant de
# considérer la particule perdue, cf. commentaire dans simulate().
MAX_WALL_BOUNCES = 1


def _oscillate(base_x, base_y, motion, t):
    """Position effective d'un objet à l'instant t, décalée par une oscillation
    sinusoïdale sur un axe (cf. "Élément oscillant", skill gameplay-mechanics)."""
    if not motion:
        return base_x, base_y
    offset = motion["amplitude"] * math.sin(2 * math.pi * t / motion["period"] + motion.get("phase", 0.0))
    if motion["axis"] == "x":
        return base_x + offset, base_y
    return base_x, base_y + offset


def _effective_threshold(obstacle, t):
    """Seuil d'énergie effectif à l'instant t (cf. "Élément oscillant")."""
    motion = obstacle.get("threshold_motion")
    base = obstacle.get("energy_threshold", 0.6)
    if not motion:
        return base
    return base + motion["amplitude"] * math.sin(2 * math.pi * t / motion["period"] + motion.get("phase", 0.0))


@dataclass
class SimResult:
    success: bool
    reason: str = ""
    photons_collected: set = field(default_factory=set)
    steps: int = 0
    trail: list = field(default_factory=list)


def simulate(level: dict, params: dict, record_trail: bool = False) -> SimResult:
    launcher = level["launcher"]
    pos = (launcher["x"], launcher["y"])

    if "precision" in params:
        # Concept "incertitude" : la précision de visée (dial) fixe à la fois
        # le pas d'angle réellement atteignable (snap grossier si imprécis)
        # et la puissance maximale disponible (compromis, cf. gameplay-mechanics).
        precision = params["precision"]
        snap = 2 + (1 - precision) * 28
        eff_angle = round(params["angle_deg"] / snap) * snap
        power = max(0.15, 1.2 - precision)
        vel = vec.from_angle(eff_angle, power)
    else:
        vel = vec.from_angle(params["angle_deg"], params.get("power", 1.0))

    target = level["target"]
    photons = {p["id"]: p for p in level.get("photons", [])}
    collected = set()
    trail = []
    state = {}
    wall_bounces = 0
    # MAX_WALL_BOUNCES : au-delà, on considère la particule "perdue" (pas de
    # vraie table de pinball) — sans cette limite, un rebond mural chaotique
    # finit presque toujours par retrouver la cible "par hasard", ce qui
    # validerait des tirs n'utilisant pas la mécanique du concept.
    #
    # Obstacles actuellement en contact : un handler ne se déclenche qu'à
    # l'ENTRÉE dans le rayon d'un obstacle, pas à chaque pas passé dedans.
    # Avant, un pôle de spin ré-appliquait sa déviation à chaque pas de
    # contact (déviation totale = N * kick_deg, N dépendant de la vitesse),
    # et le franchissement d'une barrière était ré-évalué à chaque pas contre
    # un seuil qui oscille. Une interaction = un contact = un événement.
    in_contact = set()

    tap_time = params.get("tap_time")

    for step in range(MAX_STEPS):
        pos = vec.add(pos, vec.scale(vel, DT))
        elapsed = (step + 1) * DT
        if record_trail:
            trail.append(pos)

        # action en vol (tap) : un seul geste, dont l'instant est un
        # parametre recherche par le solveur au meme titre que l'angle ou la
        # puissance (cf. skill gameplay-mechanics — "Action declenchee en vol")
        if tap_time is not None and not state.get("tapped") and elapsed >= tap_time:
            state["tapped"] = True

        # parois de la boîte fermée (rebond, jamais de sortie)
        x, y = pos
        bounced = False
        if x <= 0.0:
            x, vel = 0.0, (abs(vel[0]), vel[1]); bounced = True
        elif x >= 1.0:
            x, vel = 1.0, (-abs(vel[0]), vel[1]); bounced = True
        if y <= 0.0:
            y, vel = 0.0, (vel[0], abs(vel[1])); bounced = True
        elif y >= 1.0:
            y, vel = 1.0, (vel[0], -abs(vel[1])); bounced = True
        if bounced:
            pos = (x, y)
            wall_bounces += 1
            if wall_bounces > MAX_WALL_BOUNCES:
                return SimResult(success=False, reason="lost:too_many_wall_bounces", steps=step, trail=trail)

        # obstacles specifiques au concept (position/seuil effectifs a
        # l'instant present si l'obstacle porte une oscillation, cf. "Element
        # oscillant" - skill gameplay-mechanics)
        for obs in level.get("obstacles", []):
            ox, oy = _oscillate(obs["x"], obs["y"], obs.get("motion"), elapsed)
            touching = vec.dist(pos, (ox, oy)) < obs.get("r", 0.03) + COLLISION_EPS
            if not touching:
                in_contact.discard(obs["id"])
                continue
            if obs["id"] in in_contact:
                continue
            in_contact.add(obs["id"])
            obs_eff = obs
            if obs.get("motion") or obs.get("threshold_motion"):
                obs_eff = dict(obs)
                obs_eff["x"], obs_eff["y"] = ox, oy
                obs_eff["energy_threshold"] = _effective_threshold(obs, elapsed)
            handler = handler_for(level["concept"], obs.get("type", ""))
            vel, event = handler(obs_eff, pos, vel, params, state)
            if obs.get("type") == "wall":
                # Un mur interne (ex : goulot d'entree) est un rebond "subi",
                # comme une paroi de la boite — compte dans le meme plafond,
                # sinon un tir raté peut ricocher indefiniment sur ces murs
                # et retomber "par hasard" sur la cible (cf. essais Stage 3
                # ayant motive MAX_WALL_BOUNCES a l'origine).
                wall_bounces += 1
                if wall_bounces > MAX_WALL_BOUNCES:
                    return SimResult(success=False, reason="lost:too_many_wall_bounces", steps=step, trail=trail)

        # photons (collecte pendant le vol, cf. gameplay-mechanics) ; un
        # Photon peut osciller (cf. stars.py : c'est ce qui rend le 3 étoiles
        # dépendant du timing quand tous les chemins valides se superposent)
        for pid, ph in photons.items():
            if pid in collected:
                continue
            px, py = _oscillate(ph["x"], ph["y"], ph.get("motion"), elapsed)
            if vec.dist(pos, (px, py)) < ph.get("r", 0.02) + COLLISION_EPS:
                collected.add(pid)

        # cible (position effective si oscillante)
        tx, ty = _oscillate(target["x"], target["y"], target.get("motion"), elapsed)
        if vec.dist(pos, (tx, ty)) < target.get("r", 0.045) + COLLISION_EPS:
            return SimResult(success=True, photons_collected=collected, steps=step, trail=trail)

    return SimResult(success=False, reason="timeout", steps=MAX_STEPS, trail=trail)
