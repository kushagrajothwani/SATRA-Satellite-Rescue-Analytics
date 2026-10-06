# SATRA — Product Requirements Document (PRD)

**Project:** SATRA — Satellite-Assisted Terrain & Rescue Analytics
**Tagline:** From Space to Safety.
**Event:** Multimodal AI Hackathon 2026 · Track B — Mapping Flood Damage from Space
**Document owner:** Product / Geospatial AI
**Status:** v1.0 (hackathon baseline)
**Related docs:** `02_ARCHITECTURE.md`, `03_IMPLEMENTATION.md`, `04_DESIGN.md`, `05_DAY_BY_DAY_PLAN.md`

---

## 1. Executive Summary

When roads, bridges and phone lines are gone, rescuers still need to know **where the damage is** and **who is cut off**. SATRA is an AI-powered disaster-intelligence platform that turns satellite observations into evidence-based rescue intelligence.

SATRA ingests Sentinel-1 SAR and Sentinel-2 optical imagery for a user-selected area and disaster date, detects flooded and changed terrain with a machine-learning segmentation model, overlays pre-event OpenStreetMap infrastructure, and then runs a **road-network connectivity analysis** to find settlements that have no remaining *modelled* road connection to a town or hospital. An **agentic AI layer** answers rescue-oriented questions and produces a one-page situation report — but every number it states must come from a verified geospatial tool, never from the language model's imagination.

**One-line positioning:** *From satellite observation to settlement-level accessibility intelligence through a multimodal, evidence-grounded agentic AI pipeline.*

---

## 2. Problem Statement

A sudden glacial or monsoon flood in the Himalayas destroys roads, bridges and communications. Rescue teams face three life-critical questions:

1. **WHERE is the damage?** — detect water expansion, debris and changed terrain.
2. **WHAT infrastructure is affected?** — buildings, roads, bridges, critical facilities.
3. **WHO is cut off?** — settlements that can no longer be reached from a town or hospital.

Existing tools are either (a) raw imagery viewers with no analysis, or (b) static official damage maps that arrive too late and cover too broad an area. SATRA closes the gap between *observation* and *operational decision*.

---

## 3. Product Vision

> **Theme:** When infrastructure fails, intelligence must still reach the ground.

SATRA is not a flood-detection dashboard. It is a **geospatial intelligence + machine learning + agentic AI** system in which:

| Technology | Responsibility |
|---|---|
| Remote sensing | Observe the Earth with satellites |
| Machine learning | Detect flooded / changed regions from SAR (+ optical) |
| Geospatial intelligence | Analyse infrastructure exposure and accessibility |
| Agentic AI | Coordinate tools and produce evidence-grounded reports |

**Core design principle:** *The AI agent must never invent disaster statistics. Every numerical statement is retrieved from a deterministic geospatial tool.*

---

## 4. Objectives & Success Metrics

### 4.1 Product objectives
- **O1** — Produce a flood/hazard map for a judge-selected AOI and date from raw satellite data.
- **O2** — Estimate potentially exposed buildings, roads, bridges and hospitals.
- **O3** — Identify settlements with *no remaining modelled road connection* to a hospital/town.
- **O4** — Answer rescue questions in natural language with traceable evidence.
- **O5** — Generate a one-page situation report (English/Nepali).

### 4.2 Success metrics (proposed — require benchmarking, not guarantees)
| Metric | Target (assumption) | Notes |
|---|---|---|
| Flood segmentation IoU on held-out events | reported, not promised | never fabricate |
| Geographic generalisation | evaluated on unseen Himalayan scenes | event-level split |
| End-to-end run (small AOI) | minutes, cached | depends on data volume |
| Evidence grounding | 100% of numbers traceable to a tool | hard requirement |
| Report generated | 1 page, source-cited | hard requirement |

> Targets above are **assumptions to validate**, not commitments.

---

## 5. Target Users (Personas)

**P1 — Emergency Response Coordinator** (district disaster cell)
Needs a fast, trustworthy overview of where to send teams. Interacts with: dashboard summary, priority list, situation report.

**P2 — Disaster Management Analyst**
Needs to inspect layers, data provenance and uncertainty. Interacts with: layer controls, evidence panels, exports.

**P3 — Search & Rescue Planner**
Needs to know which settlements lost hospital access. Interacts with: connectivity screen, alternative routes.

**P4 — Geospatial Researcher / Evaluator**
Needs reproducibility and validation vs. Copernicus EMSR927. Interacts with: provenance, metrics, comparison view.

---

## 6. User Stories & Acceptance Criteria

**US-1 — Configure an analysis**
*As a coordinator, I want to enter a location and disaster date so that the system analyses the right area.*
- **AC:** AOI geometry + disaster date + pre/post observation dates accepted; system reports whether observations exist.

**US-2 — See before/after satellite imagery**
*As an analyst, I want a before/after comparison so I can visually verify change.*
- **AC:** Pre and post rasters displayed with acquisition dates and orbit metadata.

