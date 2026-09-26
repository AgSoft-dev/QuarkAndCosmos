"""Contract of the Quantum world levels (see the gameplay-mechanics skill)."""
import functools
import glob
import json
import os

import pytest

from quarkcosmos_levels import paths
from quarkcosmos_levels.concepts.generator import ALL_CONCEPTS, DIFFICULTIES, make_level
from quarkcosmos_levels.core.simulate import TAP_MIN_TIME
from quarkcosmos_levels.export.codex import missing_codex_lines
from quarkcosmos_levels.export.levels import (DEV_ONLY_KEYS, SCHEMA_VERSION, build_export_payloads,
                                              meta_path_for, read_level)
from quarkcosmos_levels.solver.stars import PHOTONS_PER_LEVEL

LEVELS_DIR = str(paths.LEVELS_DIR)
META_DIR = str(paths.META_DIR)
# Minimum share of the parameter grid that must reach the target: below it,
# the level is "solvable" on paper but unplayable by finger.
MIN_TOLERANCE = 0.05
CASES = [(c, d) for c in ALL_CONCEPTS for d in DIFFICULTIES]


@functools.lru_cache(maxsize=None)
def _generated_json(concept, difficulty):
    # make_level (Photon placement, expensive) only once per level
    return json.dumps(make_level(concept, difficulty))


def _generated(concept, difficulty):
    return json.loads(_generated_json(concept, difficulty))


@functools.lru_cache(maxsize=None)
def _exported(concept, difficulty):
    # validation only once per level for the whole suite;
    # (shipped level, dev meta) as they would be read back from disk
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
    # Every successful launch must use the declared mechanic (must_contact):
    # no level can be solved by bypassing what it is meant to teach.
    shipped, meta = _exported(concept, difficulty)
    assert meta["solvable"]
    # (incertitude has no mechanic object: the mechanic is the dial)
    if any(o["type"] != "wall" for o in shipped["obstacles"]):
        assert meta["must_contact"], "the level declares the mechanic to use"
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
    # the hint shipped to the game is exactly the reference solution
    assert _shipped(concept, difficulty)["hint"] == {"params": params}


@pytest.mark.parametrize("concept", ALL_CONCEPTS)
def test_hardest_layout_is_tighter_than_intro(concept):
    # Difficulty comes from the layout: the last difficulty leaves a smaller
    # share of winning launches than the intro.
    assert _meta(concept, DIFFICULTIES[-1])["tolerance"] < _meta(concept, DIFFICULTIES[0])["tolerance"]


@pytest.mark.parametrize("concept,difficulty", CASES)
def test_shipped_json_matches_generator(concept, difficulty):
    # The committed JSON (shipped level AND dev meta) must be exactly the
    # current generator's output (otherwise: run
    # `python3 -m quarkcosmos_levels generate-all`).
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
    # `validate <level>.json` reads must_contact back from the meta: the level
    # read back must give the validator the same input as the generator.
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


def test_meta_lives_in_the_builder():
    path = os.path.join(LEVELS_DIR, "quantique_tunnel_1.json")
    assert os.path.samefile(os.path.dirname(meta_path_for(path)), META_DIR)


def test_shipped_levels_carry_no_player_text():
    # Player-facing text is localised in content/codex/<lang>/ (FR + EN).
    for path in glob.glob(os.path.join(LEVELS_DIR, "*.json")):
        with open(path, encoding="utf-8") as f:
            assert "codex_text" not in json.load(f)


def test_every_concept_has_a_codex_line_in_every_language():
    assert missing_codex_lines(ALL_CONCEPTS) == []
