import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import "./App.css";

const API = "http://localhost:8000";

export default function App() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState("checking...");

  // 1. Check that the backend is alive
  useEffect(() => {
    fetch(`${API}/api/health`)
      .then((r) => r.json())
      .then((d) => setStatus(d.status))
      .catch(() => setStatus("backend offline"));
  }, []);

  // 2. Create the map and load the sample layer
  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
    style: {
  version: 8,
  sources: {
    base: {
      type: "raster",
      tiles: [
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
],
attribution: "Tiles © Esri",
    },
  },
  layers: [{ id: "base", type: "raster", source: "base" }],
},
     center: [85.375, 28.17],
zoom: 11,
    });

    map.addControl(new maplibregl.NavigationControl());

    map.on("load", async () => {
      const res = await fetch(`${API}/api/sample-flood`);
      const data = await res.json();

      map.addSource("flood", { type: "geojson", data });
      map.addLayer({
        id: "flood-fill",
        type: "fill",
        source: "flood",
        paint: { "fill-color": "#22d3ee", "fill-opacity": 0.5 },
      });
      map.addLayer({
        id: "flood-line",
        type: "line",
        source: "flood",
        paint: { "line-color": "#22d3ee", "line-width": 2 },
      });
    });

    return () => map.remove();
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <strong>SATRA</strong>
        <span>From Space to Safety</span>
        <span className="status">Backend: {status}</span>
      </header>
      <div ref={mapContainer} className="map" />
      <div className="badge">SAMPLE DATA - not a real analysis</div>
    </div>
  );
}