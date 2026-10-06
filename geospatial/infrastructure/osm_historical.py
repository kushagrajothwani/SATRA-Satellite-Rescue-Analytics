"""Historical OpenStreetMap extraction via the ohsome API.

We fetch infrastructure as it existed BEFORE the disaster (the baseline), never
post-event edits. Example request (roads):

    POST https://api.ohsome.org/v1/elements/geometry
    data:
      bboxes=85.2,28.0,85.6,28.4
      time=2026-07-27T00:00:00Z
      filter=highway=* and type:way
      properties=tags,metadata

Requires `requests`. If the network is unavailable, `demo_layers()` returns the
labelled synthetic baseline so the pipeline still runs.
"""
from __future__ import annotations

from typing import Any

from geospatial import demo_data

OHSOME_URL = "https://api.ohsome.org/v1/elements/geometry"
PRE_EVENT_TIME = "2026-07-27T00:00:00Z"

FILTERS = {
    "buildings": "building=* and type:polygon",
    "roads": "highway=* and type:way",
    "bridges": "bridge=* and type:way",
    "hospitals": "amenity=hospital",
    "settlements": "place=*",
}


def fetch_layer(bbox: tuple[float, float, float, float], layer: str, time: str = PRE_EVENT_TIME):
    """Fetch one OSM layer as GeoJSON. Raises if `requests`/network unavailable."""
    import requests

    data = {
        "bboxes": ",".join(str(v) for v in bbox),
        "time": time,
        "filter": FILTERS[layer],
        "properties": "tags,metadata",
    }
    r = requests.post(OHSOME_URL, data=data, timeout=90)
    r.raise_for_status()
    return r.json()


def demo_layers() -> dict[str, Any]:
    return {
        "meta": demo_data.demo_metadata(),
        "roads": {"features": demo_data.ROADS},
        "buildings": {"features": demo_data.BUILDINGS},
        "bridges": {"features": demo_data.BRIDGES},
        "hospitals": {"features": demo_data.HOSPITALS},
        "settlements": {"features": demo_data.SETTLEMENTS},
    }
