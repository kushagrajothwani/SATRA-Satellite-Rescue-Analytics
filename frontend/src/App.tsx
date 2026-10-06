import { useEffect, useMemo, useState } from "react";
import "./App.css";
import MapPanel from "./components/MapPanel";
import {
  api,
  type AgentAnswer,
  type AnalysisDetail,
  type Connectivity,
  type FloodZones,
  type Infrastructure,
  type Settlement,
} from "./services/api";

const LAYERS: Array<{ id: string; label: string; color: string }> = [
  { id: "flood-high", label: "Flood (high confidence)", color: "#ef4444" },
  { id: "flood-moderate", label: "Flood (moderate)", color: "#38bdf8" },
  { id: "anomaly", label: "Uncertain change (not debris)", color: "#f59e0b" },
  { id: "roads", label: "Roads", color: "#93c5fd" },
  { id: "buildings", label: "Buildings", color: "#e5e7eb" },
  { id: "bridges", label: "Bridges", color: "#a78bfa" },
  { id: "hospitals", label: "Hospitals", color: "#22c55e" },
  { id: "settlements", label: "Settlements", color: "#22d3ee" },
];

const DEFAULT_VISIBILITY: Record<string, boolean> = Object.fromEntries(
  LAYERS.map((l) => [l.id, true]),
);

const STATUS_META: Record<string, { label: string; cls: string }> = {
  connected: { label: "Connected", cls: "ok" },
  no_modelled_connection: { label: "No modelled route", cls: "danger" },
  uncertain: { label: "Uncertain", cls: "warn" },
  insufficient_road_data: { label: "Insufficient data", cls: "muted" },
};

const SUGGESTIONS = [
  "Which settlements may be disconnected from hospitals?",
  "Show roads intersecting high-confidence flood zones.",
  "Which buildings are potentially exposed?",
  "Generate a one-page disaster situation report.",
  "Explain the uncertainty in the detected flood boundary.",
];

