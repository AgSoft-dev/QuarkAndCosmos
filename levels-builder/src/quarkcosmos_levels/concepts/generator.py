"""
Level generation for the first world (Quantum scale; the 7 beta concepts are
listed in the gameplay-mechanics skill). Each concept is a plugin module
(concepts/<concept>.py, registered in concepts/__init__.py) that provides its
templates; this module adds the level identity and places the Photons.

Player-facing text (the Codex line of each concept) is not generated here: it
lives in content/codex/{en,fr}/quantique.json, keyed by the module's CODEX_KEY.
"""

from ..solver.stars import place_photons
from . import ALL_CONCEPTS, DIFFICULTIES, concept

__all__ = ["ALL_CONCEPTS", "DIFFICULTIES", "make_level"]


def make_level(concept_id: str, difficulty: int = 1) -> dict:
    try:
        module = concept(concept_id)
    except KeyError:
        raise ValueError(f"Unknown concept: {concept_id}") from None
    level = module.build(difficulty)
    level["id"] = f"quantique-{concept_id}-{difficulty}"
    level["scale"] = "quantique"
    level["concept"] = concept_id
    level["difficulty"] = difficulty
    # Photons placed by ray tracing (see stars.py): the share of valid paths
    # earning 1/2/3 stars follows a truncated gaussian whose σ shrinks with
    # difficulty.
    return place_photons(level)
