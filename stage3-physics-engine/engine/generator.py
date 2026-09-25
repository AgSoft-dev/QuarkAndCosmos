"""
Génère un niveau « gabarit » (difficulté 1) par concept du premier monde
(échelle Quantique, cf. CLAUDE.md pour la liste des 8 concepts). Placement
volontairement simple/lisible — la difficulté 2/3 (progression intra-concept,
cf. gameplay-mechanics) sera dérivée de ces gabarits plus tard, une fois
validés.
"""

CODEX_PLACEHOLDER = {
    "superposition": "« Tu as suivi les deux chemins à la fois, jusqu'à ce que je regarde... et que l'un des deux devienne réel. »",
    "tunnel": "« Assez d'énergie, et même un mur n'est plus vraiment un mur. »",
    "intrication": "« Actionne le levier ici, et là-bas, à distance, quelque chose bouge. Personne ne sait vraiment pourquoi ça va aussi vite. »",
    "incertitude": "« Plus tu vises pile, moins tu sais à quelle vitesse tu iras. C'est le prix à payer pour être précis·e. »",
    "quantification": "« Pas de réglage continu ici : seulement quelques crans d'énergie possibles, ni plus ni moins. »",
    "spin": "« Ton spin détermine qui t'attire et qui te repousse — une boussole invisible. »",
    "dualite": "« Onde ou particule ? Aujourd'hui, tu as choisi de te faufiler comme une onde. »",
}


def _photon(id_, x, y, r=0.025):
    return {"id": id_, "x": x, "y": y, "r": r}


def _wall_column(id_prefix, x, edge_y, direction, far_limit, r=0.05, spacing=0.06):
    """
    Chaîne de cercles « mur » (type obstacle générique, cf. concepts.HANDLERS
    — rebond simple façon paroi) formant une barrière pleine à partir d'un
    bord précis (edge_y — p.ex. la limite d'une ouverture) et s'étendant vers
    l'extérieur (direction = -1 vers le haut de l'écran / +1 vers le bas)
    jusqu'à far_limit. Le premier cercle est ancré EXACTEMENT sur edge_y (son
    bord touche edge_y pile), pas seulement "environ" comme le ferait un
    espacement régulier depuis un point de départ arbitraire — un mauvais
    calage ici a laissé passer une visée à travers un vrai trou lors des
    tests (cf. commentaire dans _superposition). Le spacing < 2*r garantit
    ensuite un recouvrement sans trou pour tout le reste de la colonne.
    """
    obstacles = []
    center = edge_y + direction * r
    i = 0
    while (center <= far_limit if direction > 0 else center >= far_limit):
        obstacles.append({"id": f"{id_prefix}{i}", "type": "wall", "x": x, "y": round(center, 4), "r": r})
        center += direction * spacing
        i += 1
    return obstacles


def make_level(concept: str, difficulty: int = 1) -> dict:
    builder = _BUILDERS.get(concept)
    if builder is None:
        raise ValueError(f"Concept inconnu: {concept}")
    level = builder(difficulty)
    level["id"] = f"quantique-{concept}-{difficulty}"
    level["scale"] = "quantique"
    level["concept"] = concept
    level["difficulty"] = difficulty
    level.setdefault("codex_text", CODEX_PLACEHOLDER.get(concept, ""))
    return level


