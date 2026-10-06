"""Health + analysis + data endpoints for SATRA."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core import store
from app.core.config import settings
from app.pipeline import run_analysis
from app.schemas.models import AnalysisCreated, AnalysisRequest

router = APIRouter()


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "SATRA",
        "copernicus_configured": settings.has_copernicus,
        "llm_configured": settings.has_llm,
        "demo_mode_default": True,
    }


@router.get("/config")
def config():
    return {
        "default_bbox": settings.default_bbox,
        "default_disaster_date": settings.default_disaster_date,
    }


@router.post("/analysis", response_model=AnalysisCreated, status_code=202)
def create_analysis(req: AnalysisRequest):
    run_id = run_analysis(req.model_dump())
    return AnalysisCreated(
        run_id=run_id,
        status="completed",
        message="Analysis complete (demo pipeline). Layers available via /api/analysis/{id}.",
    )


@router.get("/analysis")
def list_analysis():
    return {"runs": store.list_runs()}


@router.get("/analysis/{run_id}")
def get_analysis(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found")
    return {
        "run_id": run["run_id"],
        "status": run["status"],
        "aoi": run["aoi"],
        "event_date": run.get("event_date"),
        "demo_mode": run.get("demo_mode"),
        "satellite": run.get("satellite"),
        "summary": {
            "buildings": run["infrastructure"]["summary"]["buildings"],
            "roads": run["infrastructure"]["summary"]["roads"],
            "bridges": run["infrastructure"]["summary"]["bridges"],
            "hospitals": run["infrastructure"]["summary"]["hospitals"],
            "disconnected_settlements": run["connectivity"]["disconnected_count"],
            "total_settlements": run["connectivity"]["total_settlements"],
        },
        "provenance": run.get("provenance"),
    }


@router.get("/flood-zones/{run_id}")
def flood_zones(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found")
    return run["flood"]


@router.get("/infrastructure/{run_id}")
def infrastructure(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found")
    return run["infrastructure"]


@router.get("/connectivity/{run_id}")
def conn(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found")
    return run["connectivity"]
