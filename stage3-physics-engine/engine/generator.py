"""
Génère un niveau « gabarit » (difficulté 1) par concept du premier monde
(échelle Quantique, cf. CLAUDE.md pour la liste des 7 concepts de la beta). Placement
volontairement simple/lisible — la difficulté 2/3 (progression intra-concept,
cf. gameplay-mechanics) sera dérivée de ces gabarits plus tard, une fois
validés.
"""

from .simulate import TAP_MIN_TIME
from .stars import place_photons

CODEX_PLACEHOLDER = {
    "superposition": "« Tu as suivi les deux chemins à la fois, jusqu'à ce que je regarde... et que l'un des deux devienne réel. »",
    "tunnel": "« Assez d'énergie, et même un mur n'est plus vraiment un mur. »",
    "intrication": "« Actionne le levier ici, et là-bas, à distance, quelque chose bouge. Personne ne sait vraiment pourquoi ça va aussi vite. »",
    "incertitude": "« Plus tu vises pile, moins tu sais à quelle vitesse tu iras. C'est le prix à payer pour être précis·e. »",
    "quantification": "« Pas de réglage continu ici : seulement quelques crans d'énergie possibles, ni plus ni moins. »",
    "spin": "« Ton spin détermine qui t'attire et qui te repousse — une boussole invisible. »",
    "dualite": "« Onde ou particule ? Aujourd'hui, tu as choisi de te faufiler comme une onde. »",
}


def _seg(id_, type_, x1, y1, x2, y2, **extra):
    """Obstacle plat (cf. shapes.py) défini par ses deux extrémités."""
    import math
    return dict({
        "id": id_, "type": type_,
        "x": round((x1 + x2) / 2, 4), "y": round((y1 + y2) / 2, 4),
        "length": round(math.hypot(x2 - x1, y2 - y1), 4),
        "angle_deg": round(math.degrees(math.atan2(y2 - y1, x2 - x1)), 2),
    }, **extra)


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
    # Photons posés par lancer de rayons (cf. stars.py) : la part des
    # chemins valides à 1/2/3 étoiles suit une gaussienne tronquée dont σ
    # diminue avec la difficulté.
    return place_photons(level)


def _superposition(difficulty):
    return {1: _superposition_1, 2: _superposition_2, 3: _superposition_3}[difficulty]()


