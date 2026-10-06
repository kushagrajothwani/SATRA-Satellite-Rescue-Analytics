-- SATRA geospatial schema (PostgreSQL + PostGIS)
-- Dev/demo may use SQLite + SpatiaLite or file-based GeoJSON; this is the
-- production target described in docs/02_ARCHITECTURE.md.

CREATE EXTENSION IF NOT EXISTS postgis;

-- Provenance guard: only ALLOWED_INPUT may enter training/inference.
CREATE TYPE source_class AS ENUM ('ALLOWED_INPUT', 'VALIDATION_ONLY');

CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('coordinator','analyst','planner','researcher')),
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE areas_of_interest (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL,
    geom    GEOMETRY(Polygon, 4326) NOT NULL,
    bbox    DOUBLE PRECISION[4]
);
CREATE INDEX idx_aoi_geom ON areas_of_interest USING GIST (geom);

CREATE TABLE disaster_events (
    id             SERIAL PRIMARY KEY,
    name           TEXT NOT NULL,
    event_type     TEXT NOT NULL DEFAULT 'flood',
    disaster_date  DATE NOT NULL,
    aoi_id         INTEGER REFERENCES areas_of_interest(id)
);

CREATE TABLE satellite_observations (
    id              SERIAL PRIMARY KEY,
    aoi_id          INTEGER REFERENCES areas_of_interest(id),
    sensor          TEXT NOT NULL,           -- SENTINEL-1 / SENTINEL-2
    product_id      TEXT NOT NULL,
    acquired_at     TIMESTAMPTZ NOT NULL,
    orbit_direction TEXT,
    rel_orbit       INTEGER,
    polarisation    TEXT,
    cloud_cover     REAL,
    role            TEXT CHECK (role IN ('pre','post')),
    source_class    source_class NOT NULL DEFAULT 'ALLOWED_INPUT'
);
CREATE INDEX idx_obs_aoi ON satellite_observations (aoi_id, role);

CREATE TABLE analysis_runs (
    id             SERIAL PRIMARY KEY,
    event_id       INTEGER REFERENCES disaster_events(id),
    status         TEXT NOT NULL DEFAULT 'queued',
    started_at     TIMESTAMPTZ DEFAULT now(),
    finished_at    TIMESTAMPTZ,
    model_version  TEXT,
    params         JSONB
);

CREATE TABLE flood_zones (
    id          SERIAL PRIMARY KEY,
    run_id      INTEGER REFERENCES analysis_runs(id) ON DELETE CASCADE,
    class       SMALLINT NOT NULL,            -- 1 water/flood, 2 uncertain change
    prob_mean   REAL,
    confidence  TEXT,
    geom        GEOMETRY(MultiPolygon, 4326) NOT NULL
);
CREATE INDEX idx_flood_geom ON flood_zones USING GIST (geom);

CREATE TABLE infrastructure (
    id             SERIAL PRIMARY KEY,
    run_id         INTEGER REFERENCES analysis_runs(id) ON DELETE CASCADE,
    osm_id         TEXT,
    feature_type   TEXT NOT NULL,            -- building / bridge / hospital
    exposure_class TEXT NOT NULL,
    confidence     TEXT,
    geom           GEOMETRY(Geometry, 4326) NOT NULL
);
CREATE INDEX idx_infra_geom ON infrastructure USING GIST (geom);

CREATE TABLE road_segments (
    id            SERIAL PRIMARY KEY,
    run_id        INTEGER REFERENCES analysis_runs(id) ON DELETE CASCADE,
    osm_id        TEXT,
    highway       TEXT,
    hazard_status TEXT CHECK (hazard_status IN ('passable','blocked','uncertain')),
    geom          GEOMETRY(LineString, 4326) NOT NULL
);
CREATE INDEX idx_roads_geom ON road_segments USING GIST (geom);

CREATE TABLE settlements (
    id              SERIAL PRIMARY KEY,
    aoi_id          INTEGER REFERENCES areas_of_interest(id),
    osm_id          TEXT,
    name            TEXT,
    population_est  INTEGER,
    geom            GEOMETRY(Point, 4326) NOT NULL
);
CREATE INDEX idx_settle_geom ON settlements USING GIST (geom);

CREATE TABLE connectivity_results (
    id                SERIAL PRIMARY KEY,
    run_id            INTEGER REFERENCES analysis_runs(id) ON DELETE CASCADE,
    settlement_id     INTEGER REFERENCES settlements(id),
    nearest_hospital  TEXT,
    status            TEXT NOT NULL,
    alt_route_geom    GEOMETRY(LineString, 4326),
    confidence        TEXT
);

CREATE TABLE model_predictions (
    id               SERIAL PRIMARY KEY,
    run_id           INTEGER REFERENCES analysis_runs(id) ON DELETE CASCADE,
    tile_id          TEXT,
    model_version    TEXT,
    prob_raster_path TEXT,
    metrics          JSONB
);

CREATE TABLE agent_logs (
    id          SERIAL PRIMARY KEY,
    run_id      INTEGER REFERENCES analysis_runs(id) ON DELETE CASCADE,
    agent       TEXT NOT NULL,
    tool_called TEXT,
    input       JSONB,
    output      JSONB,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE situation_reports (
    id          SERIAL PRIMARY KEY,
    run_id      INTEGER REFERENCES analysis_runs(id) ON DELETE CASCADE,
    language    TEXT NOT NULL DEFAULT 'en',
    body_md     TEXT NOT NULL,
    pdf_path    TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);
