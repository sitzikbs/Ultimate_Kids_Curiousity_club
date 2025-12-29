"""Root conftest.py to setup import paths before test collection."""

import sys
from pathlib import Path

# Add src directory to Python path BEFORE pytest imports test modules
# This must happen at import time, not in a hook
project_root = Path(__file__).parent
src_dir = project_root / "src"

print(f"[CONFTEST] Adding {src_dir} to sys.path")
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
    print(f"[CONFTEST] Path added successfully")
else:
    print(f"[CONFTEST] Path already in sys.path")

print(f"[CONFTEST] Current sys.path: {sys.path[:3]}")