def _superposition_1():
    # Découverte : la lame S coupe Quarky en deux copies fantômes — l'une
    # continue tout droit vers le plafond (et s'y écrase), l'autre part en
    # réflexion vers la cible. Taper = mesurer : Quarky devient la copie la
    # plus proche du détecteur D, posé du côté de la cible. Fenêtre : entre la
    # séparation et le moment où la copie réfléchie dépasse la cible (la cible
    # n'accepte qu'un Quarky mesuré). La cloison bloque le tir direct.
    return {
        "launcher": {"x": 0.4, "y": 0.9},
        "target": {"x": 0.85, "y": 0.55, "r": 0.05},
        "obstacles": [
            _seg("S", "splitter", 0.28, 0.67, 0.52, 0.43),
            _seg("D", "detector", 0.72, 0.3, 0.72, 0.36),
            _seg("cloison", "wall", 0.58, 0.64, 0.58, 1.0),
        ],
        "must_contact": [["S", "reflect"], ["D", "measure"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -100, "max": -80, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": 0.1, "max": 1.6, "step": 0.1},
        },
    }


def _superposition_2():
    # Boucle à deux miroirs (interféromètre) : la copie transmise monte puis
    # M1 la renvoie à droite, la copie réfléchie part à droite puis M2 la
    # renvoie en haut. Les deux copies se croisent près de la cible, donc
    # chacune peut l'atteindre : deux routes, garder l'une ou l'autre. Le
    # détecteur D balaie de haut en bas : c'est sa position à l'instant du tap
    # qui décide quelle copie devient réelle.
    return {
        "launcher": {"x": 0.2, "y": 0.92},
        "target": {"x": 0.8, "y": 0.1, "r": 0.05},
        "obstacles": [
            _seg("S", "splitter", 0.1, 0.7, 0.3, 0.5),
            _seg("M1", "mirror", 0.1, 0.3, 0.3, 0.1),
            _seg("M2", "mirror", 0.7, 0.7, 0.9, 0.5),
            dict(_seg("D", "detector", 0.47, 0.45, 0.53, 0.45),
                 motion={"axis": "y", "amplitude": 0.15, "period": 1.2, "phase": 3.14}),
            _seg("cloison", "wall", 0.36, 0.62, 0.36, 1.0),
        ],
        "must_contact": [["D", "measure"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -94, "max": -84, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.8, "step": 0.1},
            "tap_time": {"type": "range", "min": 0.3, "max": 3.0, "step": 0.1},
        },
    }


def _superposition_3():
    # Deux mesures en un vol : S1 sépare, garder la copie réfléchie (la
    # transmise s'écrase vite sur le couvercle : fenêtre courte), puis S2
    # sépare à nouveau, garder cette fois la copie qui monte vers la cible
    # avant que l'autre ne s'écrase à droite. Deux taps, chacun dans une
    # fenêtre entre deux contacts.
    return {
        "launcher": {"x": 0.3, "y": 0.9},
        "target": {"x": 0.62, "y": 0.12, "r": 0.05},
        "obstacles": [
            _seg("S1", "splitter", 0.2, 0.65, 0.4, 0.45),
            _seg("couvercle", "wall", 0.15, 0.35, 0.42, 0.35),
            _seg("S2", "splitter", 0.52, 0.65, 0.72, 0.45),
            _seg("D", "detector", 0.55, 0.39, 0.55, 0.45),
            _seg("cloison", "wall", 0.46, 0.62, 0.46, 1.0),
        ],
        "must_contact": [["S1", "reflect"], ["D", "measure"], ["S2", "reflect"], ["D", "measure"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -94, "max": -84, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.8, "step": 0.1},
            "tap_time": {"type": "range", "min": 0.3, "max": 1.4, "step": 0.1},
            "tap_time_2": {"type": "range", "min": 0.8, "max": 2.6, "step": 0.1},
        },
    }


def _tunnel(difficulty):
    return {1: _tunnel_1, 2: _tunnel_2, 3: _tunnel_3}[difficulty]()


def _barrier(id_, x1, y1, x2, y2, base, amplitude, period, phase):
    """Barrière d'énergie plate dont le seuil oscille (cf. simulate)."""
    return _seg(id_, "barrier", x1, y1, x2, y2, energy_threshold=base,
                threshold_motion={"amplitude": amplitude, "period": period, "phase": phase})


def _tunnel_2():
    # Résonance : deux barrières en série dont le seuil oscille (au pic, même
    # la puissance max ne passe pas). La puissance fixe à la fois la vitesse
    # ET les deux instants d'arrivée : il faut trouver une vitesse qui tombe
    # sur un creux du seuil aux deux barrières.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.88, "y": 0.5, "r": 0.05},
        "obstacles": [
            _barrier("b1", 0.38, 0.4, 0.38, 0.6, base=0.6, amplitude=0.4, period=0.8, phase=0.0),
            _barrier("b2", 0.66, 0.4, 0.66, 0.6, base=0.6, amplitude=0.4, period=0.8, phase=2.2),
        ] + _door_wall("w1", 0.38, 0.4, 0.6) + _door_wall("w2", 0.66, 0.4, 0.6),
        "must_contact": [["b1", "pass"], ["b2", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.3, "max": 0.95, "step": 0.05},
        },
    }


def _tunnel_3():
    # Barrière, miroir, barrière : traverser b1, se faire renvoyer vers le
    # haut par le miroir, traverser b2 (seuils oscillants décalés). Le trajet
    # plus long entre les deux barrières rend la résonance plus serrée. Le
    # pic du seuil (0.98) dépasse la puissance max (0.95) : la force brute ne
    # suffit jamais, il faut tomber dans un creux.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.6, "y": 0.16, "r": 0.04},
        "obstacles": [
            _barrier("b1", 0.34, 0.71, 0.34, 0.89, base=0.6, amplitude=0.38, period=0.9, phase=1.5),
            _seg("m", "mirror", 0.53, 0.87, 0.67, 0.73),
            _barrier("b2", 0.51, 0.45, 0.69, 0.45, base=0.6, amplitude=0.38, period=0.9, phase=3.0),
            _seg("ceilL", "wall", 0.34, 0.45, 0.51, 0.45),
            _seg("ceilR", "wall", 0.69, 0.45, 1.05, 0.45),
        ] + _door_wall("w1", 0.34, 0.71, 0.89),
        "must_contact": [["b1", "pass"], ["m", "bounce"], ["b2", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.3, "max": 0.95, "step": 0.05},
        },
    }


