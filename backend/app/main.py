"""SATRA FastAPI application.

Run from the repository root so the sibling `geospatial` and `agents` packages
are importable:

    cd backend
    .\\venv\\Scripts\\Activate.ps1
    uvicorn app.main:app --reload
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repo root (parent of backend/) is importable for `geospatial`/`agents`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from app.api import agent_routes, routes  # noqa: E402

app = FastAPI(title="SATRA API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api", tags=["core"])
app.include_router(agent_routes.router, prefix="/api/agent", tags=["agent"])


@app.get("/api/sample-flood")
def sample_flood():
    """Backwards-compatible labelled demo layer.

    Prefer POST /api/analysis + GET /api/flood-zones/{id} for real runs.
    """
    from geospatial.flood_mapping import change_detection

    geo = change_detection.detect_flood_from_demo()
    return geo["moderate_confidence"]
