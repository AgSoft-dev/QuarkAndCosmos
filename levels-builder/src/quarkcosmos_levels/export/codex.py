"""
Player-facing Codex lines, one file per language:
`content/codex/<lang>/<scale>.json` = {"lines": {<concept id>: <text>}}.
The game picks the file matching the device language (English fallback).
"""
import json
import os

from .. import paths

LANGUAGES = ("en", "fr")


def load_codex(lang: str, scale: str = "quantique", codex_dir=None) -> dict:
    path = os.path.join(codex_dir or paths.CODEX_DIR, lang, f"{scale}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)["lines"]


def missing_codex_lines(concepts, scale: str = "quantique", codex_dir=None) -> list:
    """(lang, concept) pairs with no (or an empty) Codex line."""
    missing = []
    for lang in LANGUAGES:
        lines = load_codex(lang, scale, codex_dir)
        missing += [(lang, c) for c in concepts if not lines.get(c, "").strip()]
    return missing
