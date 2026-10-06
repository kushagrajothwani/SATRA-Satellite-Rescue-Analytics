"""Raster flood mask -> GeoJSON polygons (real pipeline).

Uses rasterio.features.shapes to polygonise a classified mask, simplifies
geometry to keep files small, and writes GeoJSON. Dependency-gated on rasterio
and shapely.
"""
from __future__ import annotations

import json
from pathlib import Path


def mask_to_geojson(mask_path: str, out_path: str, class_names: dict[int, str] | None = None):
    import rasterio
    from rasterio.features import shapes
    from shapely.geometry import shape, mapping

    class_names = class_names or {1: "flood", 2: "uncertain_change"}
    feats = []
    with rasterio.open(mask_path) as src:
        band = src.read(1)
        for geom, value in shapes(band, transform=src.transform):
            value = int(value)
            if value == 0:
                continue
            g = shape(geom).simplify(0.00005, preserve_topology=True)
            feats.append(
                {
                    "type": "Feature",
                    "properties": {
                        "class": value,
                        "label": class_names.get(value, f"class_{value}"),
                    },
                    "geometry": mapping(g),
                }
            )

    fc = {"type": "FeatureCollection", "features": feats}
    Path(out_path).write_text(json.dumps(fc), encoding="utf-8")
    return out_path
