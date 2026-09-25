"""
Règles de collision « vulgarisées » par concept quantique (cf. skill
gameplay-mechanics et CLAUDE.md pour la liste des 8 concepts du premier monde).

Chaque handler a la signature :
    handler(obstacle: dict, pos: Vec2, vel: Vec2, params: dict, state: dict) -> (Vec2, str)

L'événement retourné est l'un de :
    'continue' — l'obstacle a dévié/réfléchi la trajectoire, la simulation continue
    'pass'     — l'obstacle est ignoré ce pas-ci (la particule le traverse)
    'trap'     — échec immédiat du niveau (ex : décohérence prématurée)
"""
from . import vec


def _bounce(obstacle, pos, vel):
    normal = vec.sub(pos, (obstacle["x"], obstacle["y"]))
    return vec.reflect(vel, normal), "continue"


def wall_reflect(obstacle, pos, vel, params, state):
    """Comportement par défaut : rebond simple, façon paroi de la boîte fermée."""
    return _bounce(obstacle, pos, vel)


def superposition_splitter(obstacle, pos, vel, params, state):
    """
    Le « séparateur » représente la mesure qui effondre la superposition :
    selon le point d'impact (moitié haute/basse de l'obstacle, donc selon
    l'angle de visée du joueur), la trajectoire est redirigée vers l'un des
    deux bras prédéfinis (arm_a_deg / arm_b_deg). Vulgarisation assumée : la
    vraie superposition est probabiliste, ici rendue déterministe et lisible.
    """
    offset_y = pos[1] - obstacle["y"]
    chosen = obstacle["arm_a_deg"] if offset_y <= 0 else obstacle["arm_b_deg"]
    return vec.from_angle(chosen, vec.mag(vel)), "continue"


def tunnel_barrier(obstacle, pos, vel, params, state):
    """
    Franchissement sous condition d'énergie : si la vitesse au contact
    dépasse le seuil de la barrière, la particule passe au travers
    (effet tunnel) ; sinon elle rebondit comme un mur classique.
    """
    if vec.mag(vel) >= obstacle.get("energy_threshold", 0.6):
        return vel, "pass"
    return _bounce(obstacle, pos, vel)


def intrication_gate(obstacle, pos, vel, params, state):
    """
    Porte liée à un « témoin » identique (cf. skill gameplay-mechanics —
    "Action déclenchée en vol") : le joueur tape UNE fois pendant le vol
    (instant = params["tap_time"], recherché par le solveur comme n'importe
    quel autre paramètre), ce qui bascule les deux objets — témoin et porte —
    au même instant. Avant le tap : porte fermée (bloque comme un mur).
    Après : ouverte (laisse passer).
    """
    if state.get("tapped", False):
        return vel, "pass"
    return _bounce(obstacle, pos, vel)


def spin_pole(obstacle, pos, vel, params, state):
    """
    Polarité de spin (+/-) déterminant si l'obstacle attire ou repousse.
    Réglage pré-tir (spin_up = polarité de départ, cf. gameplay-mechanics)
    ET action en vol : un tap (params["tap_time"]) inverse la polarité une
    fois pendant le vol — deux variables se combinent pour viser le bon
    contact au bon instant.
    """
    spin_up = params.get("spin_up", True)
    if state.get("tapped", False):
        spin_up = not spin_up
    pole = obstacle.get("pole", "+")
    attract = (spin_up and pole == "+") or (not spin_up and pole == "-")
    kick = obstacle.get("kick_deg", 40)
    kick = kick if attract else -kick
    ang = vec.angle_of(vel) + kick
    return vec.from_angle(ang, vec.mag(vel)), "continue"


def dualite_surface(obstacle, pos, vel, params, state):
    """
    Bascule onde/particule EN VOL (cf. gameplay-mechanics — "Action
    déclenchée en vol") : Quarky part en mode particule (rebond classique),
    et un tap pendant le vol (params["tap_time"]) le fait passer en mode
    onde pour le reste du trajet (rebond + décalage d'interférence, qui
    préfigure sans la dupliquer la vraie leçon de réflexion enseignée à
    l'échelle Macro, cf. skill storytelling).
    """
    vel2, _ = _bounce(obstacle, pos, vel)
    if state.get("tapped", False):
        ang = vec.angle_of(vel2) + obstacle.get("interference_offset_deg", 15)
        vel2 = vec.from_angle(ang, vec.mag(vel2))
    return vel2, "continue"


# Registre : concept -> handler par défaut pour ses obstacles spécifiques.
# Les concepts sans obstacle dédié (incertitude, quantification) n'utilisent
# que wall_reflect sur les parois de la boîte.
HANDLERS = {
    "superposition": superposition_splitter,
    "tunnel": tunnel_barrier,
    "intrication": intrication_gate,
    "incertitude": wall_reflect,
    "quantification": wall_reflect,
    "spin": spin_pole,
    "dualite": dualite_surface,
}


def handler_for(concept, obstacle_type):
    """Un obstacle peut surcharger le handler du concept via son propre type."""
    specific = {
        "wall": wall_reflect,
        "splitter": superposition_splitter,
        "barrier": tunnel_barrier,
        "gate": intrication_gate,
        "pole": spin_pole,
        "surface": dualite_surface,
    }
    return specific.get(obstacle_type, HANDLERS.get(concept, wall_reflect))
