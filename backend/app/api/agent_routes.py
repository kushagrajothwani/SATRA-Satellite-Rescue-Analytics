"""Agent Q&A and report endpoints (evidence-grounded)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agents.graph import answer_question, run_workflow
from agents.tools import generate_situation_report
from app.core import store
from app.schemas.models import AgentQuery

router = APIRouter()


@router.post("/query")
def agent_query(q: AgentQuery):
    if not store.get_run(q.run_id):
        raise HTTPException(status_code=404, detail=f"run '{q.run_id}' not found")
    return answer_question(q.run_id, q.question)


@router.post("/run/{run_id}")
def agent_run(run_id: str):
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found")
    state = run_workflow(run_id, run.get("aoi"), run.get("event_date"))
    return {
        "run_id": run_id,
        "report": state.get("report"),
        "evidence": state.get("evidence", []),
        "errors": state.get("errors", []),
    }


@router.get("/report/{run_id}")
def report(run_id: str, language: str = "en"):
    if not store.get_run(run_id):
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found")
    return generate_situation_report(run_id, language=language)
