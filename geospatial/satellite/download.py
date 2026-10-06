import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
    "protocol/openid-connect/token"
)
DOWNLOAD_URL = "https://download.dataspace.copernicus.eu/odata/v1/Products({id})/$value"


def get_token():
    data = {
        "client_id": "cdse-public",
        "grant_type": "password",
        "username": os.getenv("COPERNICUS_USERNAME"),
        "password": os.getenv("COPERNICUS_PASSWORD"),
    }
    r = requests.post(TOKEN_URL, data=data, timeout=60)
    r.raise_for_status()
    return r.json()["access_token"]


def download_product(product_id, out_path):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    session = requests.Session()
    session.headers.update(headers)

    url = DOWNLOAD_URL.format(id=product_id)
    # Follow redirects manually so the login header is kept
    response = session.get(url, allow_redirects=False, stream=True, timeout=120)
    while response.status_code in (301, 302, 303, 307):
        url = response.headers["Location"]
        response = session.get(url, allow_redirects=False, stream=True, timeout=120)
    response.raise_for_status()

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    total = 0
    with open(out_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            total += len(chunk)
            print(f"\rDownloaded {total / 1e6:.0f} MB", end="")
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    # Usage: python -m geospatial.satellite.download PRODUCT_ID output_name.zip
    pid, name = sys.argv[1], sys.argv[2]
    download_product(pid, os.path.join("sample_data", "raw", name))