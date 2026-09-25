"""Export d'un niveau (+ sa solution de référence) au format JSON attendu côté jeu."""
import json

from .validator import validate

# Version du format JSON consommé par le jeu. À incrémenter à chaque
# changement incompatible (champ renommé/supprimé, sémantique modifiée) pour
# que le client puisse refuser un pack qu'il ne sait pas lire.
SCHEMA_VERSION = 1


def build_export_payload(level: dict) -> dict:
    report = validate(level)
    # schema_version en tête du fichier, et toujours celui du moteur courant
    # (même si on ré-exporte un niveau lu depuis un ancien JSON).
    payload = {"schema_version": SCHEMA_VERSION}
    payload.update({k: v for k, v in level.items() if k != "schema_version"})
    payload["solvable"] = report["solvable"]
    payload["reference_solution"] = report["best_solution"]
    payload["max_photons_reachable"] = report["max_photons_reachable"]
    payload["tolerance"] = report["tolerance"]
    payload["three_star_tolerance"] = report["three_star_tolerance"]
    payload["star_profile"] = report["star_profile"]
    return payload


def write_level(level: dict, path: str) -> dict:
    payload = build_export_payload(level)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


def read_level(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
