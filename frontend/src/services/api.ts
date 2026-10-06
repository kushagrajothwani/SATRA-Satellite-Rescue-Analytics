// Typed API client for the SATRA backend.
export const API = "http://localhost:8000";

export type GeoJSON = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties: Record<string, unknown>;
    geometry: { type: string; coordinates: unknown };
  }>;
};

export type FloodZones = {
  meta: { label: string; source: string; note?: string };
  high_confidence: GeoJSON;
  moderate_confidence: GeoJSON;
  uncertain_change: GeoJSON;
  hazard_rings: number[][][];
};

export type LayerSummary = Record<string, number>;

export type Infrastructure = {
  meta: { label: string };
  buildings: GeoJSON;
  roads: GeoJSON;
  bridges: GeoJSON;
  hospitals: GeoJSON;
  summary: {
    buildings: LayerSummary;
    roads: LayerSummary;
    bridges: LayerSummary;
    hospitals: LayerSummary;
  };
};

export type Settlement = {
  settlement_id: string;
  name: string;
  pop_est: number;
  lon: number;
  lat: number;
  status:
    | "connected"
    | "no_modelled_connection"
    | "uncertain"
    | "insufficient_road_data";
  nearest_hospital: string | null;
  distance_km: number | null;
  alternative_route: boolean;
  confidence: string;
  reason: string;
};

export type Edge = {
  id: string;
  from: string;
  to: string;
  highway: string;
  status: "passable" | "blocked" | "uncertain";
};

export type Connectivity = {
  meta: { label: string };
  engine: string;
  settlements: Settlement[];
  disconnected_count: number;
  total_settlements: number;
  road_edges: Edge[];
  sources: string[];
};

export type AnalysisDetail = {
  run_id: string;
  status: string;
  aoi: { name?: string; bbox?: number[] };
  event_date: string;
  demo_mode: boolean;
  satellite: {
    sensors: string[];
    observation_dates: string[];
    orbit_note: string;
    label: string;
  };
  summary: {
    buildings: LayerSummary;
    roads: LayerSummary;
    bridges: LayerSummary;
    hospitals: LayerSummary;
    disconnected_settlements: number;
    total_settlements: number;
  };
  provenance: Record<string, unknown>;
};

export type AgentAnswer = {
  answer: string;
  evidence: Array<{ tool: string; result: unknown }>;
  sources: string[];
  confidence: string;
  grounded: boolean;
  engine: string;
};

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

export const api = {
  health: () => get<{ status: string; copernicus_configured: boolean }>("/api/health"),
  createAnalysis: (body: unknown) =>
    post<{ run_id: string; status: string; message: string }>("/api/analysis", body),
  detail: (id: string) => get<AnalysisDetail>(`/api/analysis/${id}`),
  flood: (id: string) => get<FloodZones>(`/api/flood-zones/${id}`),
  infrastructure: (id: string) => get<Infrastructure>(`/api/infrastructure/${id}`),
  connectivity: (id: string) => get<Connectivity>(`/api/connectivity/${id}`),
  report: (id: string, language = "en") =>
    get<{ body_md: string; numbers: Record<string, number>; sources: string[] }>(
      `/api/agent/report/${id}?language=${language}`,
    ),
  ask: (run_id: string, question: string) =>
    post<AgentAnswer>("/api/agent/query", { run_id, question }),
};