def _tunnel_1():
    # Intro : une seule barrière, fenêtre dans une paroi (même vocabulaire que
    # les difficultés 2-3). Son seuil oscille lentement et son pic (1.05)
    # dépasse la puissance max : il faut une vitesse suffisante ET arriver
    # pendant un creux. Retour visuel immédiat : on passe ou on rebondit.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.86, "y": 0.5, "r": 0.05},
        "obstacles": [
            _barrier("barrier", 0.5, 0.4, 0.5, 0.6, base=0.6, amplitude=0.45, period=1.0, phase=0.0),
        ] + _door_wall("w", 0.5, 0.4, 0.6),
        "must_contact": [["barrier", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.3, "max": 0.95, "step": 0.05},
        },
    }


def _intrication(difficulty):
    return {1: _intrication_1, 2: _intrication_2, 3: _intrication_3}[difficulty]()


def _door_wall(prefix, x, y0, y1):
    """Paroi verticale en x percée d'une ouverture [y0, y1] (pour une porte)."""
    return [_seg(f"{prefix}Top", "wall", x, -0.05, x, y0), _seg(f"{prefix}Bot", "wall", x, y1, x, 1.05)]


def _intrication_2():
    # Paire ANTI-corrélée : la porte A est ouverte tant qu'on n'a pas tapé,
    # la porte B est fermée tant qu'on n'a pas tapé. Un seul geste ouvre
    # l'une et ferme l'autre : il faut franchir A, PUIS taper, puis franchir B.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.88, "y": 0.5, "r": 0.05},
        "obstacles": [
            _seg("A", "gate_anti", 0.4, 0.42, 0.4, 0.58),
            _seg("B", "gate", 0.65, 0.42, 0.65, 0.58),
        ] + _door_wall("wA", 0.4, 0.42, 0.58) + _door_wall("wB", 0.65, 0.42, 0.58),
        "must_contact": [["A", "pass"], ["B", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.4, "step": 0.05},
        },
    }


def _intrication_3():
    # La porte M, intriquée avec B, sert de MIROIR tant qu'elle est fermée :
    # franchir A (anti : ouverte avant le tap), rebondir sur M (fermée) vers
    # le haut, PUIS taper pour ouvrir B (et M, mais on l'a déjà quittée).
    # Taper trop tôt : M s'ouvre et on la traverse ; beaucoup trop tôt : A se
    # ferme devant soi. Une seule fenêtre : entre le rebond sur M et B.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.55, "y": 0.18, "r": 0.05},
        "obstacles": [
            _seg("A", "gate_anti", 0.3, 0.72, 0.3, 0.88),
            _seg("M", "gate", 0.48, 0.87, 0.62, 0.73),
            _seg("B", "gate", 0.47, 0.45, 0.63, 0.45),
            _seg("ceilL", "wall", 0.3, 0.45, 0.47, 0.45),
            _seg("ceilR", "wall", 0.63, 0.45, 1.05, 0.45),
        ] + _door_wall("wA", 0.3, 0.72, 0.88),
        "must_contact": [["A", "pass"], ["M", "bounce"], ["B", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.6, "step": 0.05},
        },
    }


def _intrication_1():
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
        "must_contact": [["gate", "pass"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -3, "max": 3, "step": 1},
            "power": {"type": "choice", "values": [0.5, 0.7]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.0, "step": 0.05},
        },
    }


def _incertitude(difficulty):
    return {1: _incertitude_1, 2: _incertitude_2, 3: _incertitude_3}[difficulty]()


# Dial continu (curseur) : avec des crans, vitesse et instant d'arrivée
# seraient eux aussi discrets et la cible mobile deviendrait une loterie.
PRECISIONS = {"type": "range", "min": 0.3, "max": 1.0, "step": 0.05}


