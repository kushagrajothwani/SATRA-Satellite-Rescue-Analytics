# SATRA — Implementation Plan (Beginner-Friendly Handbook)

**Audience:** a second-year CS student building under hackathon time pressure.
**Companion docs:** `01_PRD.md` (what), `02_ARCHITECTURE.md` (how it works), `04_DESIGN.md` (how it looks), `05_DAY_BY_DAY_PLAN.md` (when).

> Rule of thumb: **one working end-to-end pipeline beats ten disconnected features.** Build the smallest thing that runs, then add.

---

## 1. Development Philosophy

- Learn while building: every term is explained the first time it appears.
- Exact commands, and *where* to run them (PowerShell on Windows, unless noted).
- Working functionality before theoretical perfection.
- Never present mock results as live analysis. Label sample data loudly.

---

## 2. Development Environment

**Assumed installed:** Windows, VS Code, Python 3.14, Node 24, Git.

### 2.1 Backend setup (already partially done in this repo)
```powershell
cd backend
py -3.14 -m venv venv
.\venv\Scripts\Activate.ps1
pip install fastapi "uvicorn[standard]" python-dotenv requests pydantic
pip install rasterio geopandas shapely networkx numpy
# Optional heavy ML (install when you reach Phase 4):
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip freeze > requirements.txt
```

### 2.2 Frontend setup
```powershell
cd frontend
npm install
npm run dev      # http://localhost:5173
```

### 2.3 Run the API
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload   # http://localhost:8000
```

### 2.4 Environment variables
Copy `.env.example` → `.env` and fill in:
```
COPERNICUS_USERNAME=your_email
COPERNICUS_PASSWORD=your_password
LLM_API_KEY=your_key_here
```
`.env` is git-ignored. **Never commit credentials.**

---

## 3. Repository Structure

```
SATRA-Satellite-Rescue-Analytics/
├── frontend/                 # React + TypeScript + MapLibre dashboard
│   └── src/{components,pages,maps,services,styles}
├── backend/                  # FastAPI app
│   └── app/{main.py,api/,core/,schemas/}
├── geospatial/               # Remote-sensing + GIS logic
│   ├── satellite/            # search.py, download.py, preprocess.py
│   ├── flood_mapping/        # change_detection.py, vectorize.py
│   ├── infrastructure/       # osm_historical.py, intersect.py
│   └── connectivity/         # graph.py, analyze.py
├── ml/                       # datasets/, models/, training/, inference/
│   └── {datasets,models,training,inference}
├── agents/                   # graph.py, state.py, tools.py, nodes/
├── database/                 # schema.sql, migrations
├── docs/                     # 01..05 documents
├── tests/                    # unit + integration + e2e
├── sample_data/              # cache + labelled demo data
├── .env.example  .gitignore  README.md
```

---

## 4. Development Phases

Each phase: **Objective → Commands → Files → Run → Test → Common errors → Done when.**

### PHASE 1 — Foundation ✅ (already scaffolded)
- **Objective:** frontend and backend talk; map shows a labelled sample layer.
- **Files:** `backend/app/main.py`, `frontend/src/App.tsx`.
- **Run:** both servers; open `http://localhost:5173`.
- **Done when:** header shows `Backend: ok` and a cyan sample polygon appears over Nepal.

### PHASE 2 — Geospatial data access
- **Objective:** discover/download Sentinel-1, fetch historical OSM + DEM.
- **Files:** `geospatial/satellite/search.py` ✅, `download.py` ✅, add `preprocess.py`; `geospatial/infrastructure/osm_historical.py`.
- **Commands:**
```powershell
cd backend; .\venv\Scripts\Activate.ps1
cd ..
python -m geospatial.satellite.search
```
- **Test:** a list of Sentinel-1 products with dates/orbit appears.
- **Common errors:** `401` → check Copernicus credentials; no results → widen date window; timeout → reduce `$top`.
- **Done when:** you can search, pick a product, and download it (or cache metadata offline).

### PHASE 3 — Satellite analysis (no ML yet)
- **Objective:** before/after change detection → flood GeoJSON.
- **Files:** `geospatial/flood_mapping/change_detection.py`, `vectorize.py`.
- **Method:** backscatter drop threshold + pre-event water exclusion → mask → polygons.
- **Test:** overlay output on the map; sanity-check against known water bodies.
- **Done when:** you have a real (or clearly-labelled demo) flood polygon layer.

### PHASE 4 — Machine learning
- **Objective:** train/fine-tune U-Net; run inference on a GeoTIFF.
- **Files:** `ml/datasets/`, `ml/models/unet.py`, `ml/training/train.py`, `ml/inference/predict.py`.
- **Datasets:** Kuro Siwo (primary, recommended by brief), Sen1Floods11 (secondary).
```powershell
# after downloading a dataset into ml/datasets/
python -m ml.training.train --data ml/datasets/kuro_siwo --epochs 20 --out ml/models/unet_sar.pt
python -m ml.inference.predict --model ml/models/unet_sar.pt --input sample_data/raw/post.tif --out sample_data/flood_prob.tif
```
- **Test:** metrics printed on validation; prediction GeoTIFF georeferenced correctly.
- **Never fabricate performance.** Report what you measure.
- **Done when:** inference produces a flood mask → polygons.

