"""Agent nodes for the SATRA LangGraph workflow.

Each node performs one stage of the analysis and writes to the shared state.
Nodes call deterministic tools; they never invent numbers.

These nodes are plain functions, so they work both inside a LangGraph graph and
in the simple sequential fallback runner (`agents/graph.py`).
"""
from __future__ import annotations

from typing import Any

from agents import tools
from agents.state import SatraState


def planner_agent(state: SatraState) -> dict[str, Any]:
    """Validate the request and record the plan."""
    errors: list[str] = []
    if not state.get("run_id"):
        errors.append("missing run_id")
    evidence = state.get("evidence", [])
    evidence.append({"agent": "planner", "action": "validated request", "ok": not errors})
    return {"evidence": evidence, "errors": state.get("errors", []) + errors}


def satellite_agent(state: SatraState) -> dict[str, Any]:
    stats = tools.get_flood_statistics(state.get("run_id"))
    evidence = state.get("evidence", [])
    evidence.append({"agent": "satellite", "tool": "get_flood_statistics", "result": stats})
    return {
        "satellite_status": "completed",
        "flood": {"statistics": stats},
        "evidence": evidence,
    }


def damage_agent(state: SatraState) -> dict[str, Any]:
    buildings = tools.get_affected_buildings(state.get("run_id"))
    roads = tools.get_affected_roads(state.get("run_id"))
    evidence = state.get("evidence", [])
    evidence.append({"agent": "damage", "tool": "get_affected_buildings", "result": buildings})
    evidence.append({"agent": "damage", "tool": "get_affected_roads", "result": roads})
    return {
        "infrastructure_results": {"buildings": buildings, "roads": roads},
        "evidence": evidence,
    }


def connectivity_agent(state: SatraState) -> dict[str, Any]:
    disc = tools.get_disconnected_settlements(state.get("run_id"))
    evidence = state.get("evidence", [])
    evidence.append(
        {"agent": "connectivity", "tool": "get_disconnected_settlements", "result": disc}
    )
    return {"connectivity_results": disc, "evidence": evidence}


def report_agent(state: SatraState) -> dict[str, Any]:
    report = tools.generate_situation_report(state.get("run_id"), language="en")
    evidence = state.get("evidence", [])
    evidence.append(
        {"agent": "report", "tool": "generate_situation_report", "result": report["numbers"]}
    )
    return {"report": report["body_md"], "evidence": evidence}
