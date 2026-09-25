"""
Règles de collision « vulgarisées » par concept quantique (cf. skill
gameplay-mechanics et CLAUDE.md pour la liste des 7 concepts de la beta).

Chaque handler a la signature :
    handler(obstacle: dict, pos: Vec2, vel: Vec2, params: dict, state: dict) -> (Vec2, str)

L'événement retourné décrit ce qui s'est passé au contact (il est consigné
dans SimResult.contacts, ce qui permet au validateur de vérifier qu'une
solution utilise bien la mécanique voulue, cf. `must_contact`) :
    'bounce'  — réflexion sur l'obstacle
    'deflect' — déviation (séparateur, pôle de spin)
    'pass'    — la particule traverse l'obstacle
    'wave'    — réflexion en mode onde (dualité)
    'split'   — passage en superposition (consigné comme 'transmit' /
                'reflect' selon la copie ; la mesure ajoute 'measure')

Un handler n'est appelé qu'une fois par contact (à l'entrée dans le rayon de
l'obstacle), cf. simulate.py.
"""
from . import shapes, vec


def _bounce(obstacle, pos, vel):
    return vec.reflect(vel, shapes.normal(obstacle, pos)), "bounce"


def wall_reflect(obstacle, pos, vel, params, state):
    """Comportement par défaut : rebond simple, façon paroi de la boîte fermée."""
    return _bounce(obstacle, pos, vel)


def superposition_splitter(obstacle, pos, vel, params, state):
    """
    Lame séparatrice (plate) : au contact, Quarky passe en superposition. Il
    continue tout droit (copie transmise) ET repart en réflexion (copie
    réfléchie) — deux copies fantômes qui volent en même temps (cf.
    simulate._Body). Le tap est la mesure : Quarky se fixe sur la copie la
    plus proche d'un détecteur, l'autre s'efface avec ses Photons. La cible
    n'accepte qu'un Quarky mesuré, et une copie qui s'écrase avant la mesure
    brise la superposition (décohérence : le lancer échoue).
    Vulgarisation assumée : la vraie mesure est aléatoire, ici le moment et
    le détecteur la rendent déterministe et jouable (cf. page Codex).
    """
    return vel, "split"


def reflect_velocity(obstacle, pos, vel):
    """Vitesse de la copie réfléchie par une lame séparatrice."""
    return vec.reflect(vel, shapes.normal(obstacle, pos))


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


def intrication_gate_anti(obstacle, pos, vel, params, state):
    """
    Partenaire anti-corrélé d'une porte intriquée : ouverte AVANT le tap,
    fermée après. Le même geste ouvre une porte et en ferme une autre — deux
    objets intriqués dont les états sont toujours opposés (vulgarisation des
    mesures anti-corrélées d'une paire intriquée). Crée une fenêtre de tap :
    il faut avoir franchi celle-ci AVANT de taper.
    """
    if state.get("tapped", False):
        return _bounce(obstacle, pos, vel)
    return vel, "pass"


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
    return vec.from_angle(ang, vec.mag(vel)), "deflect"


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
        offset = obstacle.get("interference_offset_deg", 15)
        if offset % 360 == 180:
            # 180° = transmission pure : l'onde traverse la surface sans
            # changer de direction, quelle que soit l'incidence (sinon, sur
            # une surface inclinée, "rebond + 180°" renvoie une image miroir
            # de la direction, illisible pour le joueur).
            return vel, "wave"
        ang = vec.angle_of(vel2) + offset
        return vec.from_angle(ang, vec.mag(vel2)), "wave"
    return vel2, "bounce"


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
        # miroir plat : instrument de labo (rebond voulu, jamais compté comme
        # rebond "subi" contrairement aux parois)
        "mirror": wall_reflect,
        "splitter": superposition_splitter,
        "barrier": tunnel_barrier,
        "gate": intrication_gate,
        "gate_anti": intrication_gate_anti,
        "pole": spin_pole,
        "surface": dualite_surface,
    }
    return specific.get(obstacle_type, HANDLERS.get(concept, wall_reflect))
