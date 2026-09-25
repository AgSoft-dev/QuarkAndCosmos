"""Export d'un niveau (+ sa solution de référence) au format JSON attendu côté jeu."""
import json

from .validator import validate


def build_export_payload(level: dict) -> dict:
    report = validate(level)
    payload = dict(level)
    payload["solvable"] = report["solvable"]
    payload["reference_solution"] = report["best_solution"]
    payload["max_photons_reachable"] = report["max_photons_reachable"]
    return payload


def write_level(level: dict, path: str) -> dict:
    payload = build_export_payload(level)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


def read_level(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
