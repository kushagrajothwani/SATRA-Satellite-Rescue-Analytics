"""Runtime configuration for the SATRA backend, loaded from the environment."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project root = three levels up from this file (backend/app/core/config.py)
ROOT = Path(__file__).resolve().parents[3]
SAMPLE_DATA = ROOT / "sample_data"
RUNS_DIR = SAMPLE_DATA / "runs"
EXPORT_DIR = SAMPLE_DATA / "exports"

RUNS_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


class Settings:
    """Simple settings object; values come from .env when present."""

    copernicus_username: str | None = os.getenv("COPERNICUS_USERNAME")
    copernicus_password: str | None = os.getenv("COPERNICUS_PASSWORD")
    llm_api_key: str | None = os.getenv("LLM_API_KEY")

    # Default demo AOI: Trishuli / Syapru Besi corridor, Nepal
    default_bbox: tuple[float, float, float, float] = (85.20, 28.00, 85.60, 28.40)
    default_disaster_date: str = "2026-08-26"

    @property
    def has_copernicus(self) -> bool:
        return bool(self.copernicus_username and self.copernicus_password)

    @property
    def has_llm(self) -> bool:
        return bool(self.llm_api_key)


settings = Settings()