**US-3 — Detect flood extent**
*As a coordinator, I want a flood map so I know where water expanded.*
- **AC:** Flood probability raster + GeoJSON polygons produced; permanent water excluded; confidence shown; debris shown separately as "uncertain change".

**US-4 — Assess infrastructure exposure**
*As an analyst, I want to know which buildings/roads/bridges intersect the hazard.*
- **AC:** Each feature classified as Potentially exposed / High-priority inspection / Uncertain / Outside; results exportable.

**US-5 — Identify cut-off settlements**
*As an SAR planner, I want settlements with no modelled hospital route.*
- **AC:** Road graph built; hazard edges disabled; connectivity computed; result distinguishes Connected / No modelled connection / Insufficient data / Uncertain.

**US-6 — Grounded AI answers**
*As a coordinator, I want to ask questions and trust the numbers.*
- **AC:** Answer includes tool-call trace and sources; numbers match tool output exactly.

**US-7 — Situation report**
*As a coordinator, I want a one-page report to share.*
- **AC:** Report populates dynamically from verified results; English/Nepali; PDF export; limitations stated.

---

## 7. Functional Requirements

### A. Disaster Configuration
- FR-A1: Enter location by name or coordinates + bounding box / AOI polygon.
- FR-A2: Enter disaster date and pre/post observation windows.
- FR-A3: Validate satellite availability for the requested period; offer nearest usable acquisitions.
- FR-A4: Configure analysis resolution / tiling.

### B. Satellite Data Ingestion
- FR-B1: Retrieve Sentinel-1 GRD (VV/VH) via Copernicus Data Space.
- FR-B2: Retrieve Sentinel-2 L2A optical when cloud-free.
- FR-B3: Record acquisition timestamps, orbit direction, relative orbit, polarisation.
- FR-B4: Preprocess (calibration, terrain correction, speckle filtering, tiling, reprojection).

### C. Flood Intelligence
- FR-C1: Pre/post change detection (SAR backscatter decrease / threshold + ML).
- FR-C2: U-Net flood segmentation (classes: background / water-flood / uncertain change).
- FR-C3: Flood probability raster.
- FR-C4: Flood extent GeoJSON polygons.
- FR-C5: Permanent-water exclusion using pre-event water.
- FR-C6: Confidence / uncertainty visualisation.

### D. Infrastructure Assessment
- FR-D1: Historical OSM snapshot via ohsome API (roads, buildings, bridges, hospitals).
- FR-D2: Spatial intersection of infrastructure with hazard layers (with uncertainty buffers).
- FR-D3: Exposure classification per feature.
- FR-D4: Export GeoJSON + attribute table.

### E. Settlement Connectivity
- FR-E1: Build road graph G=(V,E) from OSM road network.
- FR-E2: Assign each edge a risk status from hazard intersection.
- FR-E3: Build a *scenario passability graph* (never mutate the baseline).
- FR-E4: Connectivity analysis from each settlement to nearest town/hospital.
- FR-E5: Determine alternative routes where they exist.
- FR-E6: Classify results with confidence.

### F. Multimodal ML
- FR-F1: SAR segmentation model (U-Net baseline).
- FR-F2: Optional SAR+optical fusion when aligned optical exists.
- FR-F3: Confidence estimation.
- FR-F4: Evaluation (IoU, precision, recall, F1).
- FR-F5: Geographic/event-level train/val/test generalisation testing.

### G. Agentic AI
- FR-G1: Mission Planner, Satellite Intelligence, Damage Assessment, Connectivity, Situation Report agents.
- FR-G2: Deterministic tools for all numeric analysis.
- FR-G3: Structured (Pydantic) agent state and outputs.
- FR-G4: Tool-call logging / provenance.
- FR-G5: Grounded report generation (EN/NE).
- FR-G6: No arbitrary shell/DB access from agents.

### H. Dashboard
- FR-H1: Interactive MapLibre map.
- FR-H2: Before/after slider.
- FR-H3: Layer toggle groups (flood, uncertain change, roads, buildings, bridges, hospitals, settlements, cut-off).
- FR-H4: Statistics and charts.
- FR-H5: Isolation / priority view.
- FR-H6: AI chat interface with evidence panel.
- FR-H7: Data-quality banner.

### I. Situation Report
- FR-I1: Auto-generate one-page report.
- FR-I2: English and Nepali.
- FR-I3: Only verified numbers.
- FR-I4: PDF export.

---

## 8. Non-Functional Requirements

