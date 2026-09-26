"""Default locations in the repository (all overridable from the CLI)."""
from pathlib import Path

BUILDER_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BUILDER_DIR.parent

# The shipped pack: the contract between the builder and the app.
CONTENT_DIR = REPO_DIR / "content"
LEVELS_DIR = CONTENT_DIR / "levels" / "quantique"
CODEX_DIR = CONTENT_DIR / "codex"

# Dev-only outputs.
META_DIR = BUILDER_DIR / "meta"
GOLDEN_DIR = BUILDER_DIR / "tests" / "golden"
REPORTS_DIR = BUILDER_DIR / "reports"
