"""Contrat des niveaux du monde Quantique (cf. CLAUDE.md et gameplay-mechanics)."""
import functools
import glob
import json
import os

import pytest

from engine.export import DEV_ONLY_KEYS, SCHEMA_VERSION, build_export_payloads, meta_path_for, read_level
from engine.generator import ALL_CONCEPTS, DIFFICULTIES, make_level
from engine.simulate import TAP_MIN_TIME
from engine.stars import PHOTONS_PER_LEVEL

LEVELS_DIR = os.path.join(os.path.dirname(__file__), "..", "levels")
META_DIR = os.path.join(LEVELS_DIR, "meta")
# Part minimale de la grille de paramètres qui doit atteindre la cible : en
# dessous, le niveau est "solvable" sur le papier mais injouable au doigt.
MIN_TOLERANCE = 0.05
CASES = [(c, d) for c in ALL_CONCEPTS for d in DIFFICULTIES]


@functools.lru_cache(maxsize=None)
def _generated_json(concept, difficulty):
    # make_level (placement des Photons, coûteux) une seule fois par niveau
    return json.dumps(make_level(concept, difficulty))


def _generated(concept, difficulty):
    return json.loads(_generated_json(concept, difficulty))


@functools.lru_cache(maxsize=None)
def _exported(concept, difficulty):
    # validation une seule fois par niveau pour toute la suite ;
    # (niveau livré, méta dev) tels qu'ils seraient relus depuis le disque
    return json.loads(json.dumps(build_export_payloads(_generated(concept, difficulty))))


def _shipped(concept, difficulty):
    return _exported(concept, difficulty)[0]


def _meta(concept, difficulty):
    return _exported(concept, difficulty)[1]


def _level_path(concept, difficulty):
    return os.path.join(LEVELS_DIR, f"quantique_{concept}_{difficulty}.json")


def test_beta_has_seven_concepts():
    assert len(ALL_CONCEPTS) == 7


@pytest.mark.parametrize("concept,difficulty", CASES)
def test_level_is_solvable_without_bypass(concept, difficulty):
    # Chaque lancer réussi doit utiliser la mécanique déclarée (must_contact) :
    # aucun niveau ne se résout en contournant ce qu'il est censé enseigner.
    shipped, meta = _exported(concept, difficulty)
    assert meta["solvable"]
    # (incertitude n'a pas d'objet de mécanique : la mécanique est le dial)
    if any(o["type"] != "wall" for o in shipped["obstacles"]):
        assert meta["must_contact"], "le niveau déclare la mécanique à utiliser"
    assert meta["bypass_solutions"] == 0


@pytest.mark.parametrize("concept,difficulty", CASES)
def test_three_photons_all_collectable(concept, difficulty):
    assert len(_shipped(concept, difficulty)["photons"]) == PHOTONS_PER_LEVEL
    assert _meta(concept, difficulty)["max_photons_reachable"] == PHOTONS_PER_LEVEL


@pytest.mark.parametrize("concept,difficulty", CASES)
def test_level_is_not_brittle(concept, difficulty):
    assert _meta(concept, difficulty)["tolerance"] >= MIN_TOLERANCE


@pytest.mark.parametrize("concept,difficulty", CASES)
def test_reference_solution_taps_in_flight(concept, difficulty):
    params = _meta(concept, difficulty)["reference_solution"]["params"]
    taps = [v for k, v in params.items() if k.startswith("tap_time")]
    assert all(t >= TAP_MIN_TIME for t in taps)
    # l'indice livré au jeu est exactement la solution de référence
    assert _shipped(concept, difficulty)["hint"] == {"params": params}


@pytest.mark.parametrize("concept", ALL_CONCEPTS)
def test_hardest_layout_is_tighter_than_intro(concept):
    # La difficulté passe par la disposition : la dernière difficulté laisse
    # une part de lancers gagnants plus faible que l'intro.
    assert _meta(concept, DIFFICULTIES[-1])["tolerance"] < _meta(concept, DIFFICULTIES[0])["tolerance"]


@pytest.mark.parametrize("concept,difficulty", CASES)
def test_shipped_json_matches_generator(concept, difficulty):
    # Les JSON commités (niveau livré ET méta dev) doivent être exactement la
    # sortie du générateur courant (sinon : relancer `python3 cli.py generate-all`).
    path = _level_path(concept, difficulty)
    with open(path, encoding="utf-8") as f:
        shipped = json.load(f)
    with open(meta_path_for(path), encoding="utf-8") as f:
        meta = json.load(f)
    assert shipped["schema_version"] == meta["schema_version"] == SCHEMA_VERSION
    assert shipped == _shipped(concept, difficulty)
    assert meta == _meta(concept, difficulty)


@pytest.mark.parametrize("concept,difficulty", CASES)
def test_shipped_json_has_no_dev_fields(concept, difficulty):
    shipped = _shipped(concept, difficulty)
    for key in DEV_ONLY_KEYS + ("reference_solution", "tolerance", "star_profile", "bypass_solutions"):
        assert key not in shipped


@pytest.mark.parametrize("concept,difficulty", CASES)
def test_read_level_restores_validation_input(concept, difficulty):
    # `cli.py validate levels/<nom>.json` relit must_contact dans la méta : le
    # niveau relu doit redonner au validateur la même entrée que le générateur.
    level = read_level(_level_path(concept, difficulty))
    generated = _generated(concept, difficulty)
    for key, value in generated.items():
        assert level[key] == value, key
    assert level["must_contact"] == generated.get("must_contact", [])


def test_no_stale_level_files():
    expected = {f"quantique_{c}_{d}" for c, d in CASES}
    shipped = {os.path.basename(p)[:-len(".json")] for p in glob.glob(os.path.join(LEVELS_DIR, "*.json"))}
    meta = {os.path.basename(p)[:-len(".meta.json")] for p in glob.glob(os.path.join(META_DIR, "*.json"))}
    assert shipped == expected
    assert meta == expected
