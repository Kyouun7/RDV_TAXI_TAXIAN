from pathlib import Path

APP_TITLE = "Segmentasi Perilaku Pelanggan Taksi NYC"
APP_SUBTITLE = "Fondasi Intelijen Mobilitas Perilaku"

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ENGINEER_DIR = REPO_ROOT / "data_engineer"

INTERMEDIATE_DIR = DATA_ENGINEER_DIR / "data" / "intermediate"
RAW_ZONES_DIR = DATA_ENGINEER_DIR / "data" / "raw" / "zones"

FACT_TRIPS_PATH = INTERMEDIATE_DIR / "fact_trips.parquet"
FACT_TRIPS_WEATHER_PATH = INTERMEDIATE_DIR / "fact_trips_with_weather.parquet"
DIM_ZONES_PATH = INTERMEDIATE_DIR / "dim_zones.parquet"
TAXI_ZONES_GEOJSON_PATH = RAW_ZONES_DIR / "taxi_zones.geojson"

FACT_TRIPS_CLUSTERED_PATH = INTERMEDIATE_DIR / "fact_trips_clustered.parquet"
FACT_TRIPS_WEATHER_CLUSTERED_PATH = INTERMEDIATE_DIR / "fact_trips_with_weather_clustered.parquet"

CACHE_TTL_SECONDS = 900
CACHE_MAX_ENTRIES = 128

DEFAULT_BOROUGH_SELECTION = ["All"]
DEFAULT_HOUR_RANGE = (0, 23)
DEFAULT_RUSH_HOUR_MODE = "All"
DEFAULT_WEATHER_SELECTION = ["All"]
DEFAULT_WEEKEND_MODE = "Semua"
DEFAULT_DAY_OF_WEEK_SELECTION = ["Semua"]
DEFAULT_MAP_INTERACTION_MODE = "Seimbang"
DEFAULT_GEOJSON_PRECISION = 5

DOW_LABELS = {
	1: "Senin",
	2: "Selasa",
	3: "Rabu",
	4: "Kamis",
	5: "Jumat",
	6: "Sabtu",
	0: "Minggu",
}

MAP_MODE_DESCRIPTIONS = {
	"Pasif": "Paling ringan. Sinkronisasi backend minimum, cocok untuk presentasi cepat.",
	"Seimbang": "Seimbang antara kelancaran dan detail interaksi.",
	"Interaktif": "Interaksi penuh dengan sinkronisasi posisi peta lebih aktif.",
	"Klik Detail": "Detail zona muncul saat klik; hover dibuat lebih ringan.",
	"Hover Ringan": "Hover ringkas agar beban interaksi lebih rendah dari mode penuh.",
}

MAP_CENTER = [40.7549, -73.9840]
MAP_ZOOM = 10
MAP_TILE = "CartoDB positron"

# Optional soft analytical palette (mint / teal family). Keep subtle and accessible.
SOFT_PALETTE = {
	"accent": "#074051",  # soft teal
	"accent_soft": "#1EC9CF",
	"choropleth_scale": ["#d3f2a4", "#8dda94", "#5fb288", "#31877c", "#136068"],
}
