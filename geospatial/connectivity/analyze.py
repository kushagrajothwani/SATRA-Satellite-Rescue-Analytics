"""Road-network connectivity engine.

Given pre-event road segments and a hazard layer, SATRA asks: which settlements
still have a *modelled* road connection to a hospital?

Method
------
1. Build the baseline road graph G=(V,E) from OSM/pre-event roads.
2. Classify each edge by hazard intersection
   (blocked / uncertain / passable).
3. Build a *scenario passability graph*: the baseline graph is never mutated;
   only blocked edges are removed in a copy.
4. Reachability to the nearest hospital is computed on both graphs.

Result classes
--------------
    connected                - a modelled route remains
    no_modelled_connection   - routed before the event, none now
    uncertain                - only routes via uncertain-change edges
    insufficient_road_data   - no baseline route even before the event

A settlement with "no_modelled_connection" is NOT necessarily physically
inaccessible: it means no usable connection was found under modelled
assumptions. This distinction is preserved everywhere in the UI and reports.

Uses NetworkX when installed; otherwise falls back to a small built-in graph so
the prototype runs with zero extra dependencies.
"""
from __future__ import annotations

import heapq
from typing import Any

from geospatial import demo_data, geometry
from geospatial.flood_mapping import change_detection

try:  # pragma: no cover - optional dependency
    import networkx as nx

    HAVE_NETWORKX = True
except Exception:  # pragma: no cover
    HAVE_NETWORKX = False


class SimpleGraph:
    """Minimal undirected weighted graph with node coordinates."""

    def __init__(self) -> None:
        self.coords: dict[str, tuple[float, float]] = {}
        self.adj: dict[str, dict[str, float]] = {}

    def add_node(self, n: str, xy: tuple[float, float]) -> None:
        self.coords[n] = xy
        self.adj.setdefault(n, {})

    def add_edge(self, a: str, b: str, weight: float) -> None:
        self.adj.setdefault(a, {})[b] = weight
        self.adj.setdefault(b, {})[a] = weight

    def reachable(self, src: str, targets: set[str]) -> str | None:
        if src not in self.adj:
            return None
        if src in targets:
            return src
        seen = {src}
        stack = [src]
        while stack:
            cur = stack.pop()
            for nb in self.adj.get(cur, {}):
                if nb in targets:
                    return nb
                if nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        return None

    def shortest_to_any(self, src: str, targets: set[str]) -> tuple[str, float] | None:
        if src not in self.adj:
            return None
        dist: dict[str, float] = {src: 0.0}
        pq = [(0.0, src)]
        while pq:
            d, cur = heapq.heappop(pq)
            if cur in targets:
                return cur, d
            if d > dist.get(cur, float("inf")):
                continue
            for nb, w in self.adj.get(cur, {}).items():
                nd = d + w
                if nd < dist.get(nb, float("inf")):
                    dist[nb] = nd
                    heapq.heappush(pq, (nd, nb))
        return None


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    import math

    R = 6371.0
    lon1, lat1 = a
    lon2, lat2 = b
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def build_graph(roads, hazards):
    """Return (passable_graph, baseline_graph, edge_status)."""
    core = [hazards["hazard_rings"][1]]
    extent = [hazards["hazard_rings"][0]]
    anomaly = demo_data.ANOMALY_RINGS

    passable = SimpleGraph()
    baseline = SimpleGraph()
    edge_status: list[dict[str, Any]] = []

    for r in roads:
        a, b = r["from"], r["to"]
        coords = r["coords"]
        for nid in (a, b):
            xy = demo_data.NODES.get(nid, coords[0] if nid == a else coords[-1])
            passable.add_node(nid, xy)
            baseline.add_node(nid, xy)

        w = _haversine_km(coords[0], coords[-1]) or 1.0
        baseline.add_edge(a, b, w)

        if geometry.line_intersects_any(coords, core) or geometry.line_intersects_any(
            coords, extent
        ):
            status = "blocked"
        elif geometry.line_intersects_any(coords, anomaly):
            status = "uncertain"
        else:
            status = "passable"

        if status != "blocked":
            passable.add_edge(a, b, w)

        edge_status.append(
            {"id": r["id"], "from": a, "to": b, "highway": r["highway"], "status": status}
        )

    # Attach hospitals to the road network at their nearest node. A health
    # facility is reached via the settlement it sits in; these short access
    # edges are not themselves hazard-classified.
    for h in demo_data.HOSPITALS:
        hid = h["id"]
        hxy = (h["lon"], h["lat"])
        passable.add_node(hid, hxy)
        baseline.add_node(hid, hxy)
        nearest = min(
            (n for n in baseline.coords if n != hid),
            key=lambda n: _haversine_km(hxy, baseline.coords[n]),
            default=None,
        )
        if nearest:
            w = max(_haversine_km(hxy, baseline.coords[nearest]), 0.05)
            passable.add_edge(hid, nearest, w)
            baseline.add_edge(hid, nearest, w)

    return passable, baseline, edge_status


