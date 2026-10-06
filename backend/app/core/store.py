"""File-backed store for analysis runs.

For the hackathon we persist each run as a JSON document under
`sample_data/runs/`. This keeps the whole prototype dependency-free and makes
provenance easy to inspect. In production this maps onto the PostgreSQL +
PostGIS schema described in docs/02_ARCHITECTURE.md.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import RUNS_DIR


def _run_path(run_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", run_id)
    return RUNS_DIR / f"{safe}.json"


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"SATRA-{stamp}"


def save_run(run: dict[str, Any]) -> None:
    run.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
    _run_path(run["run_id"]).write_text(json.dumps(run, indent=2), encoding="utf-8")


def get_run(run_id: str) -> dict[str, Any] | None:
    path = _run_path(run_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_runs() -> list[dict[str, Any]]:
    runs = []
    for path in sorted(RUNS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            runs.append(
                {
                    "run_id": data.get("run_id"),
                    "status": data.get("status"),
                    "aoi": data.get("aoi"),
                    "created_at": data.get("created_at"),
                }
            )
        except Exception:  # pragma: no cover - tolerate corrupt files
            continue
    return runs
