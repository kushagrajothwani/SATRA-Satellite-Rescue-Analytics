"""Agentic AI orchestration for SATRA.

Builds a controlled five-node workflow:
    planner -> satellite -> damage -> connectivity -> report

If LangGraph is installed it is used directly; otherwise a simple sequential
runner produces the same state transitions. In both cases the *numbers* come
from `agents.tools` (deterministic), never from the language model.

`answer_question()` adds an optional LLM step for natural-language phrasing.
If no LLM key is configured (or the call fails), a deterministic template
answer is produced from the tool evidence instead -- so the demo never depends
on the LLM being reachable.
"""
from __future__ import annotations

from typing import Any

from agents import nodes, tools
from agents.state import SatraState

try:  # pragma: no cover - optional dependency
    from langgraph.graph import END, START, StateGraph

    HAVE_LANGGRAPH = True
except Exception:  # pragma: no cover
    HAVE_LANGGRAPH = False


def build_graph():
    """Return a compiled LangGraph graph, or None if LangGraph is unavailable."""
    if not HAVE_LANGGRAPH:
        return None
    g = StateGraph(SatraState)
    g.add_node("planner", nodes.planner_agent)
    g.add_node("satellite", nodes.satellite_agent)
    g.add_node("damage", nodes.damage_agent)
    g.add_node("connectivity", nodes.connectivity_agent)
    g.add_node("report", nodes.report_agent)

    g.add_edge(START, "planner")
    g.add_edge("planner", "satellite")
    g.add_edge("satellite", "damage")
    g.add_edge("damage", "connectivity")
    g.add_edge("connectivity", "report")
    g.add_edge("report", END)
    return g.compile()


def run_workflow(run_id: str, aoi: dict | None = None, event_date: str | None = None) -> SatraState:
    """Run the full agent workflow and return the final state."""
    initial: SatraState = {
        "run_id": run_id,
        "aoi": aoi or {},
        "event_date": event_date or "",
        "evidence": [],
        "errors": [],
    }

    compiled = build_graph()
    if compiled is not None:
        return compiled.invoke(initial)

    # Sequential fallback -------------------------------------------------
    state = dict(initial)
    for node in (
        nodes.planner_agent,
        nodes.satellite_agent,
        nodes.damage_agent,
        nodes.connectivity_agent,
        nodes.report_agent,
    ):
        state.update(node(state))
    return state  # type: ignore[return-value]


def _route_question(question: str, run_id: str) -> list[tuple[str, dict[str, Any]]]:
    """Map a natural-language question to the deterministic tools to call."""
    q = question.lower()
    calls: list[tuple[str, dict[str, Any]]] = []

    def call(name: str):
        return (name, getattr(tools, name)(run_id))

    if any(k in q for k in ("disconnect", "cut off", "isolat", "hospital", "access")):
        calls.append(call("get_disconnected_settlements"))
    if any(k in q for k in ("road", "route", "bridge", "blocked")):
        calls.append(call("get_affected_roads"))
    if any(k in q for k in ("building", "house", "structure")):
        calls.append(call("get_affected_buildings"))
    if any(k in q for k in ("flood", "water", "extent", "inundat")):
        calls.append(call("get_flood_statistics"))
    if any(k in q for k in ("report", "situation", "summary")):
        calls.append(call("generate_situation_report"))
    if not calls:
        calls.append(call("get_flood_statistics"))
        calls.append(call("get_disconnected_settlements"))
    return calls


def _template_answer(calls, question) -> str:
    lines = ["Based on verified geospatial tools:"]
    for name, result in calls:
        if name == "get_disconnected_settlements":
            if not result["settlements"]:
                lines.append("- No settlements lost their modelled hospital route.")
            else:
                lines.append(
                    f"- {result['disconnected_count']} settlement(s) lost a modelled hospital route: "
                    + ", ".join(s["name"] for s in result["settlements"])
                )
        elif name == "get_affected_roads":
            lines.append(
                f"- {result['affected_road_segments']} road segment(s) intersect hazard; "
                f"blocked segments: {', '.join(result['blocked_edge_ids']) or 'none'}."
            )
        elif name == "get_affected_buildings":
            lines.append(
                f"- {result['potentially_exposed_or_higher']} building(s) are potentially exposed."
            )
        elif name == "get_flood_statistics":
            lines.append(
                f"- {result['high_confidence_polygons'] + result['moderate_confidence_polygons']} "
                f"flood polygon(s) and {result['uncertain_change_polygons']} uncertain-change zone(s) detected."
            )
        elif name == "generate_situation_report":
            lines.append("- A one-page situation report was generated (see report panel).")
    lines.append(
        "These are modelled exposure/connectivity results, not confirmed damage or a "
        "claim about individuals."
    )
    return "\n".join(lines)


def answer_question(run_id: str, question: str) -> dict[str, Any]:
    calls = _route_question(question, run_id)
    evidence = [{"tool": n, "result": r} for n, r in calls]

    answer = None
    # Optional LLM phrasing -- strictly constrained to the tool evidence.
    try:
        from app.core.config import settings

        if settings.has_llm:
            answer = _llm_answer(question, evidence)
    except Exception:
        answer = None

    if not answer:
        answer = _template_answer(calls, question)

    return {
        "answer": answer,
        "evidence": evidence,
        "sources": ["Sentinel-1 (demo)", "historical OSM (demo)", "Copernicus DEM (demo)"],
        "confidence": "medium",
        "grounded": True,
        "engine": "llm" if answer and "Based on" not in answer else "deterministic",
    }


def _llm_answer(question: str, evidence: list[dict[str, Any]]) -> str | None:
    """Call an OpenAI-compatible endpoint if configured. Numbers stay verbatim."""
    import json
    import urllib.request

    from app.core.config import settings

    system = (
        "You are SATRA's Situation Report Agent. Summarise ONLY the provided "
        "tool evidence for disaster-response coordinators. Rules: never invent "
        "numbers; use only the evidence; distinguish detected hazards from "
        "confirmed damage; never claim to locate missing people; if evidence is "
        "missing say so; keep it concise."
    )
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": f"Question: {question}\nEvidence JSON:\n{json.dumps(evidence)[:12000]}",
            },
        ],
        "temperature": 0.1,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.llm_api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None