def _incertitude_2():
    # Dilemme : une fente étroite exige une visée précise (dial haut)... qui
    # ralentit Quarky, alors que la cible derrière la fente dérive. Un dial
    # imprécis va vite mais ne vise que par grands crans : il faut trouver le
    # compromis qui passe la fente ET arrive au bon moment.
    return {
        "launcher": {"x": 0.1, "y": 0.6},
        "target": {"x": 0.85, "y": 0.39, "r": 0.05,
                   "motion": {"axis": "y", "amplitude": 0.04, "period": 1.1}},
        "obstacles": _door_wall("slit", 0.45, 0.465, 0.535),
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -30, "max": 5, "step": 0.5},
            "precision": PRECISIONS,
        },
    }


def _incertitude_3():
    # Deux fentes alignées (ouverture plus serrée) et une cible qui dérive
    # plus vite : le compromis précision/vitesse se resserre.
    return {
        "launcher": {"x": 0.1, "y": 0.7},
        "target": {"x": 0.88, "y": 0.33, "r": 0.04,
                   "motion": {"axis": "y", "amplitude": 0.07, "period": 0.8}},
        "obstacles": _door_wall("slit1", 0.35, 0.535, 0.625) + _door_wall("slit2", 0.6, 0.42, 0.51),
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -35, "max": 5, "step": 0.5},
            "precision": PRECISIONS,
        },
    }


def _incertitude_1():
    # Element oscillant (cf. gameplay-mechanics) : la cible derive legerement
    # — se combine au compromis precision/vitesse deja existant (viser juste
    # ne suffit plus, il faut aussi arriver au bon moment).
    return {
        "launcher": {"x": 0.1, "y": 0.6},
        "target": {"x": 0.85, "y": 0.5, "r": 0.03, "motion": {"axis": "y", "amplitude": 0.02, "period": 0.8}},
        "obstacles": [],
        "param_space": {
            "angle_deg": {"type": "range", "min": -15, "max": 5, "step": 0.5},
            "precision": {"type": "choice", "values": [0.3, 0.5, 0.7, 0.8, 0.9, 1.0]},
        },
    }


def _quantification(difficulty):
    return {1: _quantification_1, 2: _quantification_2, 3: _quantification_3}[difficulty]()


QUANTA = [0.3, 0.45, 0.6, 0.75, 0.9]


def _quantification_2():
    # Le lanceur n'a que 5 crans d'énergie. Deux barrières en série au seuil
    # oscillant : chaque cran donne une vitesse ET des instants d'arrivée
    # différents : seuls deux crans (0.45 et 0.9) tombent dans un creux aux
    # deux barrières.
    # (En attente de la refonte "serrure accordée sur un cran" — [GATE] todo.)
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.88, "y": 0.5, "r": 0.05},
        "obstacles": [
            _barrier("b1", 0.36, 0.4, 0.36, 0.6, base=0.6, amplitude=0.4, period=0.7, phase=0.0),
            _barrier("b2", 0.64, 0.4, 0.64, 0.6, base=0.6, amplitude=0.4, period=0.7, phase=0.8),
        ] + _door_wall("w1", 0.36, 0.4, 0.6) + _door_wall("w2", 0.64, 0.4, 0.6),
        "must_contact": [["b1", "pass"], ["b2", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "choice", "values": QUANTA},
        },
    }


def _quantification_3():
    # Trois barrières dont une après un miroir : le bon cran doit tomber dans
    # un creux trois fois de suite : un seul cran (0.45) y parvient. On ne
    # peut pas "doser" : il faut choisir.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.6, "y": 0.16, "r": 0.06},
        "obstacles": [
            _barrier("b1", 0.3, 0.71, 0.3, 0.89, base=0.6, amplitude=0.4, period=0.7, phase=0.0),
            _barrier("b2", 0.44, 0.71, 0.44, 0.89, base=0.6, amplitude=0.4, period=0.7, phase=3.6),
            _seg("m", "mirror", 0.53, 0.87, 0.67, 0.73),
            _barrier("b3", 0.51, 0.45, 0.69, 0.45, base=0.6, amplitude=0.4, period=0.7, phase=0.8),
            _seg("ceilL", "wall", 0.44, 0.45, 0.51, 0.45),
            _seg("ceilR", "wall", 0.69, 0.45, 1.05, 0.45),
        ] + _door_wall("w1", 0.3, 0.71, 0.89) + _door_wall("w2", 0.44, 0.71, 0.89),
        "must_contact": [["b1", "pass"], ["b2", "pass"], ["m", "bounce"], ["b3", "pass"]],
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -12, "max": 12, "step": 1},
            "power": {"type": "choice", "values": QUANTA},
        },
    }


