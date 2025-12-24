"""Test suite for the Ultimate Kids Curiosity Club."""

import sys
from pathlib import Path

import pytest

# Ensure src is in the path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(project_root) not in sys.path and src_path.exists():
    sys.path.insert(0, str(project_root))


@pytest.mark.unit
def test_basic_import():
    """Test that the main package can be imported."""
    # Import inside the test function after path is set
    import src  # noqa: E402

    assert src.__version__ == "0.1.0"
