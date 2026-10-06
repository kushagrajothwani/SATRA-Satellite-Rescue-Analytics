"""Clearly-labelled DEMO dataset for the Trishuli / Syapru Besi corridor, Nepal.

This is SYNTHETIC placeholder data used only so the end-to-end pipeline can be
demonstrated and tested offline. It is *not* a real damage assessment and must
never be presented as one. When Copernicus credentials and the real OSM/DEM
extraction are available, the same analysis functions operate on real layers.

Coordinates are approximate real settlements in the Rasuwa / Nuwakot area and
sit inside the default AOI bbox (85.20, 28.00, 85.60, 28.40).
"""
from __future__ import annotations

DEMO_LABEL = "SYNTHETIC DEMO DATA - not a real damage assessment"

TOWNS = [
    {"id": "town-syaprubesi", "name": "Syapru Besi", "lon": 85.380, "lat": 28.160},
    {"id": "town-bidur", "name": "Bidur", "lon": 85.300, "lat": 28.050},
]

HOSPITALS = [
    {"id": "hosp-syapru", "name": "Syapru Besi Health Post", "lon": 85.383, "lat": 28.157},
    {"id": "hosp-bidur", "name": "Bidur District Hospital", "lon": 85.303, "lat": 28.047},
]

# Mountain settlements; some will become isolated in the demo scenario.
SETTLEMENTS = [
    {"id": "set-001", "name": "Langtang Village", "lon": 85.430, "lat": 28.210, "pop_est": 300},
    {"id": "set-002", "name": "Thulo Syapru", "lon": 85.405, "lat": 28.180, "pop_est": 450},
    {"id": "set-003", "name": "Rasuwa Gaun", "lon": 85.340, "lat": 28.230, "pop_est": 380},
    {"id": "set-004", "name": "Dhunche", "lon": 85.290, "lat": 28.110, "pop_est": 1200},
    {"id": "set-005", "name": "Timure", "lon": 85.360, "lat": 28.290, "pop_est": 260},
    {"id": "set-006", "name": "Briddhim", "lon": 85.330, "lat": 28.150, "pop_est": 210},
    {"id": "set-007", "name": "Chilime", "lon": 85.350, "lat": 28.180, "pop_est": 340},
    {"id": "set-008", "name": "Kakani", "lon": 85.250, "lat": 28.080, "pop_est": 900},
]

# Road graph edges: (from_id, to_id, highway class). Coordinates resolved from
# node table below. The river crossing edges are the vulnerable ones.
NODES = {t["id"]: (t["lon"], t["lat"]) for t in TOWNS}
NODES.update({s["id"]: (s["lon"], s["lat"]) for s in SETTLEMENTS})
NODES.update({h["id"]: (h["lon"], h["lat"]) for h in HOSPITALS})

