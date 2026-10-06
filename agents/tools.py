"""Deterministic SATRA tools -- the ONLY source of analytical numbers.

The language model may never compute a statistic. It calls these functions and
receives structured JSON, which it may summarise but not alter. This is what
makes SATRA's agent "evidence-grounded".

Tools operate on either (a) a live analysis run stored on disk, or (b) the
in-process demo pipeline. Both return the same structured shapes.
"""
from __future__ import annotations

from typing import Any

from geospatial.connectivity import analyze as connectivity
from geospatial.flood_mapping import change_detection
from geospatial.infrastructure import intersect as infra


def _run_or_demo(run_id: str | None) -> dict[str, Any]:
    if run_id and run_id != "demo":
        try:
            from app.core.store import get_run

            run = get_run(run_id)
            if run and run.get("status") == "completed":
                return run
        except Exception:
            # `app` package not importable in this context (e.g. plain script);
            # fall through to the in-process demo pipeline.
            pass
    # Fall back to computing the demo pipeline in-process.
    hazard = change_detection.detect_flood_from_demo()
    return {
        "run_id": run_id or "demo",
        "status": "completed",
        "flood": hazard,
        "infrastructure": infra.analyze_infrastructure(hazard),
        "connectivity": connectivity.analyze_connectivity(hazard),
        "satellite": {"source": "demo", "observations": []},
    }


def get_flood_statistics(run_id: str | None = None) -> dict[str, Any]:
    run = _run_or_demo(run_id)
    flood = run["flood"]
    return {
        "run_id": run["run_id"],
        "source": flood.get("meta", {}).get("label", ""),
        "high_confidence_polygons": len(flood["high_confidence"]["features"]),
        "moderate_confidence_polygons": len(flood["moderate_confidence"]["features"]),
        "uncertain_change_polygons": len(flood["uncertain_change"]["features"]),
        "observation_dates": run.get("satellite", {}).get("observation_dates", []),
    }


def get_affected_buildings(run_id: str | None = None) -> dict[str, Any]:
    run = _run_or_demo(run_id)
    summary = run["infrastructure"]["summary"]["buildings"]
    exposed = (
        summary.get("potentially_exposed", 0)
        + summary.get("high_priority_inspection", 0)
    )
    return {
        "run_id": run["run_id"],
        "counts_by_class": summary,
        "potentially_exposed_or_higher": exposed,
    }


def get_affected_roads(run_id: str | None = None) -> dict[str, Any]:
    run = _run_or_demo(run_id)
    summary = run["infrastructure"]["summary"]["roads"]
    affected = (
        summary.get("potentially_exposed", 0)
        + summary.get("high_priority_inspection", 0)
    )
    blocked = [e for e in run["connectivity"]["road_edges"] if e["status"] == "blocked"]
    return {
        "run_id": run["run_id"],
        "counts_by_class": summary,
        "affected_road_segments": affected,
        "blocked_edge_ids": [e["id"] for e in blocked],
    }


def get_disconnected_settlements(run_id: str | None = None) -> dict[str, Any]:
    run = _run_or_demo(run_id)
    conn = run["connectivity"]
    isolated = [
        s
        for s in conn["settlements"]
        if s["status"] in ("no_modelled_connection", "uncertain")
    ]
    return {
        "run_id": run["run_id"],
        "disconnected_count": len(isolated),
        "settlements": isolated,
    }


def get_nearest_alternative_hospital(settlement_id: str, run_id: str | None = None) -> dict[str, Any]:
    run = _run_or_demo(run_id)
    for s in run["connectivity"]["settlements"]:
        if s["settlement_id"] == settlement_id or s["name"] == settlement_id:
            return {
                "settlement": s["name"],
                "nearest_hospital": s["nearest_hospital"],
                "distance_km": s["distance_km"],
                "alternative_route": s["alternative_route"],
                "status": s["status"],
                "confidence": s["confidence"],
            }
    return {"error": f"settlement '{settlement_id}' not found"}


