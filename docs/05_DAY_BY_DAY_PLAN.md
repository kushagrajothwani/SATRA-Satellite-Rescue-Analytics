# SATRA — Day-by-Day Execution Plan (Simple & Practical)

**Who this is for:** you, building SATRA mostly alone, possibly in a short hackathon window.
**How to read it:** each day has a **Goal**, **Do this**, **Files**, and a **Done when** checklist. If a day slips, don't skip the next — protect the end-to-end pipeline first.

> Golden rule: **a running end-to-end demo with clearly-labelled demo data beats a half-built perfect pipeline.** Label anything synthetic.

---

## Overview

| Day | Theme | Output |
|---|---|---|
| 1 | Foundation & plan | 4 docs + running app with map |
| 2 | Satellite access | Sentinel-1 search + download working |
| 3 | Change detection | Before/after + flood polygons (no ML) |
| 4 | ML setup | Dataset ready, U-Net code, first training run |
| 5 | ML inference | Flood mask from model → polygons |
| 6 | Infrastructure | OSM extraction + exposure analysis |
| 7 | Connectivity | Road graph + cut-off settlements |
| 8 | Agentic AI | Grounded Q&A + report generator |
| 9 | Frontend dashboard | All layers + panels on the map |
| 10 | Integration | End-to-end run, error/loading states |
| 11 | Validation | EMSR927 comparison (independent) |
| 12 | Report & Nepali | One-page report + multilingual |
| 13 | Testing & polish | Tests, unseen-area check, cleanup |
| 14 | Submission | README, 6-page report, demo video, push |

*(If you only have 3 days, use the compressed track at the end.)*

---

## Day 1 — Foundation & Plan
**Goal:** everyone knows what you're building; frontend ↔ backend works.

**Do this**
1. Read all four docs in `docs/`.
2. Confirm servers run (Phase 1 of the implementation doc).
3. Create the GitHub repo remote (already: `kushagrajothwani/SATRA-Satellite-Rescue-Analytics`).

**Files:** `docs/01..04`, `backend/app/main.py`, `frontend/src/App.tsx`

**Done when**
- [ ] `uvicorn` serves `/api/health` → `{"status":"ok"}`
- [ ] `npm run dev` shows the map with the labelled sample polygon
- [ ] Header shows `Backend: ok`

---

## Day 2 — Satellite Access
**Goal:** find and download real Sentinel-1 imagery for the Nepal AOI.

**Do this**
1. Put Copernicus credentials in `.env`.
2. Run the search script; note products with the **same relative orbit** ~12 days apart.
3. Download one pre-event and one post-event product.

**Files:** `geospatial/satellite/search.py`, `download.py`, add `preprocess.py`

**Commands**
```powershell
python -m geospatial.satellite.search
python -m geospatial.satellite.download <PRODUCT_ID> pre_event.zip
```

**Done when**
- [ ] Search returns dated products with orbit info
- [ ] Two products (pre + post) exist in `sample_data/raw/`

**If blocked:** cache the catalogue metadata and continue; label the analysis "demo".

---

## Day 3 — Change Detection (no ML yet)
**Goal:** a flood polygon layer from SAR change, before any neural network.

**Do this**
1. Preprocess: calibration → speckle filter → dB → reproject → tile.
2. Change detection: post-minus-pre backscatter drop + threshold.
3. Exclude permanent water; vectorise mask → GeoJSON.

**Files:** `geospatial/flood_mapping/change_detection.py`, `vectorize.py`

**Done when**
- [ ] `sample_data/flood.geojson` exists
- [ ] It renders on the map
- [ ] You can explain why a pixel was flagged

---

## Day 4 — ML Setup & First Training
**Goal:** dataset ready and a first U-Net training run.

**Do this**
1. Download Kuro Siwo (primary) and/or Sen1Floods11.
2. Inspect tiles/masks; build splits **by event**, not random tiles.
3. Train baseline U-Net.

**Files:** `ml/datasets/`, `ml/models/unet.py`, `ml/training/train.py`

**Commands**
```powershell
pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m ml.training.train --data ml/datasets/kuro_siwo --epochs 10 --out ml/models/unet_sar.pt
```

**Done when**
- [ ] Loss decreases; validation metrics print
- [ ] A checkpoint is saved
- [ ] You have NOT invented any accuracy number

---

## Day 5 — ML Inference
**Goal:** model output becomes geospatial polygons.

**Do this**
1. Run patchwise inference on a GeoTIFF.
2. Stitch probability raster; threshold; vectorise.
3. Distinguish **water** vs **uncertain change** (never call it confirmed debris).

**Files:** `ml/inference/predict.py`, `geospatial/flood_mapping/vectorize.py`

**Done when**
- [ ] `flood_prob.tif` written and georeferenced
- [ ] Polygons align with the imagery
- [ ] Class 2 labelled "uncertain change" in the UI

