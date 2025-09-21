"""Test configuration helpers."""

import sys
from pathlib import Path


def _ensure_project_root_on_path() -> None:
    """Add the repository root to ``sys.path`` for module resolution."""

    project_root = Path(__file__).resolve().parent.parent
    root_as_str = str(project_root)
    if root_as_str not in sys.path:
        sys.path.insert(0, root_as_str)


_ensure_project_root_on_path()