- **NFR-1 Accuracy:** Outputs are *exposure assessments* and *modelled connectivity*, never claims of confirmed damage.
- **NFR-2 Reproducibility:** Every result stores inputs, dates, model version, parameters, confidence.
- **NFR-3 Provenance:** Validation-only datasets (EMSR927, UNOSAT, published maps, post-event OSM) must be technically prevented from entering inference/training inputs.
- **NFR-4 Reliability:** Graceful degradation when imagery/credentials missing; no fabricated progress.
- **NFR-5 Performance:** Cache imagery; tile AOI; separate processing from rendering.
- **NFR-6 Explainability:** Confidence and limitations on every product.
- **NFR-7 Security:** API keys in `.env`; validated inputs; restricted agent tools.
- **NFR-8 Accessibility:** Readable dark UI, colour + text labels (not colour alone), keyboard nav for panels.
- **NFR-9 Usability:** Beginner-friendly dashboard; ≤3 clicks from landing to analysis.

---

## 9. System Scope

**In scope (this build):** AOI/date config, Sentinel-1 SAR retrieval, change detection + U-Net segmentation, flood polygons, historical OSM extraction, infrastructure exposure, road-graph connectivity, agentic Q&A, one-page report, interactive dashboard, EMSR927 comparison view.

**Out of scope:** Real-time continuous monitoring; flood depth/velocity simulation; identifying individual missing persons; operational emergency dispatch; physical sensor integration.

### 9.1 Explicit limitations
- Sentinel-1/2 are **discrete acquisitions**, not live video; the system cannot predict a slope collapse before it happens.
- A DEM drainage trace is **not** a physical flood simulation.
- "No mapped route" ≠ physically inaccessible; it means no usable connection was found under modelled assumptions.
- Mountain shadow, turbid water and permanent rivers can cause false positives; SAR is primary, optical secondary.

---

## 10. MVP vs Future Scope

**MVP (must-have for submission):**
- Satellite retrieval (S1 SAR) + pre/post comparison
- SAR change detection + U-Net flood segmentation
- Historical OSM infrastructure overlay
- Road-graph connectivity → cut-off settlements
- Interactive map + basic metrics
- Evidence-grounded agent report
- Data attribution

**Advanced (stretch):**
- SAR+optical multimodal fusion
- Debris/anomaly classification with validation
- Downstream flood-path tracing (DEM)
- Multilingual (Nepali) assistant
- Uncertainty calibration
- Rescue Priority Intelligence Engine

---

## 11. Hackathon Constraints (mandatory)

- **Allowed inputs:** Sentinel-1, Sentinel-2, Copernicus DEM, pre-event OSM, approved training datasets (Kuro Siwo, Sen1Floods11).
- **Forbidden as inputs:** Copernicus EMS, UNOSAT, published damage maps, post-event OSM edits.
- **Validation only:** EMSR927 comparison after independent results.
- System must work for **judge-selected locations and dates**.
- Must communicate revisit limitations.
- Must never claim to identify missing people.
- Must distinguish detected exposure from confirmed structural damage.

---

## 12. User Journey (high level)

1. Open SATRA → landing.
2. Configure AOI + disaster date → system validates observations.
3. Run analysis → progress states.
4. View dashboard: before/after, flood, infrastructure, cut-off settlements.
5. Open Connectivity screen → inspect settlements + alternative routes.
6. Ask the AI assistant a rescue question → evidence-backed answer.
7. Export one-page situation report.
8. (Evaluator) Compare against EMSR927 in the validation view.

---

## 13. Risks & Assumptions

| Risk | Mitigation |
|---|---|
| Cloud cover blocks optical | Make SAR primary |
| Different SAR orbit geometry | Compare same-track (~12-day) observations |
| Mountain shadows | Terrain-aware uncertainty |
| Permanent rivers flagged as flood | Pre-event water exclusion |
| Debris confused with water | Separate "uncertain change" class |
| OSM missing roads | Show data completeness + uncertainty |
| Model fails in Himalayas | Event-level unseen-scene evaluation |
| No image for requested date | List nearest usable acquisitions |
| LLM invents statistics | Force all numbers through verified tools |
| Slow processing | Cache + tile + async jobs |
| DEM error in mountains | Present drainage as approximation |

**Assumption:** judges accept a reproducible prototype with clearly-labelled sample/demo data where live data is unavailable.

---

## 14. Acceptance Criteria (submission-level)

- [ ] Four documents present and consistent.
- [ ] End-to-end pipeline runs for one AOI/date and produces all layers.
- [ ] Flood outputs exported as geospatial layers with confidence.
- [ ] Historical OSM snapshot used (not post-event).
- [ ] Connectivity analysis produces a cut-off settlement list with confidence.
- [ ] Agent answers are 100% tool-grounded.
- [ ] One-page report populates from real results.
- [ ] EMSR927 comparison performed independently.
- [ ] Limitations, attribution and citations included.

---

## 15. Future Roadmap

1. **v1.0 (hackathon):** SAR flood + connectivity + grounded agent report.
2. **v1.1:** Optical fusion, debris validation, Nepali assistant.
3. **v1.2:** DEM flood-path tracing + Rescue Priority Intelligence Engine.
4. **v2.0:** Multi-hazard (earthquake, landslide), time-series change, multi-user operations, PostGIS/cloud deployment.