---

## Day 6 — Infrastructure Intelligence
**Goal:** know which buildings/roads/bridges/hospitals are exposed.

**Do this**
1. Extract historical OSM via ohsome for the **pre-event date**.
2. Repair geometries, align CRS, build spatial index.
3. Intersect with hazard; classify exposure + confidence.

**Files:** `geospatial/infrastructure/osm_historical.py`, `intersect.py`

**Done when**
- [ ] Buildings/roads/bridges/hospitals fetched for the pre-event snapshot
- [ ] Exposure classes computed and exported
- [ ] Results show as toggleable map layers

---

## Day 7 — Connectivity Intelligence ⭐
**Goal:** the differentiator — settlements with no modelled hospital route.

**Do this**
1. Build road graph (NetworkX).
2. Classify edges by hazard intersection.
3. Build a **scenario passability graph** (keep baseline intact).
4. Connected components + shortest path to nearest hospital; find alternatives.

**Files:** `geospatial/connectivity/graph.py`, `analyze.py`

**Done when**
- [ ] Each settlement gets: status, nearest hospital, alt route, confidence
- [ ] Map shows cut-off markers
- [ ] You can explain "no mapped route ≠ physically inaccessible"

---

## Day 8 — Agentic AI
**Goal:** grounded Q&A and a report generator.

**Do this**
1. Define typed state + deterministic tools.
2. Implement the five agent nodes.
3. Wire `/api/agent/query`; enforce tool-only numbers.
4. Add deterministic fallback (works with no LLM key).

**Files:** `agents/state.py`, `tools.py`, `nodes/`, `graph.py`

**Done when**
- [ ] A question returns an answer **plus** a tool/evidence trace
- [ ] Numbers match tool output exactly
- [ ] Missing evidence is stated, not invented

---

## Day 9 — Frontend Dashboard
**Goal:** judges see/understand everything.

**Do this**
1. Build the 3-panel dashboard, layer control, metric cards.
2. Add before/after slider and connectivity table.
3. Add AI chat with tool trace and report preview.

**Files:** `frontend/src/{pages,components,maps,services,styles}`

**Done when**
- [ ] All layers toggle on the map
- [ ] Clicking a feature shows source/date/confidence
- [ ] Report preview populates from backend

---

## Day 10 — Integration
**Goal:** one clean end-to-end run.

**Do this:** connect every stage; add loading/error/data-quality states; cache downloads; record provenance.

**Done when**
- [ ] Configure → run → dashboard → report works without manual steps
- [ ] Failures show helpful messages (no fake progress)
- [ ] `run_id` ties all artifacts together

---

## Day 11 — Validation (EMSR927)
**Goal:** independent comparison, done *after* your own results.

**Do this:** compare flood overlap, building exposure, road intersections, cut-off settlements. Explain differences (resolution, timing, method).

**Done when**
- [ ] Comparison document/table produced
- [ ] EMSR927 was **never** used as input
- [ ] Differences explained honestly

---

## Day 12 — Report & Multilingual
**Goal:** shareable one-page report, English + Nepali.

**Do this:** dynamic report template; bundle a Devanagari font; PDF export.

**Done when**
- [ ] Report numbers come from the DB, not hand-typed
- [ ] Nepali renders correctly
- [ ] Limitations stated on the page

---

## Day 13 — Testing & Polish
**Goal:** it doesn't break in front of judges.

**Do this:** unit + integration + e2e tests; test an **unseen** AOI; data-provenance audit; UI cleanup.

**Done when**
- [ ] `pytest -q` passes
- [ ] Unseen-area run completes
- [ ] No hard-coded stats anywhere

---

## Day 14 — Submission
**Goal:** ship.

**Do this:** README + install steps; six-page technical report; one-page situation report; 3-minute demo video; data attribution; repo cleanup; **push to GitHub**.

**Required attribution (exact):**
- Satellite: *"Contains modified Copernicus Sentinel data 2026."*
- Elevation: *"Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved."*
- OSM: *"© OpenStreetMap contributors."*
- Datasets: cite Kuro Siwo (Bountos et al., 2024) and Sen1Floods11.

**Done when**
- [ ] All 17 tracker items in the submission checklist are true
- [ ] Repo pushed and public
- [ ] Demo recorded

---

## Compressed 3-Day Track

| Day | Deliverable |
|---|---|
| 1 | Running map + before/after change detection (labelled demo data if needed) |
| 2 | Infrastructure overlay + connectivity graph + cut-off list |
| 3 | Agentic report + polished dashboard + demo video + push |

Prioritise: **flood mapping (30%) → AI component (25%) → cut-off analysis (20%) → report/Q&A/limits (15%) → dashboard (10%)**.

---

## Daily Habit (10 minutes)
- Morning: pick the day's "Done when" box.
- Evening: commit + push, note one blocker, write tomorrow's first task.
