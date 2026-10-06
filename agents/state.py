"""Shared, typed agent state exchanged between SATRA agents.

Agents communicate through this structured state rather than free-form chat,
which keeps the workflow deterministic and auditable.
"""
from __future__ import annotations

from typing import Any, TypedDict


class SatraState(TypedDict, total=False):
    run_id: str
    aoi: dict[str, Any]
    event_date: str

    satellite_status: str
    flood: dict[str, Any]
    flood_map_path: str | None

    infrastructure_results: dict[str, Any]
    connectivity_results: dict[str, Any]

    evidence: list[dict[str, Any]]
    report: str | None
    errors: list[str]
