# SATRA — Satellite-Assisted Terrain & Rescue Analytics

> **From Space to Safety.**
> When roads, bridges and phone lines are gone, rescuers still need to know *where the damage is* and *who is cut off*. SATRA tells them — from space.

SATRA is a multimodal, evidence-grounded disaster-intelligence platform that turns satellite observations into rescue intelligence. It detects flood extent with SAR machine learning, overlays pre-event OpenStreetMap infrastructure, and runs a road-network connectivity analysis to find settlements with **no modelled route to a hospital**. An agentic AI layer answers rescue questions and writes a one-page situation report — but every number it states comes from a deterministic geospatial tool, never from the language model.

`Multimodal AI Hackathon 2026 · Track B — Mapping Flood Damage from Space`

---

## Why SATRA is different

| Typical project | SATRA |
|---|---|
| Flood mask heatmap | Flood extent **+** infrastructure exposure **+** road-network isolation |
| Chatbot bolted onto a map | Five-agent workflow where the LLM may only *summarise tool output* |
| "AI detected damage" | Explicitly distinguishes **detected exposure** from **confirmed damage** |

---

## Architecture at a glance

```
React + MapLibre dashboard
        │  REST
FastAPI orchestration  ──  Agentic AI (LangGraph, tool-grounded)
        │
Geospatial engine (change detection, OSM, graph)  ──  ML engine (U-Net SAR segmentation)
        │
Copernicus Data Space · ohsome OSM · Copernicus DEM · Kuro Siwo / Sen1Floods11
```

See [`docs/02_ARCHITECTURE.md`](docs/02_ARCHITECTURE.md) for the full design.

---

## Documentation

| Doc | Purpose |
|---|---|
| [`docs/01_PRD.md`](docs/01_PRD.md) | What we build, for whom, acceptance criteria |
| [`docs/02_ARCHITECTURE.md`](docs/02_ARCHITECTURE.md) | How the system works (layers, DB, API, ML, agents) |
| [`docs/03_IMPLEMENTATION.md`](docs/03_IMPLEMENTATION.md) | Beginner-friendly build handbook |
| [`docs/04_DESIGN.md`](docs/04_DESIGN.md) | UI/UX design system and screens |
| [`docs/05_DAY_BY_DAY_PLAN.md`](docs/05_DAY_BY_DAY_PLAN.md) | Day-by-day execution plan |
| [`docs/06_ML_AGENTIC_AI.md`](docs/06_ML_AGENTIC_AI.md) | How ML + agentic AI integrate |

---

## Quick start

### Prerequisites
Windows, Python 3.11+, Node 18+, Git. (Tested with Python 3.14, Node 24.)

### 1. Backend

```powershell
cd backend
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://localhost:8000
```

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

Open the frontend, click **Run analysis**. With no credentials configured, SATRA runs its clearly-labelled **synthetic demo pipeline**, so the whole flow works offline.

### 3. Real satellite data (optional)

Copy `.env.example` → `.env` and add Copernicus credentials:

```
COPERNICUS_USERNAME=your_email
COPERNICUS_PASSWORD=your_password
LLM_API_KEY=your_key_here          # optional; enables LLM phrasing
```

Then:

```powershell
$env:PYTHONPATH=$PWD
python -m geospatial.satellite.search          # discover Sentinel-1 products
python -m geospatial.satellite.download <ID> pre_event.zip
```

---

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | liveness + config status |
| POST | `/api/analysis` | start an analysis run |
| GET | `/api/analysis/{run_id}` | status + summary |
| GET | `/api/flood-zones/{run_id}` | flood GeoJSON |
| GET | `/api/infrastructure/{run_id}` | infrastructure GeoJSON |
| GET | `/api/connectivity/{run_id}` | cut-off settlement results |
| POST | `/api/agent/query` | grounded Q&A |
| GET | `/api/agent/report/{run_id}` | situation report |
| GET | `/api/sample-flood` | labelled demo layer |

---

## Project structure

```
SATRA-Satellite-Rescue-Analytics/
├── frontend/        React + TypeScript + MapLibre dashboard
├── backend/         FastAPI app  (app/main.py, app/api/, pipeline.py)
├── geospatial/      satellite/ flood_mapping/ infrastructure/ connectivity/
├── ml/              models/ training/ inference/
├── agents/          state.py tools.py nodes.py graph.py
├── database/        schema.sql (PostGIS)
├── docs/            01–06 documents
├── tests/           geometry + pipeline + API tests
└── sample_data/     caches + clearly-labelled demo data
```

---

## Running tests

```powershell
.\backend\venv\Scripts\python.exe -m pytest -q
```

---

## Data provenance & ethics

- Allowed inputs: Sentinel-1, Sentinel-2, Copernicus DEM, **pre-event** OSM, training datasets.
- **Validation only:** Copernicus EMS (EMSR927), UNOSAT, published damage maps, post-event OSM edits.
- SATRA never identifies individuals; it reports *potentially isolated settlements* and *exposure*, not confirmed damage.
- The demo dataset is synthetic and clearly labelled everywhere it appears.

### Required attribution
- **Satellite:** "Contains modified Copernicus Sentinel data 2026."
- **Elevation:** "Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved."
- **OpenStreetMap:** "© OpenStreetMap contributors."
- **Datasets:** Kuro Siwo (Bountos et al., 2024); Sen1Floods11.

---

## Tech stack

React · TypeScript · MapLibre GL JS · FastAPI · Pydantic · Rasterio/GDAL · GeoPandas · Shapely · NetworkX · PyTorch (U-Net) · LangGraph · PostgreSQL/PostGIS (production) · Docker (optional).