# Each road is a polyline (list of lon/lat) so hazard intersection is realistic.
ROADS = [
    {"id": "rd-01", "highway": "primary", "from": "town-bidur", "to": "town-syaprubesi",
     "coords": [(85.300, 28.050), (85.330, 28.090), (85.365, 28.130), (85.380, 28.160)]},
    {"id": "rd-02", "highway": "secondary", "from": "town-syaprubesi", "to": "set-001",
     "coords": [(85.380, 28.160), (85.400, 28.175), (85.415, 28.195), (85.430, 28.210)]},
    {"id": "rd-03", "highway": "secondary", "from": "town-syaprubesi", "to": "set-002",
     "coords": [(85.380, 28.160), (85.395, 28.170), (85.405, 28.180)]},
    {"id": "rd-04", "highway": "tertiary", "from": "town-syaprubesi", "to": "set-003",
     "coords": [(85.380, 28.160), (85.360, 28.190), (85.340, 28.230)]},
    {"id": "rd-05", "highway": "tertiary", "from": "town-syaprubesi", "to": "set-005",
     "coords": [(85.380, 28.160), (85.370, 28.225), (85.360, 28.290)]},
    {"id": "rd-06", "highway": "tertiary", "from": "town-syaprubesi", "to": "set-007",
     "coords": [(85.380, 28.160), (85.365, 28.172), (85.350, 28.180)]},
    {"id": "rd-07", "highway": "tertiary", "from": "set-007", "to": "set-006",
     "coords": [(85.350, 28.180), (85.340, 28.165), (85.330, 28.150)]},
    {"id": "rd-08", "highway": "primary", "from": "town-bidur", "to": "set-004",
     "coords": [(85.300, 28.050), (85.295, 28.080), (85.290, 28.110)]},
    {"id": "rd-09", "highway": "primary", "from": "town-bidur", "to": "set-008",
     "coords": [(85.300, 28.050), (85.275, 28.065), (85.250, 28.080)]},
    {"id": "rd-10", "highway": "secondary", "from": "set-004", "to": "set-008",
     "coords": [(85.290, 28.110), (85.270, 28.095), (85.250, 28.080)]},
    # A river-hugging mountain track that the flood corridor will cut.
    {"id": "rd-11", "highway": "track", "from": "set-003", "to": "set-005",
     "coords": [(85.340, 28.230), (85.350, 28.260), (85.360, 28.290)]},
    {"id": "rd-12", "highway": "track", "from": "set-001", "to": "set-005",
     "coords": [(85.430, 28.210), (85.400, 28.250), (85.360, 28.290)]},
]

BRIDGES = [
    {"id": "br-01", "name": "Trishuli Bridge (Syapru)", "lon": 85.372, "lat": 28.152},
    {"id": "br-02", "name": "Bidur Bridge", "lon": 85.305, "lat": 28.055},
]

# Buildings scattered near settlements (point centroids for the demo).
BUILDINGS = []
_seed_pts = [
    (85.431, 28.211, "set-001"), (85.429, 28.209, "set-001"),
    (85.406, 28.181, "set-002"), (85.404, 28.179, "set-002"),
    (85.341, 28.231, "set-003"), (85.339, 28.229, "set-003"),
    (85.291, 28.111, "set-004"), (85.289, 28.109, "set-004"),
    (85.361, 28.291, "set-005"), (85.359, 28.289, "set-005"),
    (85.331, 28.151, "set-006"), (85.329, 28.149, "set-006"),
    (85.351, 28.181, "set-007"), (85.349, 28.179, "set-007"),
    (85.251, 28.081, "set-008"), (85.249, 28.079, "set-008"),
    # A few buildings right beside the river (likely exposed in demo).
    (85.370, 28.153, "town-syaprubesi"), (85.368, 28.151, "town-syaprubesi"),
]
for i, (lon, lat, host) in enumerate(_seed_pts):
    BUILDINGS.append({"id": f"bld-{i:03d}", "lon": lon, "lat": lat, "settlement": host})

# The demo flood corridor: a polygon roughly along the Trishuli valley that
# crosses a few roads and riverside buildings.
FLOOD_RING = [
    (85.352, 28.130), (85.368, 28.148), (85.382, 28.158),
    (85.376, 28.170), (85.358, 28.180), (85.352, 28.175),
    (85.345, 28.160), (85.346, 28.145), (85.352, 28.130),
]

# Higher-confidence core of the corridor (kept distinct so the UI can show
# confident vs uncertain detections).
FLOOD_CORE_RING = [
    (85.360, 28.145), (85.370, 28.154), (85.376, 28.163),
    (85.368, 28.170), (85.359, 28.170), (85.355, 28.158),
    (85.360, 28.145),
]

# "Uncertain change" anomalies near steeper terrain (class 2 - NOT debris).
ANOMALY_RINGS = [
    [(85.415, 28.150), (85.425, 28.155), (85.420, 28.165), (85.410, 28.160), (85.415, 28.150)],
    [(85.320, 28.200), (85.330, 28.205), (85.326, 28.214), (85.316, 28.209), (85.320, 28.200)],
]


def demo_metadata() -> dict:
    return {
        "label": DEMO_LABEL,
        "source": "synthetic demo dataset",
        "note": "Replace with Sentinel-1/2 + ohsome OSM extraction for real analysis.",
    }