### PHASE 5 — Infrastructure intelligence
- **Objective:** intersect hazard with buildings/roads/bridges/hospitals.
- **Files:** `geospatial/infrastructure/intersect.py`.
- **Concept:**
```python
affected = infra[infra.geometry.intersects(flood_union)]
```
- **Handle:** invalid geometries (`make_valid`), CRS alignment, spatial index, uncertainty buffers.
- **Done when:** each feature has an exposure class + confidence, served as GeoJSON.

### PHASE 6 — Connectivity intelligence
- **Objective:** road graph → cut-off settlements.
- **Files:** `geospatial/connectivity/graph.py`, `analyze.py`.
- **Method:** build graph; classify edges by hazard; build **scenario** graph (don't mutate baseline); connected components to nearest hospital; alternative routes.
- **Done when:** settlement list with status + confidence appears on the Connectivity screen.

### PHASE 7 — Agentic AI
- **Objective:** LangGraph workflow → grounded answer + report.
- **Files:** `agents/state.py`, `tools.py`, `nodes/*.py`, `graph.py`.
- **Rules:** agents call typed tools; numbers only from tools; log every call.
- **Done when:** `/api/agent/query` returns an answer with an evidence trace.

### PHASE 8 — Frontend dashboard
- **Objective:** interactive map + panels + assistant + report.
- **Files:** `frontend/src/{pages,components,maps,services}`.
- **Done when:** judges can configure, view layers, inspect a cut-off settlement and export a report.

### PHASE 9 — Integration & hardening
- End-to-end run for one AOI/date; error states; loading states; provenance; caches.
- Test with judges' likely AOIs/dates.

### PHASE 10 — Submission
- README, six-page technical report, one-page situation report, 3-minute demo, attribution, repo cleanup.

---

## 5. ML Training Instructions (concrete)

1. **Dataset prep:** unzip Kuro Siwo/Sen1Floods11; organise `tiles/` + `masks/`.
2. **Band normalisation:** clip to per-channel percentiles; handle missing bands explicitly.
3. **Splits:** split by **event/geography**, not random tiles (avoid leakage).
4. **Model:** U-Net (see `ml/models/unet.py`), 6 input channels, 3 classes.
5. **Loss:** `BCEWithLogitsLoss + DiceLoss`.
6. **Loop:** Adam, LR 1e-3, checkpoint best val IoU.
7. **Evaluate:** IoU / precision / recall / F1 per class.
8. **Save:** `torch.save(model.state_dict(), "ml/models/unet_sar.pt")`.
9. **Inference:** patchwise on GeoTIFF, stitch, write `flood_prob.tif`.
10. **Vectorise:** threshold → simplify → `GeoJSON`.

> Realistic demo path: if a full training run is not possible in time, ship the trained-weights pipeline with a small fine-tune and **clearly document** the training scale.

---

## 6. Agentic AI Instructions

- **State:** typed dict (see `agents/state.py`).
- **Nodes:** planner → satellite → damage → connectivity → report.
- **Tools:** `get_flood_statistics`, `get_affected_buildings`, `get_affected_roads`, `get_disconnected_settlements`, `get_nearest_alternative_hospital`, `generate_situation_report`.
- **Transitions:** conditional on run status / missing evidence.
- **Outputs:** Pydantic models validated before returning.
- **Guardrails:** allow-list tools only; no shell; no raw SQL; if evidence missing, say so.
- **Fallback:** works even without an LLM key by using deterministic templates.

---

## 7. Integration Testing

One end-to-end test (`tests/test_e2e.py`):
```
configure AOI/date → analysis runs → flood map →
infrastructure assessed → connectivity computed →
agent report generated → API returns all layers
```
Plus unit tests per module and API contract tests. Run: `pytest -q`.

---

## 8. Time Management

| Track | Plan |
|---|---|
| 3-day emergency MVP | Day1 map + change detection; Day2 infra + connectivity; Day3 agent report + polish |
| 7-day prototype | Days 1–2 foundation+data; 3–4 analysis; 5 ML; 6 connectivity; 7 agents+frontend |
| 14-day polished | Follow the 10 phases above with testing/report buffer |

See `05_DAY_BY_DAY_PLAN.md` for the calendar.

---

## 9. Effort Allocation (suggested)

- 35% satellite processing + ML
- 25% infrastructure + connectivity
- 20% agentic AI
- 15% dashboard
- 5% docs/presentation

---

## 10. Common Errors & Debugging

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: rasterio` | not in venv | activate venv, `pip install rasterio` |
| CORS error in browser | backend origin mismatch | confirm `allow_origins=["http://localhost:5173"]` |
| Map blank | bad style/tiles | check network tab; swap basemap |
| `401` Copernicus | bad credentials | fix `.env` |
| Geometry error in intersect | invalid polygon | `shapely.make_valid` |
| Agent hallucinated number | bypassed tools | tighten prompt + require tool evidence |
| PDF fonts missing | Nepali glyphs | bundle a Devanagari font |
