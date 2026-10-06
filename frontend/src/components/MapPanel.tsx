import { useEffect, useRef } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Connectivity, FloodZones, Infrastructure } from "../services/api";

type Props = {
  flood: FloodZones | null;
  infra: Infrastructure | null;
  conn: Connectivity | null;
  visible: Record<string, boolean>;
  selectedSettlement: string | null;
  onSelectSettlement: (id: string) => void;
};
const STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    base: {
      type: "raster",
      tiles: [
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      ],
      tileSize: 256,
      attribution: "Tiles © Esri · © OpenStreetMap contributors",
    },
  },
  layers: [{ id: "base", type: "raster", source: "base" }],
};

// Layer ids we add, in draw order (bottom -> top).
const LAYER_ORDER = [
  "flood-moderate",
  "flood-high",
  "anomaly",
  "roads",
  "buildings",
  "bridges",
  "hospitals",
  "settlements",
  "isolated",
];

export default function MapPanel({
  flood,
  infra,
  conn,
  visible,
  selectedSettlement,
  onSelectSettlement,
}: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  // Create the map once.
  useEffect(() => {
    if (!container.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: container.current,
      style: STYLE,
      center: [85.36, 28.17],
      zoom: 11,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-left");
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Add/refresh data layers whenever inputs change.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const apply = () => {
      const addGeo = (
        id: string,
        data: unknown,
        type: "fill" | "line" | "circle",
        paint: maplibregl.LayerSpecification["paint"],
        extra: Record<string, unknown> = {},
      ) => {
        const srcId = `${id}-src`;
        if (map.getLayer(id)) map.removeLayer(id);
        if (map.getSource(srcId)) map.removeSource(srcId);
        map.addSource(srcId, { type: "geojson", data: data as never });
        map.addLayer({
          id,
          type,
          source: srcId,
          paint,
          ...extra,
        } as maplibregl.LayerSpecification);
      };

      if (flood) {
        addGeo(
          "flood-moderate",
          flood.moderate_confidence,
          "fill",
          { "fill-color": "#38bdf8", "fill-opacity": 0.35 },
        );
        addGeo(
          "flood-high",
          flood.high_confidence,
          "fill",
          { "fill-color": "#ef4444", "fill-opacity": 0.45 },
        );
        addGeo(
          "anomaly",
          flood.uncertain_change,
          "fill",
          { "fill-color": "#f59e0b", "fill-opacity": 0.3 },
        );
      }
      if (infra) {
        addGeo("roads", infra.roads, "line", {
          "line-color": [
            "match",
            ["get", "exposure"],
            "high_priority_inspection",
            "#ef4444",
            "potentially_exposed",
            "#f59e0b",
            "#93c5fd",
          ],
          "line-width": 2,
        });
        addGeo("buildings", infra.buildings, "circle", {
          "circle-radius": 3.5,
          "circle-color": [
            "match",
            ["get", "exposure"],
            "high_priority_inspection",
            "#ef4444",
            "potentially_exposed",
            "#f59e0b",
            "#e5e7eb",
          ],
        });
        addGeo("bridges", infra.bridges, "circle", {
          "circle-radius": 6,
          "circle-color": "#a78bfa",
          "circle-stroke-color": "#0b1220",
          "circle-stroke-width": 1.5,
        });
        addGeo("hospitals", infra.hospitals, "circle", {
          "circle-radius": 7,
          "circle-color": "#22c55e",
          "circle-stroke-color": "#0b1220",
          "circle-stroke-width": 2,
        });
      }
      if (conn) {
        const all = {
          type: "FeatureCollection",
          features: conn.settlements.map((s) => ({
            type: "Feature",
            properties: { id: s.settlement_id, name: s.name, status: s.status },
            geometry: { type: "Point", coordinates: [s.lon, s.lat] },
          })),
        };
        addGeo("settlements", all, "circle", {
          "circle-radius": 5,
          "circle-color": [
            "match",
            ["get", "status"],
            "connected",
            "#22c55e",
            "no_modelled_connection",
            "#ef4444",
            "#f59e0b",
            "#f59e0b",
          ],
          "circle-stroke-color": "#0b1220",
          "circle-stroke-width": 1.5,
        });
      }

      // Re-apply visibility.
      LAYER_ORDER.forEach((id) => {
        if (map.getLayer(id)) {
          map.setLayoutProperty(id, "visibility", visible[id] ? "visible" : "none");
        }
      });
    };

    if (map.isStyleLoaded()) apply();
    else map.once("load", apply);
  }, [flood, infra, conn, visible]);

  // Centre the map on the selected settlement.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedSettlement || !conn) return;
    const s = conn.settlements.find((x) => x.settlement_id === selectedSettlement);
    if (s) map.flyTo({ center: [s.lon, s.lat], zoom: 13 });
  }, [selectedSettlement, conn]);

  // Settlement click -> detail.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const handler = (e: maplibregl.MapLayerMouseEvent) => {
      const f = e.features?.[0];
      if (f && f.properties?.id) onSelectSettlement(String(f.properties.id));
    };
    map.on("click", "settlements", handler);
    map.on("mouseenter", "settlements", () => (map.getCanvas().style.cursor = "pointer"));
    map.on("mouseleave", "settlements", () => (map.getCanvas().style.cursor = ""));
    return () => {
      map.off("click", "settlements", handler);
    };
  }, [onSelectSettlement]);

  return <div ref={container} className="map" />;
}
