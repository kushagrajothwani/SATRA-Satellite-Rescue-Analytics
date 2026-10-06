"""Pydantic request/response schemas for the SATRA API."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AOI(BaseModel):
    name: str = "Syapru Besi"
    # (min_lon, min_lat, max_lon, max_lat)
    bbox: tuple[float, float, float, float] = (85.20, 28.00, 85.60, 28.40)


class AnalysisRequest(BaseModel):
    aoi: AOI = Field(default_factory=AOI)
    disaster_date: str = "2026-08-26"
    pre_window: tuple[str, str] = ("2026-08-01", "2026-08-14")
    post_window: tuple[str, str] = ("2026-08-26", "2026-09-05")
    sensors: list[Literal["S1", "S2"]] = ["S1"]
    demo_mode: bool = True


class AnalysisCreated(BaseModel):
    run_id: str
    status: str
    message: str


class AgentQuery(BaseModel):
    run_id: str
    question: str


class AgentAnswer(BaseModel):
    answer: str
    evidence: list[dict[str, Any]] = []
    sources: list[str] = []
    confidence: str = "medium"
    grounded: bool = True
