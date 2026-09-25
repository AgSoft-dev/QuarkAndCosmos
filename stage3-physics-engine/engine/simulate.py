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
from . import shapes, vec
from .concepts import handler_for, reflect_velocity

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
    # (id de l'obstacle, événement du handler) dans l'ordre des contacts
    contacts: list = field(default_factory=list)


@dataclass
class _Body:
    """Quarky, ou l'une de ses copies fantômes quand il est en superposition
    (cf. concepts.superposition_splitter). Chaque copie a sa trajectoire, ses
    contacts, ses rebonds subis et ses Photons : seuls ceux de la copie qui
    survit à la mesure comptent."""
    pos: tuple
    vel: tuple
    wall_bounces: int = 0
    in_contact: set = field(default_factory=set)
    contacts: list = field(default_factory=list)
    collected: set = field(default_factory=set)
    trail: list = field(default_factory=list)

    def fork(self, vel):
        return _Body(self.pos, vel, self.wall_bounces, set(self.in_contact),
                     list(self.contacts), set(self.collected), list(self.trail))


def tap_times(params: dict) -> list:
    """Instants des taps du lancer : `tap_time`, puis `tap_time_2`… (un
    niveau de superposition peut demander une mesure par séparateur)."""
    keys = sorted((k for k in params if k.startswith("tap_time")), key=lambda k: (len(k), k))
    return [params[k] for k in keys if params[k] is not None]


def taps_ordered(params: dict) -> bool:
    """Vrai si les taps successifs sont strictement dans l'ordre (sinon le
    même lancer serait compté deux fois par le solveur)."""
    keys = sorted((k for k in params if k.startswith("tap_time")), key=lambda k: (len(k), k))
    times = [params[k] for k in keys]
    return all(a < b for a, b in zip(times, times[1:]))


