"""SAR preprocessing helpers (real pipeline).

Documented, dependency-gated steps for turning Sentinel-1 GRD products into
analysis-ready rasters:

    1. Read VV/VH bands from the SAFE/GeoTIFF.
    2. Radiometric calibration to sigma0 (or use already-calibrated GRD).
    3. Speckle filtering (Refined Lee / Lee).
    4. Terrain correction (range-Doppler) to WGS84.
    5. Convert to dB, clip to per-channel percentiles.
    6. Co-register pre/post and tile to fixed patches.

Fully automated SNAP processing is heavy; for the hackathon the practical path
is either (a) Sentinel Hub / Copernicus Processing API for calibrated+terrain-
corrected imagery, or (b) pre-processed GeoTIFFs loaded here. This module marks
the seam where those outputs enter the pipeline.
"""
from __future__ import annotations

from typing import Any


def to_db(values, eps: float = 1e-6):
    import math

    return [10.0 * math.log10(max(float(v), eps)) for v in values]


def percentile_stretch(values, lo: float = 2.0, hi: float = 98.0):
    import numpy as np

    arr = np.asarray(values, dtype="float32")
    a, b = np.percentile(arr, lo), np.percentile(arr, hi)
    if b <= a:
        return np.zeros_like(arr)
    return np.clip((arr - a) / (b - a), 0, 1)


def describe() -> dict[str, Any]:
    return {
        "steps": [
            "read VV/VH",
            "radiometric calibration",
            "speckle filter",
            "terrain correction",
            "dB + percentile stretch",
            "co-register + tile",
        ],
        "note": "Use Copernicus/Sentinel Hub processed GeoTIFFs, or SNAP for full processing.",
    }
