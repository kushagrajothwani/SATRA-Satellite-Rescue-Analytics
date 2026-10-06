import requests

CATALOGUE = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"


def search_sentinel1(bbox, start, end, max_results=20):
    """
    bbox  = (min_lon, min_lat, max_lon, max_lat)
    start = "2026-08-01", end = "2026-08-31"
    Returns a list of Sentinel-1 GRD products with key details.
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    polygon = (
        f"POLYGON(({min_lon} {min_lat},{max_lon} {min_lat},"
        f"{max_lon} {max_lat},{min_lon} {max_lat},{min_lon} {min_lat}))"
    )

    filter_query = (
        "Collection/Name eq 'SENTINEL-1' "
        f"and OData.CSC.Intersects(area=geography'SRID=4326;{polygon}') "
        f"and ContentDate/Start gt {start}T00:00:00.000Z "
        f"and ContentDate/Start lt {end}T23:59:59.000Z "
        "and contains(Name,'GRD')"
    )

    params = {
        "$filter": filter_query,
        "$orderby": "ContentDate/Start asc",
        "$top": max_results,
        "$expand": "Attributes",
    }

    response = requests.get(CATALOGUE, params=params, timeout=60)
    response.raise_for_status()

    products = []
    for item in response.json().get("value", []):
        attrs = {a["Name"]: a["Value"] for a in item.get("Attributes", [])}
        products.append({
            "id": item["Id"],
            "name": item["Name"],
            "start": item["ContentDate"]["Start"],
            "orbit_direction": attrs.get("orbitDirection"),
            "relative_orbit": attrs.get("relativeOrbitNumber"),
        })
    return products


if __name__ == "__main__":
    # Small test box in Nepal (change to your AOI)
    results = search_sentinel1((85.2, 28.0, 85.6, 28.4), "2026-07-20", "2026-09-05")
    for p in results:
        print(p["id"], p["start"], p["orbit_direction"], p["relative_orbit"], p["name"])