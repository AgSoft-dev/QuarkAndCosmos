"""The golden trajectories (Python ⇄ Kotlin contract, see export/golden.py)
must be the current engine's: otherwise the Android runtime's JUnit test
would validate stale physics. Regenerate: `python3 -m quarkcosmos_levels golden`."""
import json
import os

import pytest

from quarkcosmos_levels import paths
from quarkcosmos_levels.export.golden import GOLDEN_LEVELS, golden_for
from quarkcosmos_levels.export.levels import read_level

LEVELS_DIR = str(paths.LEVELS_DIR)
GOLDEN_DIR = str(paths.GOLDEN_DIR)


@pytest.mark.parametrize("name", GOLDEN_LEVELS)
def test_golden_up_to_date(name):
    with open(os.path.join(GOLDEN_DIR, f"{name}.golden.json"), encoding="utf-8") as f:
        committed = json.load(f)
    fresh = json.loads(json.dumps(golden_for(read_level(os.path.join(LEVELS_DIR, f"{name}.json")))))
    assert committed == fresh, f"stale golden: run `python3 -m quarkcosmos_levels golden` ({name})"


@pytest.mark.parametrize("name", GOLDEN_LEVELS)
def test_golden_hint_wins_with_all_photons(name):
    with open(os.path.join(GOLDEN_DIR, f"{name}.golden.json"), encoding="utf-8") as f:
        hint = json.load(f)["cases"][0]
    assert hint["name"] == "hint" and hint["success"] and len(hint["photons"]) == 3
