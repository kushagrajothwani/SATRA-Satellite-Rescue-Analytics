"""Pytest configuration: make the project importable from the repo root.

Adds the repo root (for `geospatial`, `agents`) and the `backend/` directory
(for the `app` package) to sys.path.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"

for p in (str(ROOT), str(BACKEND)):
    if p not in sys.path:
        sys.path.insert(0, p)
