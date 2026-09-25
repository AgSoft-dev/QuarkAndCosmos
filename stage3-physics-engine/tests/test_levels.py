"""Contrat des niveaux du monde Quantique (cf. CLAUDE.md et gameplay-mechanics)."""
import functools
import glob
import json
import os

import pytest

from engine.export import SCHEMA_VERSION, build_export_payload
from engine.generator import ALL_CONCEPTS, DIFFICULTIES, make_level
from engine.simulate import TAP_MIN_TIME
from engine.stars import PHOTONS_PER_LEVEL

LEVELS_DIR = os.path.join(os.path.dirname(__file__), "..", "levels")
# Part minimale de la grille de paramètres qui doit atteindre la cible : en
# dessous, le niveau est "solvable" sur le papier mais injouable au doigt.
MIN_TOLERANCE = 0.05
CASES = [(c, d) for c in ALL_CONCEPTS for d in DIFFICULTIES]


@functools.lru_cache(maxsize=None)
def _payload(concept, difficulty):
    # make_level + validation une seule fois par niveau pour toute la suite
    return json.loads(json.dumps(build_export_payload(make_level(concept, difficulty))))


def test_beta_has_seven_concepts():
    assert len(ALL_CONCEPTS) == 7


@pytest.mark.parametrize("concept,difficulty", CASES)
def test_level_is_solvable_without_bypass(concept, difficulty):
    # Chaque lancer réussi doit utiliser la mécanique déclarée (must_contact) :
    # aucun niveau ne se résout en contournant ce qu'il est censé enseigner.
    payload = _payload(concept, difficulty)
    assert payload["solvable"]
    # (incertitude n'a pas d'objet de mécanique : la mécanique est le dial)
    if any(o["type"] != "wall" for o in payload["obstacles"]):
        assert payload.get("must_contact"), "le niveau déclare la mécanique à utiliser"
    assert payload["bypass_solutions"] == 0


@pytest.mark.parametrize("concept,difficulty", CASES)
def test_three_photons_all_collectable(concept, difficulty):
    payload = _payload(concept, difficulty)
    assert len(payload["photons"]) == PHOTONS_PER_LEVEL
    assert payload["max_photons_reachable"] == PHOTONS_PER_LEVEL


@pytest.mark.parametrize("concept,difficulty", CASES)
def test_level_is_not_brittle(concept, difficulty):
    assert _payload(concept, difficulty)["tolerance"] >= MIN_TOLERANCE


@pytest.mark.parametrize("concept,difficulty", CASES)
def test_reference_solution_taps_in_flight(concept, difficulty):
    tap = _payload(concept, difficulty)["reference_solution"]["params"].get("tap_time")
    assert tap is None or tap >= TAP_MIN_TIME


@pytest.mark.parametrize("concept", ALL_CONCEPTS)
def test_hardest_layout_is_tighter_than_intro(concept):
    # La difficulté passe par la disposition : la dernière difficulté laisse
    # une part de lancers gagnants plus faible que l'intro.
    assert _payload(concept, DIFFICULTIES[-1])["tolerance"] < _payload(concept, DIFFICULTIES[0])["tolerance"]


@pytest.mark.parametrize("concept,difficulty", CASES)
def test_shipped_json_matches_generator(concept, difficulty):
    # Les JSON commités doivent être exactement la sortie du générateur
    # courant (sinon : relancer `python3 cli.py generate-all`).
    path = os.path.join(LEVELS_DIR, f"quantique_{concept}_{difficulty}.json")
    with open(path, encoding="utf-8") as f:
        shipped = json.load(f)
    assert shipped["schema_version"] == SCHEMA_VERSION
    assert shipped == _payload(concept, difficulty)


def test_no_stale_level_files():
    expected = {f"quantique_{c}_{d}.json" for c, d in CASES}
    assert {os.path.basename(p) for p in glob.glob(os.path.join(LEVELS_DIR, "*.json"))} == expected
