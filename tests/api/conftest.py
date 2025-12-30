"""Conftest for API tests to ensure proper imports."""

import sys
from pathlib import Path

# Add src directory to path if not already there
src_dir = Path(__file__).parent.parent.parent / "src"
src_path = str(src_dir.resolve())

if src_path not in sys.path:
    sys.path.insert(0, src_path)
