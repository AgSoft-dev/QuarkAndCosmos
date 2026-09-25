"""Contrat des niveaux de la beta (monde Quantique, cf. CLAUDE.md)."""
import json
import os

import pytest

from engine.export import SCHEMA_VERSION, build_export_payload
from engine.generator import ALL_CONCEPTS, make_level
from engine.simulate import TAP_MIN_TIME
from engine.validator import PHOTONS_PER_LEVEL, validate

LEVELS_DIR = os.path.join(os.path.dirname(__file__), "..", "levels")
# Part minimale de la grille de paramètres qui doit atteindre la cible : en
# dessous, le niveau est "solvable" sur le papier mais injouable au doigt.
MIN_TOLERANCE = 0.05


@pytest.fixture(scope="module", params=ALL_CONCEPTS)
def generated(request):
    level = make_level(request.param, 1)
    return level, validate(level)


def test_beta_has_seven_concepts():
    assert len(ALL_CONCEPTS) == 7


def test_level_is_solvable(generated):
    _, report = generated
    assert report["solvable"]


def test_three_photons_all_collectable(generated):
    level, report = generated
    assert len(level["photons"]) == PHOTONS_PER_LEVEL
    assert report["max_photons_reachable"] == PHOTONS_PER_LEVEL


def test_level_is_not_brittle(generated):
    _, report = generated
    assert report["tolerance"] >= MIN_TOLERANCE


def test_reference_solution_taps_in_flight(generated):
    _, report = generated
    tap = report["best_solution"]["params"].get("tap_time")
    assert tap is None or tap >= TAP_MIN_TIME


@pytest.mark.parametrize("concept", ALL_CONCEPTS)
def test_shipped_json_matches_generator(concept):
    # Les JSON commités doivent être exactement la sortie du générateur
    # courant (sinon : relancer `python3 cli.py generate-all`).
    path = os.path.join(LEVELS_DIR, f"quantique_{concept}_1.json")
    with open(path, encoding="utf-8") as f:
        shipped = json.load(f)
    assert shipped["schema_version"] == SCHEMA_VERSION
    assert shipped == json.loads(json.dumps(build_export_payload(make_level(concept, 1))))
