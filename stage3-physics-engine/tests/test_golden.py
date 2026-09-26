"""Les trajectoires golden (contrat Python ⇄ Kotlin, cf. engine/golden.py)
doivent être celles du moteur courant : sinon le test JUnit du runtime
Android validerait une physique périmée. Régénérer : `python3 cli.py golden`."""
import json
import os

import pytest

from engine.export import read_level
from engine.golden import GOLDEN_LEVELS, golden_for

HERE = os.path.dirname(__file__)
LEVELS_DIR = os.path.join(HERE, "..", "levels")
GOLDEN_DIR = os.path.join(HERE, "golden")


@pytest.mark.parametrize("name", GOLDEN_LEVELS)
def test_golden_up_to_date(name):
    with open(os.path.join(GOLDEN_DIR, f"{name}.golden.json"), encoding="utf-8") as f:
        committed = json.load(f)
    fresh = json.loads(json.dumps(golden_for(read_level(os.path.join(LEVELS_DIR, f"{name}.json")))))
    assert committed == fresh, f"golden périmé : lancer `python3 cli.py golden` ({name})"


@pytest.mark.parametrize("name", GOLDEN_LEVELS)
def test_golden_hint_wins_with_all_photons(name):
    with open(os.path.join(GOLDEN_DIR, f"{name}.golden.json"), encoding="utf-8") as f:
        hint = json.load(f)["cases"][0]
    assert hint["name"] == "hint" and hint["success"] and len(hint["photons"]) == 3
