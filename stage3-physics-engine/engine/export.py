"""
Export d'un niveau au format JSON, en deux fichiers :

- `levels/<nom>.json` — **livré dans le jeu** : géométrie, objets, Photons,
  plages de réglage publiques (`param_space`, pour les dials de l'UI) et
  `hint` (paramètres de la solution de référence, pour l'indice « premier
  segment » proposé après 5 échecs).
- `levels/meta/<nom>.meta.json` — **dev uniquement** : tout ce que calcule le
  validateur (solvabilité, tolérances, contournements, solution de référence
  complète, profil d'étoiles) + `must_contact`, qui ne sert qu'à valider.

`read_level` recolle les deux (cf. sa docstring) : `cli.py validate
levels/<nom>.json` fonctionne donc comme avant.
"""
import json
import os
import sys

from .simulate import MAX_WALL_BOUNCES
from .validator import validate

# Version du format JSON consommé par le jeu. À incrémenter à chaque
# changement incompatible (champ renommé/supprimé, sémantique modifiée) pour
# que le client puisse refuser un pack qu'il ne sait pas lire.
# v2 : séparation niveau livré / méta dev, `hint` remplace `reference_solution`
# dans le fichier livré, `max_wall_bounces` toujours explicite.
SCHEMA_VERSION = 2

# Champs du niveau livré, dans cet ordre (lisibilité des diffs). Un champ de
# niveau inconnu ici est ajouté à la fin plutôt que perdu en silence.
SHIPPED_KEYS = (
    "id", "scale", "concept", "difficulty", "codex_text",
    "launcher", "target", "obstacles", "photons",
    "max_wall_bounces", "param_space",
)
# Champs du niveau qui ne servent qu'au validateur : jamais livrés au jeu.
DEV_ONLY_KEYS = ("must_contact",)
META_DIR = "meta"


def build_export_payloads(level: dict) -> tuple:
    """(niveau livré, méta dev) pour un niveau généré."""
    report = validate(level)
    # schema_version en tête des deux fichiers, et toujours celui du moteur
    # courant (même si on ré-exporte un niveau lu depuis un ancien JSON).
    level = {k: v for k, v in level.items() if k != "schema_version"}
    # Valeur par défaut résolue ici : le jeu n'a pas à connaître celle du moteur.
    level.setdefault("max_wall_bounces", MAX_WALL_BOUNCES)

    shipped = {"schema_version": SCHEMA_VERSION}
    for k in SHIPPED_KEYS:
        if k in level:
            shipped[k] = level[k]
    for k, v in level.items():
        if k not in shipped and k not in DEV_ONLY_KEYS:
            shipped[k] = v
    best = report["best_solution"]
    shipped["hint"] = None if best is None else {"params": best["params"]}

    meta = {
        "schema_version": SCHEMA_VERSION,
        "id": level.get("id"),
        "must_contact": level.get("must_contact", []),
        "solvable": report["solvable"],
        "reference_solution": best,
        "max_photons_reachable": report["max_photons_reachable"],
        "tolerance": report["tolerance"],
        "three_star_tolerance": report["three_star_tolerance"],
        "bypass_solutions": report["bypass_solutions"],
        "star_profile": report["star_profile"],
    }
    return shipped, meta


def meta_path_for(level_path: str) -> str:
    """levels/<nom>.json -> levels/meta/<nom>.meta.json"""
    folder, name = os.path.split(level_path)
    stem = name[:-len(".json")] if name.endswith(".json") else name
    return os.path.join(folder, META_DIR, f"{stem}.meta.json")


def _dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_level(level: dict, path: str) -> tuple:
    """Écrit le niveau livré à `path` et sa méta à côté ; renvoie (livré, méta)."""
    shipped, meta = build_export_payloads(level)
    meta_path = meta_path_for(path)
    os.makedirs(os.path.dirname(meta_path) or ".", exist_ok=True)
    _dump(shipped, path)
    _dump(meta, meta_path)
    return shipped, meta


def read_level(path: str) -> dict:
    """
    Niveau prêt pour validate/solve : le fichier livré + `must_contact` lu
    dans la méta voisine (`meta/<nom>.meta.json`). Sans méta (pack livré
    seul), le niveau reste simulable mais `bypass_solutions` ne vérifie plus
    rien : on le signale sur stderr. Un ancien JSON v1 (must_contact inclus)
    se lit tel quel.
    """
    with open(path, "r", encoding="utf-8") as f:
        level = json.load(f)
    meta_path = meta_path_for(path)
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            level["must_contact"] = json.load(f).get("must_contact", [])
    elif "must_contact" not in level:
        print(f"[avertissement] {meta_path} absent : must_contact inconnu, "
              "contournements non vérifiés", file=sys.stderr)
    return level