def _superposition(difficulty):
    # Un "chute d'entrée" (goulot) proche du lanceur oblige le joueur à viser
    # dans un cône étroit avant même d'atteindre le séparateur — c'est ce qui
    # rend le séparateur obligatoire (avant, une visée directe en ligne droite
    # pouvait atteindre le Photon puis la cible sans jamais le toucher, cf.
    # retour test manuel). Le goulot est placé À DISTANCE du séparateur (x=0.22
    # vs séparateur x=0.35) plutôt que collé dessus : sinon les murs du goulot
    # bloquent le bras de sortie du séparateur lui-même juste après la
    # redirection, et la particule reste piégée à ricocher sur place (bug
    # constaté en test : un tir parfaitement droit se bloquait juste après
    # avoir été redirigé). Le cône du goulot (~16°) est volontairement plus
    # étroit que le cône du séparateur (~18°, rayon 0.075) : tout ce qui passe
    # le goulot est donc garanti de toucher le séparateur ensuite.
    # Cône du goulot (16°) volontairement plus étroit que le cône du séparateur
    # (~18°, rayon 0.075 à distance 0.23) : tan(16°)*0.10 = 0.0287 -> le bord
    # de l'ouverture est ancré à 0.5 ± 0.0287 pile (cf. _wall_column, qui
    # calle le premier cercle exactement dessus plutôt qu'"à peu près").
    CHUTE_X = 0.22
    CHUTE_HALF = 0.0287
    chute = (
        _wall_column("chuteTop", x=CHUTE_X, edge_y=0.5 - CHUTE_HALF, direction=-1, far_limit=-0.05, r=0.12, spacing=0.10)
        + _wall_column("chuteBot", x=CHUTE_X, edge_y=0.5 + CHUTE_HALF, direction=1, far_limit=1.05, r=0.12, spacing=0.10)
    )
    # Element oscillant (cf. gameplay-mechanics) : le separateur derive
    # legerement de haut en bas — amplitude volontairement petite (niveau
    # d'entree du monde, doit rester approchable), juste assez pour que le
    # moment ou l'on tire influence quel bras on obtient, pas seulement
    # l'angle vise.
    return {
        "launcher": {"x": 0.12, "y": 0.5},
        "target": {"x": 0.85, "y": 0.15, "r": 0.05},
        "obstacles": chute + [
            {"id": "splitter", "type": "splitter", "x": 0.35, "y": 0.5, "r": 0.075,
             "arm_a_deg": -35, "arm_b_deg": 35,
             "motion": {"axis": "y", "amplitude": 0.015, "period": 0.6}},
        ],
        "photons": [_photon("p1", 0.6, 0.283, 0.03)],
        "param_space": {
            "angle_deg": {"type": "range", "min": -15, "max": 15, "step": 1},
            "power": {"type": "choice", "values": [0.4, 0.6, 0.8]},
        },
    }


def _tunnel(difficulty):
    # Element oscillant (cf. gameplay-mechanics) : le seuil d'energie de la
    # barriere varie dans le temps — il ne suffit plus d'avoir assez de
    # vitesse, il faut aussi que l'arrivee sur la barriere coincide avec une
    # phase ou le seuil est assez bas (ou avoir assez de vitesse pour battre
    # meme le pic).
    return {
        "launcher": {"x": 0.1, "y": 0.85},
        "target": {"x": 0.85, "y": 0.15, "r": 0.05},
        "obstacles": [
            {"id": "barrier", "type": "barrier", "x": 0.5, "y": 0.48, "r": 0.05,
             "energy_threshold": 0.65,
             "threshold_motion": {"amplitude": 0.45, "period": 0.15, "phase": 4.0}},
        ],
        "photons": [_photon("p1", 0.835, 0.288, 0.03)],
        "param_space": {
            "angle_deg": {"type": "range", "min": -49, "max": -38, "step": 1},
            "power": {"type": "choice", "values": [0.3, 0.5, 0.7, 0.9]},
        },
    }


def _intrication(difficulty):
    # Action declenchee en vol (cf. gameplay-mechanics) remplace le levier
    # pre-tir : le joueur tape UNE fois pendant le vol (tap_time, recherche
    # par le solveur comme l'angle ou la puissance) — le temoin ET la porte
    # basculent au meme instant. Trop tot ou trop tard = porte fermee au
    # moment du passage = rebond.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.85, "y": 0.5, "r": 0.05},
        "obstacles": [
            {"id": "gate", "type": "gate", "x": 0.5, "y": 0.5, "r": 0.05},
        ],
        "photons": [
            _photon("p1", 0.22, 0.5, 0.025),
            _photon("p2", 0.35, 0.5, 0.025),
            _photon("p3", 0.7, 0.5, 0.025),
        ],
        "param_space": {
            "angle_deg": {"type": "range", "min": -3, "max": 3, "step": 1},
            "power": {"type": "choice", "values": [0.5, 0.7]},
            "tap_time": {"type": "range", "min": 0.0, "max": 1.0, "step": 0.05},
        },
    }


