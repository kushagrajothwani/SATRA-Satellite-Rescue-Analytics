"""SAR change detection -> flood extent.

Real pipeline (documented, activated with rasterio + downloaded S1 products):
    1. Read co-registered pre/post GRD VV (+VH) rasters.
    2. Convert to dB; compute change = post - pre.
    3. Flood candidate where post backscatter drops sharply vs pre
       (change < threshold) AND pre was not already water.
    4. Exclude permanent water using a pre-event water mask.
    5. Vectorise the binary mask to polygons.

This module exposes `detect_flood_arrays(pre, post)` which works on numpy
arrays so it can be unit-tested offline, plus `detect_flood_from_demo()` which
returns the labelled demo extent so the end-to-end pipeline runs without heavy
dependencies or network access.
"""
from __future__ import annotations

from typing import Any

from geospatial import demo_data


def _to_db(values: list[float], eps: float = 1e-6) -> list[float]:
    import math

    return [10.0 * math.log10(max(v, eps)) for v in values]


def detect_flood_arrays(
    pre_vv: list[float],
    post_vv: list[float],
    threshold_db: float = -3.0,
    pre_water_mask: list[bool] | None = None,
) -> list[bool]:
    """Return a boolean flood mask (True = flood) for 1-D sample arrays.

    A pixel is flagged as flood when the post-event backscatter is at least
    `threshold_db` lower than pre-event (a classic SAR open-water signature:
    smooth water reflects radar away from the sensor) and it was not already
    water before the event.
    """
    pre_db = _to_db(pre_vv)
    post_db = _to_db(post_vv)
    mask: list[bool] = []
    for i, (a, b) in enumerate(zip(pre_db, post_db)):
        was_water = bool(pre_water_mask[i]) if pre_water_mask else False
        mask.append((b - a) <= threshold_db and not was_water)
    return mask


def rings_to_geojson(rings: list[list[tuple[float, float]]], props: dict[str, Any]) -> dict:
    features = []
    for ring in rings:
        closed = list(ring)
        if closed[0] != closed[-1]:
            closed.append(closed[0])
        features.append(
            {
                "type": "Feature",
                "properties": dict(props),
                "geometry": {"type": "Polygon", "coordinates": [closed]},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def detect_flood_from_demo() -> dict:
    """Labelled demo flood extent incl. a confident core and uncertain class."""
    conf_geo = rings_to_geojson(
        [demo_data.FLOOD_CORE_RING],
        {"class": 1, "label": "flood (high confidence)", "confidence": "high"},
    )
    uncertain_geo = rings_to_geojson(
        [demo_data.FLOOD_RING],
        {"class": 1, "label": "flood (moderate confidence)", "confidence": "medium"},
    )
    anomaly_geo = rings_to_geojson(
        demo_data.ANOMALY_RINGS,
        {"class": 2, "label": "uncertain change (NOT confirmed debris)", "confidence": "low"},
    )
    return {
        "meta": demo_data.demo_metadata(),
        "high_confidence": conf_geo,
        "moderate_confidence": uncertain_geo,
        "uncertain_change": anomaly_geo,
        "hazard_rings": [demo_data.FLOOD_RING, demo_data.FLOOD_CORE_RING],
    }
