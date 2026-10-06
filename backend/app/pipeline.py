"""End-to-end analysis pipeline.

Runs the full SATRA flow for a request and stores the result as a run document.
With `demo_mode=True` (the default) it uses the labelled synthetic dataset so
everything runs offline. With real credentials and downloaded imagery, the
satellite/geospatial modules would replace the demo layers at the same seams.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core import store
from geospatial.connectivity import analyze as connectivity
from geospatial.flood_mapping import change_detection
from geospatial.infrastructure import intersect as infra


def run_analysis(request: dict[str, Any]) -> str:
    """Execute an analysis and return the run_id."""
    run_id = store.new_run_id()
    hazard = change_detection.detect_flood_from_demo()
    infrastructure = infra.analyze_infrastructure(hazard)
    conn = connectivity.analyze_connectivity(hazard)

    infrastructure["road_edges"] = conn["road_edges"]

    run = {
        "run_id": run_id,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "aoi": request.get("aoi", {}),
        "event_date": request.get("disaster_date"),
        "pre_window": request.get("pre_window"),
        "post_window": request.get("post_window"),
        "sensors": request.get("sensors", ["S1"]),
        "demo_mode": request.get("demo_mode", True),
        "satellite": _satellite_block(hazard, request),
        "flood": hazard,
        "infrastructure": infrastructure,
        "connectivity": conn,
        "provenance": {
            "model_version": "unet-demo-0.1",
            "processing_date": datetime.now(timezone.utc).isoformat(),
            "inputs": ["geospatial.demo_data (synthetic)"],
            "validation_only": [],
        },
    }
    store.save_run(run)
    return run_id


def _satellite_block(hazard: dict, request: dict) -> dict[str, Any]:
    return {
        "source": hazard["meta"]["source"],
        "label": hazard["meta"]["label"],
        "sensors": request.get("sensors", ["S1"]),
        "observation_dates": list(request.get("post_window", [])),
        "orbit_note": "Same relative orbit ~12 days apart recommended for real SAR change detection.",
        "observations": [],
    }
