"""Infrastructure exposure analysis.

Overlays pre-event infrastructure (buildings, roads, bridges, hospitals) on the
detected hazard layer and assigns each feature an *exposure* class:

    high_priority_inspection  - inside the high-confidence flood core
    potentially_exposed       - intersects the wider detected flood extent
    uncertain                 - only intersects an uncertain-change/anomaly zone
    outside                   - no intersection with any detected hazard

This is an EXPOSURE assessment, never a claim of confirmed structural damage.
"""
from __future__ import annotations

from typing import Any

from geospatial import demo_data, geometry
from geospatial.flood_mapping import change_detection


def _classify_hit(rings_hit: dict[str, bool]) -> tuple[str, str]:
    if rings_hit.get("core"):
        return "high_priority_inspection", "high"
    if rings_hit.get("extent"):
        return "potentially_exposed", "medium"
    if rings_hit.get("anomaly"):
        return "uncertain", "low"
    return "outside", "low"


def analyze_infrastructure(hazard: dict | None = None) -> dict:
    """Return GeoJSON layers + summary for each infrastructure class."""
    hazard = hazard or change_detection.detect_flood_from_demo()
    core = [hazard["hazard_rings"][1]]
    extent = [hazard["hazard_rings"][0]]
    anomaly = demo_data.ANOMALY_RINGS

    def hit_flags(pt: tuple[float, float]) -> dict[str, bool]:
        return {
            "core": geometry.point_intersects_any(pt, core),
            "extent": geometry.point_intersects_any(pt, extent),
            "anomaly": geometry.point_intersects_any(pt, anomaly),
        }

    def line_flags(coords):
        return {
            "core": geometry.line_intersects_any(coords, core),
            "extent": geometry.line_intersects_any(coords, extent),
            "anomaly": geometry.line_intersects_any(coords, anomaly),
        }

    summary: dict[str, dict[str, int]] = {}

    # --- Buildings ---
    b_features = []
    b_counts: dict[str, int] = {}
    for b in demo_data.BUILDINGS:
        cls, conf = _classify_hit(hit_flags((b["lon"], b["lat"])))
        b_counts[cls] = b_counts.get(cls, 0) + 1
        b_features.append(
            {
                "type": "Feature",
                "properties": {"id": b["id"], "settlement": b["settlement"],
                               "exposure": cls, "confidence": conf},
                "geometry": {"type": "Point", "coordinates": [b["lon"], b["lat"]]},
            }
        )
    summary["buildings"] = b_counts

    # --- Roads ---
    r_features = []
    r_counts: dict[str, int] = {}
    for r in demo_data.ROADS:
        cls, conf = _classify_hit(line_flags(r["coords"]))
        r_counts[cls] = r_counts.get(cls, 0) + 1
        r_features.append(
            {
                "type": "Feature",
                "properties": {"id": r["id"], "highway": r["highway"],
                               "from": r["from"], "to": r["to"],
                               "exposure": cls, "confidence": conf},
                "geometry": {"type": "LineString", "coordinates": [list(c) for c in r["coords"]]},
            }
        )
    summary["roads"] = r_counts

    # --- Bridges ---
    br_features = []
    br_counts: dict[str, int] = {}
    for br in demo_data.BRIDGES:
        cls, conf = _classify_hit(hit_flags((br["lon"], br["lat"])))
        br_counts[cls] = br_counts.get(cls, 0) + 1
        br_features.append(
            {
                "type": "Feature",
                "properties": {"id": br["id"], "name": br["name"],
                               "exposure": cls, "confidence": conf},
                "geometry": {"type": "Point", "coordinates": [br["lon"], br["lat"]]},
            }
        )
    summary["bridges"] = br_counts

    # --- Hospitals ---
    h_features = []
    h_counts: dict[str, int] = {}
    for h in demo_data.HOSPITALS:
        cls, conf = _classify_hit(hit_flags((h["lon"], h["lat"])))
        h_counts[cls] = h_counts.get(cls, 0) + 1
        h_features.append(
            {
                "type": "Feature",
                "properties": {"id": h["id"], "name": h["name"],
                               "exposure": cls, "confidence": conf},
                "geometry": {"type": "Point", "coordinates": [h["lon"], h["lat"]]},
            }
        )
    summary["hospitals"] = h_counts

    def fc(features):
        return {"type": "FeatureCollection", "features": features}

    return {
        "meta": demo_data.demo_metadata(),
        "buildings": fc(b_features),
        "roads": fc(r_features),
        "bridges": fc(br_features),
        "hospitals": fc(h_features),
        "summary": summary,
    }