def _quantification_1():
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
        "must_contact": [["barrier", "pass"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -3, "max": 3, "step": 1},
            "power": {"type": "choice", "values": [0.2, 0.4, 0.6, 0.8, 1.0]},
        },
    }


def _spin(difficulty):
    return {1: _spin_1, 2: _spin_2, 3: _spin_3}[difficulty]()


def _spin_2():
    # Deux pôles "+" en série (façon Stern-Gerlach en cascade), chacun dévie
    # de 45° : spin haut = attiré (vers le haut), spin bas = repoussé. Pour
    # remonter en A puis revenir à l'horizontale en B, il faut partir spin
    # haut et inverser le spin ENTRE les deux pôles. Seule combinaison.
    return {
        "launcher": {"x": 0.1, "y": 0.72},
        "target": {"x": 0.86, "y": 0.51, "r": 0.05},
        "obstacles": [
            {"id": "A", "type": "pole", "x": 0.36, "y": 0.72, "r": 0.06, "pole": "+", "kick_deg": -45},
            {"id": "B", "type": "pole", "x": 0.555, "y": 0.465, "r": 0.06, "pole": "+", "kick_deg": -45},
        ],
        "must_contact": [["A", "deflect"], ["B", "deflect"]],
        # aucune bande : toucher une paroi = particule perdue
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -10, "max": 10, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "spin_up": {"type": "choice", "values": [True, False]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.4, "step": 0.05},
        },
    }