def _measure(bodies, level, elapsed):
    """Mesure (tap pendant une superposition) : Quarky se fixe sur la copie
    la plus proche d'un détecteur. Sans détecteur, rien n'est mesuré."""
    detectors = [o for o in level.get("obstacles", []) if o.get("type") == "detector"]
    if not detectors:
        return bodies, None
    best, best_d, best_det = None, None, None
    for body in bodies:
        for det in detectors:
            dx, dy = _oscillate(det["x"], det["y"], det.get("motion"), elapsed)
            d = shapes.distance(dict(det, x=dx, y=dy), body.pos)
            if best_d is None or d < best_d - 1e-12:
                best, best_d, best_det = body, d, det
    return [best], best_det["id"]


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
    state = {}
    # MAX_WALL_BOUNCES : au-delà, on considère la particule "perdue" (pas de
    # vraie table de pinball) — sans cette limite, un rebond mural chaotique
    # finit presque toujours par retrouver la cible "par hasard", ce qui
    # validerait des tirs n'utilisant pas la mécanique du concept.
    #
    # Obstacles actuellement en contact (par copie) : un handler ne se
    # déclenche qu'à l'ENTRÉE dans le rayon d'un obstacle, pas à chaque pas
    # passé dedans. Avant, un pôle de spin ré-appliquait sa déviation à chaque
    # pas de contact (déviation totale = N * kick_deg, N dépendant de la
    # vitesse), et le franchissement d'une barrière était ré-évalué à chaque
    # pas contre un seuil qui oscille. Une interaction = un contact = un
    # événement.
    bodies = [_Body(pos, vel)]
    # Un niveau peut autoriser plus de rebonds "subis" (ex : bande exigée).
    max_wall_bounces = level.get("max_wall_bounces", MAX_WALL_BOUNCES)
    obstacles = level.get("obstacles", [])

    taps = tap_times(params)
    next_tap = 0

    def result(success, body, reason, step):
        return SimResult(success=success, reason=reason,
                         photons_collected=body.collected if success else set(),
                         steps=step, trail=body.trail, contacts=body.contacts)

    for step in range(MAX_STEPS):
        elapsed = (step + 1) * DT
        for body in bodies:
            body.pos = vec.add(body.pos, vec.scale(body.vel, DT))
            if record_trail:
                body.trail.append(body.pos)

        # action en vol (tap) : un geste, dont l'instant est un paramètre
        # recherché par le solveur au même titre que l'angle ou la puissance
        # (cf. skill gameplay-mechanics — "Action déclenchée en vol"). En
        # superposition, un tap est une mesure ; sinon il n'a d'effet que sur
        # les objets qui consultent state["tapped"].
        while next_tap < len(taps) and elapsed >= taps[next_tap]:
            next_tap += 1
            state["tapped"] = True
            if len(bodies) > 1:
                bodies, det_id = _measure(bodies, level, elapsed)
                if det_id is not None:
                    bodies[0].contacts.append((det_id, "measure"))

        superposed = len(bodies) > 1
        spawned = []
        for body in bodies:
            # parois de la boîte fermée (rebond, jamais de sortie)
            x, y = body.pos
            vel = body.vel
            bounced = False
            if x <= 0.0:
                x, vel = 0.0, (abs(vel[0]), vel[1]); bounced = True
            elif x >= 1.0:
                x, vel = 1.0, (-abs(vel[0]), vel[1]); bounced = True
            if y <= 0.0:
                y, vel = 0.0, (vel[0], abs(vel[1])); bounced = True
            elif y >= 1.0:
                y, vel = 1.0, (vel[0], -abs(vel[1])); bounced = True
            body.vel = vel
            if bounced:
                body.pos = (x, y)
                body.wall_bounces += 1
                if body.wall_bounces > max_wall_bounces:
                    return result(False, body, _lost(superposed), step)

            # obstacles specifiques au concept (position/seuil effectifs a
            # l'instant present si l'obstacle porte une oscillation, cf.
            # "Element oscillant" - skill gameplay-mechanics)
            for obs in obstacles:
                if obs.get("type") == "detector":
                    continue  # instrument de mesure : ne touche pas Quarky
                ox, oy = _oscillate(obs["x"], obs["y"], obs.get("motion"), elapsed)
                placed = obs if (ox, oy) == (obs["x"], obs["y"]) else dict(obs, x=ox, y=oy)
                if not shapes.touching(placed, body.pos, COLLISION_EPS):
                    body.in_contact.discard(obs["id"])
                    continue
                if obs["id"] in body.in_contact:
                    continue
                body.in_contact.add(obs["id"])
                obs_eff = obs
                if obs.get("motion") or obs.get("threshold_motion"):
                    obs_eff = dict(obs)
                    obs_eff["x"], obs_eff["y"] = ox, oy
                    obs_eff["energy_threshold"] = _effective_threshold(obs, elapsed)
                handler = handler_for(level["concept"], obs.get("type", ""))
                body.vel, event = handler(obs_eff, body.pos, body.vel, params, state)
                if event == "split":
                    # Superposition : Quarky continue tout droit (copie
                    # transmise) ET part en réflexion (copie réfléchie).
                    ghost = body.fork(reflect_velocity(obs_eff, body.pos, body.vel))
                    body.contacts.append((obs["id"], "transmit"))
                    ghost.contacts.append((obs["id"], "reflect"))
                    spawned.append(ghost)
                elif obs.get("type") != "wall":
                    body.contacts.append((obs["id"], event))
                if obs.get("type") == "wall":
                    # Un mur interne (ex : goulot d'entree) est un rebond "subi",
                    # comme une paroi de la boite — compte dans le meme plafond,
                    # sinon un tir raté peut ricocher indefiniment sur ces murs
                    # et retomber "par hasard" sur la cible (cf. essais Stage 3
                    # ayant motive MAX_WALL_BOUNCES a l'origine).
                    body.wall_bounces += 1
                    if body.wall_bounces > max_wall_bounces:
                        return result(False, body, _lost(superposed), step)

            # photons (collecte pendant le vol, cf. gameplay-mechanics) ; un
            # Photon peut osciller (cf. stars.py : c'est ce qui rend le 3 étoiles
            # dépendant du timing quand tous les chemins valides se superposent)
            for pid, ph in photons.items():
                if pid in body.collected:
                    continue
                px, py = _oscillate(ph["x"], ph["y"], ph.get("motion"), elapsed)
                if vec.dist(body.pos, (px, py)) < ph.get("r", 0.02) + COLLISION_EPS:
                    body.collected.add(pid)

            # cible (position effective si oscillante) : elle n'accepte qu'un
            # Quarky mesuré — une copie fantôme la traverse sans l'atteindre.
            if superposed:
                continue
            tx, ty = _oscillate(target["x"], target["y"], target.get("motion"), elapsed)
            if vec.dist(body.pos, (tx, ty)) < target.get("r", 0.045) + COLLISION_EPS:
                return result(True, body, "", step)
        bodies = bodies + spawned

    return result(False, bodies[0], "timeout", MAX_STEPS)


def _lost(superposed):
    # Une copie qui s'écrase avant la mesure brise la superposition
    # (décohérence) : tout le lancer échoue, pas seulement cette copie.
    return "lost:decoherence" if superposed else "lost:too_many_wall_bounces"