export default function App() {
  const [health, setHealth] = useState<{ status: string; copernicus_configured: boolean } | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [tab, setTab] = useState<"map" | "report">("map");

  const [detail, setDetail] = useState<AnalysisDetail | null>(null);
  const [flood, setFlood] = useState<FloodZones | null>(null);
  const [infra, setInfra] = useState<Infrastructure | null>(null);
  const [conn, setConn] = useState<Connectivity | null>(null);

  const [visible, setVisible] = useState(DEFAULT_VISIBILITY);
  const [selected, setSelected] = useState<string | null>(null);

  const [messages, setMessages] = useState<Array<{ role: "user" | "bot"; text: string; trace?: string[] }>>([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);

  const [report, setReport] = useState<string>("");
  const [loadingReport, setLoadingReport] = useState(false);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ status: "offline", copernicus_configured: false }));
  }, []);

  async function startAnalysis() {
    setStarting(true);
    setError(null);
    try {
      const created = await api.createAnalysis({
        aoi: { name: "Syapru Besi", bbox: [85.2, 28.0, 85.6, 28.4] },
        disaster_date: "2026-08-26",
        demo_mode: true,
      });
      setRunId(created.run_id);
      const [d, f, i, c] = await Promise.all([
        api.detail(created.run_id),
        api.flood(created.run_id),
        api.infrastructure(created.run_id),
        api.connectivity(created.run_id),
      ]);
      setDetail(d);
      setFlood(f);
      setInfra(i);
      setConn(c);
    } catch (e) {
      setError(String(e));
    } finally {
      setStarting(false);
    }
  }

  async function ask(q: string) {
    if (!runId || !q.trim()) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setQuestion("");
    setAsking(true);
    try {
      const ans: AgentAnswer = await api.ask(runId, q);
      setMessages((m) => [
        ...m,
        { role: "bot", text: ans.answer, trace: ans.evidence.map((e) => e.tool) },
      ]);
    } catch (e) {
      setMessages((m) => [...m, { role: "bot", text: `Error: ${e}` }]);
    } finally {
      setAsking(false);
    }
  }

  async function loadReport() {
    if (!runId) return;
    setLoadingReport(true);
    try {
      const r = await api.report(runId);
      setReport(r.body_md);
    } catch (e) {
      setReport(`Error: ${e}`);
    } finally {
      setLoadingReport(false);
    }
  }

  const selectedSettlement: Settlement | undefined = useMemo(
    () => conn?.settlements.find((s) => s.settlement_id === selected),
    [conn, selected],
  );

  const summary = detail?.summary;
  const demoLabel = detail?.demo_mode ? "SYNTHETIC DEMO DATA — not a real damage assessment" : "";

  return (
    <div className="app">
      <header className="topbar">
        <span className="brand">SATRA</span>
        <span className="tag">From Space to Safety</span>
        <div className="right">
          <span>
            <span className={`dot ${health?.status === "ok" ? "ok" : "bad"}`} />
            Backend: {health?.status ?? "…"}
          </span>
          <span className="small">
            Copernicus: {health?.copernicus_configured ? "configured" : "demo data"}
          </span>
          {runId && <span className="badge info">{runId}</span>}
        </div>
      </header>

      <div className="layout">
        {/* ---------------- LEFT ---------------- */}
        <aside className="panel left">
          <div className="card">
            <h3>Disaster configuration</h3>
            <div className="solid small" style={{ marginBottom: 8 }}>
              AOI: Syapru Besi (85.20–85.60, 28.00–28.40)
              <br />
              Disaster date: 2026-08-26 · Sensor: Sentinel-1
            </div>
            <button className="btn" style={{ width: "100%" }} disabled={starting} onClick={startAnalysis}>
              {starting ? "Running analysis…" : runId ? "Re-run analysis" : "Run analysis"}
            </button>
            {error && <div className="error" style={{ marginTop: 8 }}>{error}</div>}
          </div>

          <div className="card">
            <h3>Layers</h3>
            {LAYERS.map((l) => (
              <label className="row" key={l.id}>
                <input
                  type="checkbox"
                  style={{ width: "auto" }}
                  checked={!!visible[l.id]}
                  onChange={() => setVisible((v) => ({ ...v, [l.id]: !v[l.id] }))}
                />
                <span className="swatch" style={{ background: l.color }} />
                {l.label}
              </label>
            ))}
          </div>

          <div className="card">
            <h3>Data sources</h3>
            <div className="small">
              Sentinel-1 SAR (primary) · Sentinel-2 optical (when cloud-free) · historical OSM
              (ohsome, pre-event) · Copernicus DEM.
              <br />
              <br />
              EMSR927 / UNOSAT / published maps are used for <b>validation only</b>.
            </div>
          </div>
        </aside>

        {/* ---------------- CENTER ---------------- */}
        <main className="map-wrap">
          {tab === "map" ? (
            <MapPanel
              flood={flood}
              infra={infra}
              conn={conn}
              visible={visible}
              selectedSettlement={selected}
              onSelectSettlement={setSelected}
            />
          ) : (
            <div className="panel" style={{ height: "100%" }}>
              <div className="card">
                <h3>Situation report</h3>
                {!report && (
                  <button className="btn" onClick={loadReport} disabled={!runId || loadingReport}>
                    {loadingReport ? "Generating…" : "Generate report"}
                  </button>
                )}
                {report && (
                  <div className="report" dangerouslySetInnerHTML={{ __html: mdToHtml(report) }} />
                )}
              </div>
            </div>
          )}

          <div className="toolbar">
            <button className="btn ghost" onClick={() => setTab("map")}>
              Map
            </button>
            <button className="btn ghost" onClick={() => setTab("report")}>
              Report
            </button>
          </div>

          <div className="legend">
            <div className="item"><span className="swatch" style={{ background: "#ef4444" }} /> High-priority flood / blocked</div>
            <div className="item"><span className="swatch" style={{ background: "#f59e0b" }} /> Uncertain / moderate</div>
            <div className="item"><span className="swatch" style={{ background: "#22c55e" }} /> Connected / hospital</div>
            <div className="item small">Green = no concern in analysed layers — not a safety guarantee.</div>
          </div>

          {demoLabel && <div className="badge warn" style={{ position: "absolute", top: 12, left: 12, zIndex: 4 }}>{demoLabel}</div>}

          {starting && <div className="loading">Running satellite + geospatial pipeline…</div>}
        </main>

        {/* ---------------- RIGHT ---------------- */}
        <aside className="panel right">
          {!runId && (
            <div className="card">
              <h3>Getting started</h3>
              <p className="small">
                Run an analysis to see flood extents, infrastructure exposure and cut-off
                settlements for the selected AOI.
              </p>
            </div>
          )}

          {summary && (
            <div className="card">
              <h3>Detected impact</h3>
              <div className="metric"><span className="lbl">Settlements cut off</span><span className="val" style={{ color: "#fca5a5" }}>{summary.disconnected_settlements}</span></div>
              <div className="metric"><span className="lbl">Buildings exposed</span><span className="val">{countExposed(summary.buildings)}</span></div>
              <div className="metric"><span className="lbl">Roads affected</span><span className="val">{countExposed(summary.roads)}</span></div>
              <div className="metric"><span className="lbl">Bridges exposed</span><span className="val">{countExposed(summary.bridges)}</span></div>
            </div>
          )}

          {selectedSettlement && (
            <div className="card">
              <h3>Selected settlement</h3>
              <div style={{ fontWeight: 700, marginBottom: 4 }}>{selectedSettlement.name}</div>
              <div className="small" style={{ marginBottom: 6 }}>
                Pop. est. {selectedSettlement.pop_est}
              </div>
              <span className={`badge ${STATUS_META[selectedSettlement.status]?.cls ?? "muted"}`}>
                {STATUS_META[selectedSettlement.status]?.label ?? selectedSettlement.status}
              </span>
              <div className="small" style={{ marginTop: 8 }}>
                Nearest hospital: {selectedSettlement.nearest_hospital ?? "—"}
                <br />
                Distance: {selectedSettlement.distance_km ?? "—"} km
                <br />
                Alternative route: {selectedSettlement.alternative_route ? "yes" : "no"}
                <br />
                Confidence: {selectedSettlement.confidence}
              </div>
              <div className="small" style={{ marginTop: 8 }}>{selectedSettlement.reason}</div>
            </div>
          )}

          {conn && (
            <div className="card">
              <h3>Settlement connectivity</h3>
              <table>
                <thead>
                  <tr><th>Name</th><th>Status</th><th>Conf.</th></tr>
                </thead>
                <tbody>
                  {conn.settlements.map((s) => (
                    <tr key={s.settlement_id} className="clickable" onClick={() => setSelected(s.settlement_id)}>
                      <td>{s.name}</td>
                      <td>
                        <span className={`badge ${STATUS_META[s.status]?.cls ?? "muted"}`}>
                          {STATUS_META[s.status]?.label ?? s.status}
                        </span>
                      </td>
                      <td className="small">{s.confidence}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="card">
            <h3>Intelligence assistant</h3>
            <div className="chat-log">
              {messages.length === 0 && (
                <div className="small">Ask a rescue question. Every number is returned by a verified tool.</div>
              )}
              {messages.map((m, i) => (
                <div key={i} className={`msg ${m.role}`}>
                  {m.text}
                  {m.trace && <div className="tooltrace">tools: {m.trace.join(", ")}</div>}
                </div>
              ))}
              {asking && <div className="msg bot">Reasoning over verified tools…</div>}
            </div>
            <div className="chips">
              {SUGGESTIONS.slice(0, 3).map((s) => (
                <span key={s} className="chip" onClick={() => ask(s)}>{s}</span>
              ))}
            </div>
            <textarea
              rows={2}
              placeholder="e.g. Which settlements are cut off?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  ask(question);
                }
              }}
              disabled={!runId || asking}
            />
            <button className="btn" style={{ width: "100%", marginTop: 6 }} disabled={!runId || asking} onClick={() => ask(question)}>
              Ask
            </button>
          </div>

          <div className="banner">
            Exposure and connectivity are modelled assessments, not confirmed damage, and never a
            claim about individuals.
          </div>
        </aside>
      </div>
    </div>
  );
}

function countExposed(m: Record<string, number>): number {
  return (m.potentially_exposed ?? 0) + (m.high_priority_inspection ?? 0);
}

// Tiny markdown -> HTML for the report (headings, bold, lists, paragraphs).
function mdToHtml(md: string): string {
  const esc = md
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return esc
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
    .replace(/^\- (.*)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/^/, "<p>")
    .replace(/$/, "</p>");
}