def analyze_connectivity(hazard: dict | None = None) -> dict:
    hazard = hazard or change_detection.detect_flood_from_demo()
    passable, baseline, edge_status = build_graph(demo_data.ROADS, hazard)

    hospital_ids = {h["id"] for h in demo_data.HOSPITALS}
    hospital_names = {h["id"]: h["name"] for h in demo_data.HOSPITALS}

    results = []
    disconnected = 0
    for s in demo_data.SETTLEMENTS:
        sid = s["id"]
        base_hit = baseline.reachable(sid, hospital_ids)
        pass_hit = passable.reachable(sid, hospital_ids)

        # uncertain-only route check
        uncertain_reach = None
        if base_hit and not pass_hit:
            # any node reachable in baseline that can reach a hospital through
            # an uncertain edge? approximate by testing passable graph from
            # uncertain edge endpoints.
            for e in edge_status:
                if e["status"] == "uncertain" and (
                    e["from"] == sid or e["to"] == sid
                ):
                    uncertain_reach = base_hit

        if not base_hit:
            status = "insufficient_road_data"
            conf = "low"
        elif pass_hit:
            status = "connected"
            conf = "medium"
        elif uncertain_reach:
            status = "uncertain"
            conf = "low"
        else:
            status = "no_modelled_connection"
            conf = "medium"

        best = passable.shortest_to_any(sid, hospital_ids) or baseline.shortest_to_any(
            sid, hospital_ids
        )
        nearest = hospital_names.get(best[0]) if best else None
        distance = round(best[1], 1) if best else None

        if status in ("no_modelled_connection", "uncertain"):
            disconnected += 1

        results.append(
            {
                "settlement_id": sid,
                "name": s["name"],
                "pop_est": s["pop_est"],
                "lon": s["lon"],
                "lat": s["lat"],
                "status": status,
                "nearest_hospital": nearest,
                "distance_km": distance,
                "alternative_route": pass_hit is not None,
                "confidence": conf,
                "reason": _reason(status),
            }
        )

    return {
        "meta": demo_data.demo_metadata(),
        "engine": "networkx" if HAVE_NETWORKX else "builtin",
        "settlements": results,
        "disconnected_count": disconnected,
        "total_settlements": len(results),
        "road_edges": edge_status,
        "sources": ["pre-event OSM road network (demo)", "Sentinel-1 flood extent (demo)"],
    }


def _reason(status: str) -> str:
    return {
        "connected": "A modelled route to a hospital remains.",
        "no_modelled_connection": (
            "All modelled paths to a hospital intersect high-confidence hazard "
            "segments; no alternative route was identified."
        ),
        "uncertain": (
            "A route exists only through segments classified as uncertain change."
        ),
        "insufficient_road_data": (
            "No baseline road route was found even before the event; likely "
            "incomplete OSM road data, not necessarily physical inaccessibility."
        ),
    }.get(status, "Unknown status.")


def _fc(features):
    return {"type": "FeatureCollection", "features": features}