def generate_situation_report(run_id: str | None = None, language: str = "en") -> dict[str, Any]:
    run = _run_or_demo(run_id)
    flood = get_flood_statistics(run["run_id"])
    build = get_affected_buildings(run["run_id"])
    roads = get_affected_roads(run["run_id"])
    disc = get_disconnected_settlements(run["run_id"])

    names = ", ".join(s["name"] for s in disc["settlements"]) or "none identified"
    if language == "ne":
        body = _report_ne(run, flood, build, roads, disc, names)
    else:
        body = _report_en(run, flood, build, roads, disc, names)

    return {
        "run_id": run["run_id"],
        "language": language,
        "body_md": body,
        "numbers": {
            "buildings_potentially_exposed": build["potentially_exposed_or_higher"],
            "road_segments_affected": roads["affected_road_segments"],
            "settlements_disconnected": disc["disconnected_count"],
            "flood_polygons": flood["high_confidence_polygons"]
            + flood["moderate_confidence_polygons"],
        },
        "sources": ["Sentinel-1 (demo)", "historical OSM (demo)", "Copernicus DEM (demo)"],
        "limitations": (
            "Exposure and connectivity are modelled assessments, not confirmed "
            "damage. Optically/structurally unverified."
        ),
    }


def _report_en(run, flood, build, roads, disc, names) -> str:
    return f"""# SATRA — Emergency Situation Report

> DEMO OUTPUT — synthetic demonstration data, not a real disaster assessment.

**Event:** {run.get('aoi', {}).get('name', 'Selected AOI')} flood case study
**Disaster date:** {run.get('event_date', 'configured')}
**Run:** {run['run_id']}

## Verified findings (from geospatial tools)
- Detected flood polygons: **{flood['high_confidence_polygons'] + flood['moderate_confidence_polygons']}**
- Uncertain-change zones (NOT confirmed debris): **{flood['uncertain_change_polygons']}**
- Buildings potentially exposed: **{build['potentially_exposed_or_higher']}**
- Road segments affected/blocked: **{roads['affected_road_segments']}**
- Settlements with no modelled hospital route: **{disc['disconnected_count']}**

## Settlements requiring verification
{names}

## Interpretation
Each "disconnected" settlement means *no usable modelled road route* to a
hospital was found under the stated assumptions. This is not proof of physical
inaccessibility and is not a claim about individual people.

## Data quality & limitations
{run.get('limitations', 'Exposure and connectivity are modelled assessments.')}
"""


def _report_ne(run, flood, build, roads, disc, names) -> str:
    return f"""# SATRA — आपतकालीन स्थिति प्रतिवेदन

> डेमो नतिजा — यो वास्तविक विपद् मूल्याङ्कन होइन।

**घटना:** {run.get('aoi', {}).get('name', 'चयनित क्षेत्र')} बाढी केस स्टडी
**विपद् मिति:** {run.get('event_date', 'निर्धारित')}
**रन:** {run['run_id']}

## प्रमाणित तथ्याङ्क (जियोस्पेशियल टुलबाट)
- पहिचान भएको बाढी क्षेत्र: **{flood['high_confidence_polygons'] + flood['moderate_confidence_polygons']}**
- अनिश्चित परिवर्तन क्षेत्र (पुष्टि भएको भग्नावशेष होइन): **{flood['uncertain_change_polygons']}**
- सम्भावित प्रभावित भवन: **{build['potentially_exposed_or_higher']}**
- प्रभावित/अवरुद्ध सडक खण्ड: **{roads['affected_road_segments']}**
- अस्पताल पुग्ने मोडेल गरिएको बाटो नभएका बस्ती: **{disc['disconnected_count']}**

## पुनरावलोकन आवश्यक बस्तीहरू
{names}

## व्याख्या
"सम्पर्कविहीन" भन्नाले निर्धारित मान्यताअनुसार अस्पताल पुग्ने कुनै प्रयोगयोग्य
मोडेल गरिएको बाटो फेला नपरेको हो — यो भौतिक रूपमा असम्भव पुग्ने प्रमाण होइन।

## सीमितता
{run.get('limitations', 'जोखिम र सम्पर्क मोडेल गरिएका मूल्याङ्कन हुन्।')}
"""


# Registry so the agent layer can expose an allow-list of safe tools.
TOOL_REGISTRY = {
    "get_flood_statistics": get_flood_statistics,
    "get_affected_buildings": get_affected_buildings,
    "get_affected_roads": get_affected_roads,
    "get_disconnected_settlements": get_disconnected_settlements,
    "get_nearest_alternative_hospital": get_nearest_alternative_hospital,
    "generate_situation_report": generate_situation_report,
}
