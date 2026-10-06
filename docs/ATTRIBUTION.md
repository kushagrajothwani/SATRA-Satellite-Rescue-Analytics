# Data attribution and citations — SATRA

Required notices, reproduced exactly as specified by the hackathon Track B brief.

## Satellite data
> Contains modified Copernicus Sentinel data 2026.

- Copernicus Data Space Ecosystem — https://dataspace.copernicus.eu

## Elevation data
> Produced using Copernicus WorldDEM-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.

## OpenStreetMap
> © OpenStreetMap contributors.

- Historical extraction via the ohsome API — https://api.ohsome.org

## Training datasets
- **Kuro Siwo** (recommended primary dataset). Cite Bountos et al., 2024. Verify repository license before redistribution.
- **Sen1Floods11** — georeferenced Sentinel-1 flood dataset (flood + permanent-water labels; ~4,831 chips).

## Validation only (never model inputs)
- Copernicus EMS activation **EMSR927** (Nepal flood).
- UNOSAT and published damage maps.
- Post-event OpenStreetMap edits.

## Frameworks & libraries
FastAPI, Pydantic, Rasterio, GDAL, GeoPandas, Shapely, NetworkX, PyTorch, LangGraph, React, TypeScript, MapLibre GL JS.
