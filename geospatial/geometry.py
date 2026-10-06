"""Dependency-free 2D geometry helpers.

SATRA's *production* path uses shapely / rasterio / geopandas (see the other
modules in this package). These helpers exist so the backend, connectivity
engine and demo pipeline can run end-to-end even before those heavy libraries
are installed. Treat lon/lat as planar coordinates -- adequate for small AOIs
and for the demo dataset; swap for shapely in production.

Reference: standard point-in-polygon ray casting and segment intersection.
"""
from __future__ import annotations

from typing import Sequence

Point = tuple[float, float]
Ring = Sequence[Point]

EPS = 1e-12


def bbox(ring: Ring) -> tuple[float, float, float, float]:
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def point_in_ring(pt: Point, ring: Ring) -> bool:
    """Ray-casting point-in-polygon test. `ring` may be open or closed."""
    x, y = pt
    inside = False
    n = len(ring)
    if n < 3:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y):
            x_cross = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_cross:
                inside = not inside
        j = i
    return inside


def _orient(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: Point, q: Point, b: Point) -> bool:
    return (
        min(a[0], b[0]) - EPS <= q[0] <= max(a[0], b[0]) + EPS
        and min(a[1], b[1]) - EPS <= q[1] <= max(a[1], b[1]) + EPS
    )


def segments_intersect(a: Point, b: Point, c: Point, d: Point) -> bool:
    d1 = _orient(c, d, a)
    d2 = _orient(c, d, b)
    d3 = _orient(a, b, c)
    d4 = _orient(a, b, d)

    if ((d1 > EPS and d2 < -EPS) or (d1 < -EPS and d2 > EPS)) and (
        (d3 > EPS and d4 < -EPS) or (d3 < -EPS and d4 > EPS)
    ):
        return True

    if abs(d1) <= EPS and _on_segment(c, a, d):
        return True
    if abs(d2) <= EPS and _on_segment(c, b, d):
        return True
    if abs(d3) <= EPS and _on_segment(a, c, b):
        return True
    if abs(d4) <= EPS and _on_segment(a, d, b):
        return True
    return False


def line_intersects_ring(coords: Sequence[Point], ring: Ring) -> bool:
    """True if a polyline touches/enters/ends inside a polygon ring."""
    if any(point_in_ring(p, ring) for p in coords):
        return True
    n = len(ring)
    for i in range(len(coords) - 1):
        a, b = coords[i], coords[i + 1]
        for j in range(n):
            c, d = ring[j], ring[(j + 1) % n]
            if segments_intersect(a, b, c, d):
                return True
    return False


def point_intersects_any(pt: Point, rings: Sequence[Ring]) -> bool:
    return any(point_in_ring(pt, r) for r in rings)


def line_intersects_any(coords: Sequence[Point], rings: Sequence[Ring]) -> bool:
    return any(line_intersects_ring(coords, r) for r in rings)


def shoelace_area_km2(ring: Ring, center_lat: float) -> float:
    """Approximate a small polygon's area in km^2 from lon/lat degrees."""
    if len(ring) < 3:
        return 0.0
    area_deg2 = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        area_deg2 += x1 * y2 - x2 * y1
    area_deg2 = abs(area_deg2) / 2.0
    import math

    km_per_deg_lat = 111.0
    km_per_deg_lon = 111.0 * math.cos(math.radians(center_lat))
    return area_deg2 * km_per_deg_lat * km_per_deg_lon