def _incertitude(difficulty):
    # Element oscillant (cf. gameplay-mechanics) : la cible derive legerement
    # — se combine au compromis precision/vitesse deja existant (viser juste
    # ne suffit plus, il faut aussi arriver au bon moment).
    return {
        "launcher": {"x": 0.1, "y": 0.6},
        "target": {"x": 0.85, "y": 0.5, "r": 0.03, "motion": {"axis": "y", "amplitude": 0.02, "period": 0.8}},
        "obstacles": [],
        "photons": [_photon("p1", 0.45, 0.553, 0.03)],
        "param_space": {
            "angle_deg": {"type": "range", "min": -15, "max": 5, "step": 0.5},
            "precision": {"type": "choice", "values": [0.3, 0.5, 0.7, 0.8, 0.9, 1.0]},
        },
    }


def _quantification(difficulty):
    # Element oscillant (cf. gameplay-mechanics), meme principe que le tunnel :
    # le seuil de la barriere varie dans le temps, en plus des crans d'energie
    # fixes du lanceur (les deux variables se combinent).
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.85, "y": 0.5, "r": 0.05},
        "obstacles": [
            {"id": "barrier", "type": "barrier", "x": 0.45, "y": 0.5, "r": 0.05,
             "energy_threshold": 0.65,
             "threshold_motion": {"amplitude": 0.45, "period": 0.2, "phase": 1.2}},
        ],
        "photons": [_photon("p1", 0.65, 0.5, 0.03)],
        "param_space": {
            "angle_deg": {"type": "range", "min": -3, "max": 3, "step": 1},
            "power": {"type": "choice", "values": [0.2, 0.4, 0.6, 0.8, 1.0]},
        },
    }


def _spin(difficulty):
    # Se combine au reglage pre-tir (spin_up = polarite de depart) : un tap
    # pendant le vol (cf. gameplay-mechanics) inverse la polarite une fois —
    # deux variables au lieu d'une pour viser le bon contact.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.867, "y": 0.69, "r": 0.04},
        "obstacles": [
            {"id": "pole", "type": "pole", "x": 0.4, "y": 0.42, "r": 0.06,
             "pole": "+", "kick_deg": -60},
        ],
        "photons": [_photon("p1", 0.6, 0.641, 0.03)],
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": -11, "step": 1},
            "power": {"type": "choice", "values": [0.5, 0.7]},
            "spin_up": {"type": "choice", "values": [True, False]},
            "tap_time": {"type": "range", "min": 0.0, "max": 0.8, "step": 0.05},
        },
    }


def _dualite(difficulty):
    # Action declenchee en vol (cf. gameplay-mechanics) remplace le reglage
    # pre-tir : Quarky part en mode particule, un tap pendant le vol
    # (tap_time) bascule en mode onde pour le reste du trajet.
    return {
        "launcher": {"x": 0.08, "y": 0.3},
        "target": {"x": 0.85, "y": 0.3, "r": 0.05},
        "obstacles": [
            {"id": "surface", "type": "surface", "x": 0.35, "y": 0.3, "r": 0.05,
             "interference_offset_deg": 180},
        ],
        "photons": [_photon("p1", 0.6, 0.3, 0.03)],
        "param_space": {
            "angle_deg": {"type": "range", "min": -3, "max": 3, "step": 1},
            "power": {"type": "choice", "values": [0.5, 0.7]},
            "tap_time": {"type": "range", "min": 0.0, "max": 0.7, "step": 0.05},
        },
    }


# Ordre = ordre d'introduction dans le monde Quantique (beta), cf. CLAUDE.md.
# "tunnel" ouvre le monde : mécanique la plus immédiate (seuil de vitesse à
# franchir/pas franchir, un seul obstacle, retour visuel évident) pour
# habituer le joueur au lancer en boîte fermée sans gravité avant de lui
# demander de comprendre un choix de chemin (superposition).
_BUILDERS = {
    "tunnel": _tunnel,
    "superposition": _superposition,
    "intrication": _intrication,
    "incertitude": _incertitude,
    "quantification": _quantification,
    "spin": _spin,
    "dualite": _dualite,
}

ALL_CONCEPTS = list(_BUILDERS.keys())
