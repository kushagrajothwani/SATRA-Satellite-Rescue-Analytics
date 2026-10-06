"""End-to-end pipeline + agent grounding tests (offline, demo data)."""
from agents.graph import answer_question, run_workflow
from agents import tools
from geospatial.connectivity import analyze as connectivity
from geospatial.flood_mapping import change_detection
from geospatial.infrastructure import intersect as infra


def test_demo_flood_has_all_classes():
    flood = change_detection.detect_flood_from_demo()
    assert flood["high_confidence"]["features"]
    assert flood["moderate_confidence"]["features"]
    assert flood["uncertain_change"]["features"]


def test_infrastructure_summary_present():
    result = infra.analyze_infrastructure()
    for layer in ("buildings", "roads", "bridges", "hospitals"):
        assert layer in result["summary"]


def test_connectivity_classifies_every_settlement():
    conn = connectivity.analyze_connectivity()
    assert conn["total_settlements"] > 0
    valid = {
        "connected",
        "no_modelled_connection",
        "uncertain",
        "insufficient_road_data",
    }
    for s in conn["settlements"]:
        assert s["status"] in valid
        assert s["confidence"] in {"high", "medium", "low"}


def test_report_numbers_match_tools():
    """The report must reuse tool numbers exactly (no invention)."""
    flood = tools.get_flood_statistics("demo")
    report = tools.generate_situation_report("demo")
    expected = (
        flood["high_confidence_polygons"] + flood["moderate_confidence_polygons"]
    )
    assert report["numbers"]["flood_polygons"] == expected


def test_agent_answer_is_grounded_and_has_evidence():
    ans = answer_question("demo", "Which settlements lost road access to hospitals?")
    assert ans["grounded"] is True
    assert ans["evidence"], "agent answered without calling any tool"
    assert any(e["tool"] == "get_disconnected_settlements" for e in ans["evidence"])


def test_workflow_runs_all_stages():
    state = run_workflow("demo")
    assert state.get("report")
    assert len(state.get("evidence", [])) >= 4
