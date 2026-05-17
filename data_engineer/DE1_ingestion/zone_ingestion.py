"""
DE1 - Taxi Zone Reference Data Ingestion
Downloads zone lookup CSV and shapefile from NYC TLC for geographic mapping.

Outputs:
  data/raw/zones/taxi_zone_lookup.csv   -> LocationID to Zone name + Borough
  data/raw/zones/taxi_zones.geojson     -> polygon geometry for each zone (for maps)
"""

import urllib.request
import zipfile
import io
from pathlib import Path

ZONES_DIR = Path(__file__).parent.parent / "data" / "raw" / "zones"

LOOKUP_URL    = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
SHAPEFILE_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip"


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def download_zone_lookup():
    dest = ZONES_DIR / "taxi_zone_lookup.csv"
    if dest.exists():
        print(f"[SKIP] taxi_zone_lookup.csv already exists.")
        return

    print(f"[DOWNLOAD] Zone lookup CSV...")
    dest.write_bytes(fetch(LOOKUP_URL))
    print(f"[DONE] Saved to {dest}")


def download_zone_shapefile():
    geojson_dest  = ZONES_DIR / "taxi_zones.geojson"
    shapefile_dir = ZONES_DIR / "shapefile"

    if geojson_dest.exists():
        print(f"[SKIP] taxi_zones.geojson already exists.")
        return

    if not shapefile_dir.exists():
        print(f"[DOWNLOAD] Taxi zone shapefile...")
        data = fetch(SHAPEFILE_URL)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(shapefile_dir)
        print(f"[DONE] Shapefile extracted to {shapefile_dir}")

    try:
        import geopandas as gpd
        shp_file = next(shapefile_dir.rglob("*.shp"))
        gdf = gpd.read_file(shp_file).to_crs("EPSG:4326")
        gdf.to_file(geojson_dest, driver="GeoJSON")
        print(f"[DONE] GeoJSON saved to {geojson_dest}")
    except ImportError:
        print("[WARN] geopandas not installed — shapefile saved but not converted.")
        print(f"       Shapefile at: {shapefile_dir}")


def run_ingestion():
    ZONES_DIR.mkdir(parents=True, exist_ok=True)
    download_zone_lookup()
    download_zone_shapefile()
    print("[DONE] Zone reference data ready.")


if __name__ == "__main__":
    run_ingestion()
