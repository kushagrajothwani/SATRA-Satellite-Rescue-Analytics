from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SATRA API", version="0.1.0")

# Allow the React app to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "SATRA"}


@app.get("/api/sample-flood")
def sample_flood():
    """Sample GeoJSON, clearly labelled as SAMPLE data, not a real analysis."""
    return {
        "type": "FeatureCollection",
        "properties": {"label": "SAMPLE DATA - not a real analysis"},
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Sample flood zone"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [85.35, 28.15], [85.40, 28.15],
                        [85.40, 28.19], [85.35, 28.19],
                        [85.35, 28.15],
                    ]],
                },
            }
        ],
    }