def _spin_3():
    # Trois pôles de signes +, −, + (déviations 40°, 40°, 60°) : il faut LIRE le signe
    # de chaque pôle. Monter en A (spin haut, attiré par +), encore monter en
    # B (pôle −, il faut être attiré donc spin bas : inverser entre A et B),
    # puis redescendre en C (pôle +, spin bas = repoussé). Le pôle C oscille :
    # la puissance doit aussi caler l'arrivée.
    return {
        "launcher": {"x": 0.1, "y": 0.9},
        "target": {"x": 0.792, "y": 0.416, "r": 0.05},
        "obstacles": [
            {"id": "A", "type": "pole", "x": 0.32, "y": 0.9, "r": 0.06, "pole": "+", "kick_deg": -40},
            {"id": "B", "type": "pole", "x": 0.49, "y": 0.707, "r": 0.06, "pole": "-", "kick_deg": -40},
            {"id": "C", "type": "pole", "x": 0.492, "y": 0.47, "r": 0.06, "pole": "+", "kick_deg": -60,
             "motion": {"axis": "x", "amplitude": 0.05, "period": 1.2}},
        ],
        "must_contact": [["A", "deflect"], ["B", "deflect"], ["C", "deflect"]],
        # aucune bande : toucher une paroi = particule perdue
        "max_wall_bounces": 0,
        "param_space": {
            "angle_deg": {"type": "range", "min": -10, "max": 10, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "spin_up": {"type": "choice", "values": [True, False]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.8, "step": 0.05},
        },
    }


def _spin_1():
    # Se combine au reglage pre-tir (spin_up = polarite de depart) : un tap
    # pendant le vol (cf. gameplay-mechanics) inverse la polarite une fois —
    # deux variables au lieu d'une pour viser le bon contact.
    # Cible placée sur la branche "repoussée" (déviation vers le bas) : il
    # faut soit partir spin bas, soit partir spin haut et taper AVANT le
    # contact avec le pôle. La déviation ne s'applique qu'une fois par
    # contact (cf. simulate.py) — l'ancienne cible (0.867, 0.69) n'était
    # atteinte que grâce à une déviation ré-appliquée à chaque pas, et
    # seulement sur 1° de visée.
    return {
        "launcher": {"x": 0.1, "y": 0.5},
        "target": {"x": 0.72, "y": 0.84, "r": 0.05},
        "obstacles": [
            {"id": "pole", "type": "pole", "x": 0.4, "y": 0.42, "r": 0.06,
             "pole": "+", "kick_deg": -60},
        ],
        "must_contact": [["pole", "deflect"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -20, "max": 0, "step": 1},
            "power": {"type": "choice", "values": [0.5, 0.7]},
            "spin_up": {"type": "choice", "values": [True, False]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 0.8, "step": 0.05},
        },
    }


def _dualite(difficulty):
    return {1: _dualite_1, 2: _dualite_2, 3: _dualite_3}[difficulty]()


def _dualite_2():
    # Séquence en deux temps, surfaces planes (angle d'incidence = angle de
    # réflexion) : s1 est un miroir à 45° qui renvoie une PARTICULE vers le
    # haut ; s2 est une fenêtre dans le plafond de la chambre du bas, qu'on
    # ne franchit qu'en ONDE. Le tap doit tomber entre les deux contacts :
    # trop tôt, Quarky traverse s1 en onde et file vers la droite ; trop
    # tard, il rebondit sur s2 comme une particule.
    return {
        "launcher": {"x": 0.1, "y": 0.8},
        "target": {"x": 0.45, "y": 0.14, "r": 0.05},
        "obstacles": [
            _seg("s1", "surface", 0.38, 0.87, 0.52, 0.73, interference_offset_deg=180),
            _seg("s2", "surface", 0.35, 0.42, 0.55, 0.42, interference_offset_deg=180),
            _seg("ceilL", "wall", -0.05, 0.42, 0.35, 0.42),
            _seg("ceilR", "wall", 0.55, 0.42, 1.05, 0.42),
        ],
        "must_contact": [["s1", "bounce"], ["s2", "wave"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -15, "max": 15, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 1.6, "step": 0.05},
        },
    }


def _dualite_3():
    # Chaîne : deux rebonds en particule (miroirs s1 puis s2 : droite -> haut
    # -> droite), puis traversée en onde de la fenêtre s3 vers la chambre de
    # droite, où la cible dérive. Le tap doit tomber entre s2 et s3, et la
    # puissance règle l'arrivée face à la cible mobile.
    return {
        "launcher": {"x": 0.1, "y": 0.85},
        "target": {"x": 0.86, "y": 0.45, "r": 0.05,
                   "motion": {"axis": "y", "amplitude": 0.08, "period": 1.6}},
        "obstacles": [
            _seg("s1", "surface", 0.25, 0.92, 0.39, 0.78, interference_offset_deg=180),
            _seg("s2", "surface", 0.18, 0.59, 0.39, 0.38, interference_offset_deg=180),
            _seg("s3", "surface", 0.65, 0.33, 0.65, 0.57, interference_offset_deg=180),
            _seg("wallTop", "wall", 0.65, -0.05, 0.65, 0.33),
            _seg("wallBot", "wall", 0.65, 0.57, 0.65, 1.05),
            _seg("shelf", "wall", 0.42, 0.66, 0.65, 0.66),
            # couvercle au-dessus de s2 : en onde trop tôt, Quarky traverse
            # s2 vers le haut et ne doit pas rejoindre s3 par le plafond
            _seg("lid", "wall", 0.18, 0.26, 0.5, 0.26),
        ],
        "must_contact": [["s1", "bounce"], ["s2", "bounce"], ["s3", "wave"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -15, "max": 15, "step": 1},
            "power": {"type": "range", "min": 0.4, "max": 0.9, "step": 0.1},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 2.2, "step": 0.05},
        },
    }


def _dualite_1():
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
        "must_contact": [["surface", "wave"]],
        "param_space": {
            "angle_deg": {"type": "range", "min": -3, "max": 3, "step": 1},
            "power": {"type": "choice", "values": [0.5, 0.7]},
            "tap_time": {"type": "range", "min": TAP_MIN_TIME, "max": 0.7, "step": 0.05},
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
# Difficultés disponibles par concept : 1 = découverte (une instance de la
# mécanique), 2 = séquence (la mécanique utilisée deux fois, dans les deux
# sens), 3 = enchaînement (trois instances ou deux + un élément mobile).
DIFFICULTIES = [1, 2, 3]
