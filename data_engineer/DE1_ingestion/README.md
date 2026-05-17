# DE1 - Data Ingestion

**PIC:** A. Agung Ngurah A.W  
**Tanggung jawab:** Download raw data dari TLC dan Open-Meteo, simpan ke `data/raw/`

## Files

| File | Deskripsi |
|---|---|
| `tlc_ingestion.py` | Download Yellow Taxi Parquet (Sept 2025 - Jan 2026) dari NYC TLC |
| `weather_ingestion.py` | Fetch data cuaca per jam untuk NYC dari Open-Meteo API |
| `prefect_flow.py` | Orkestrasi pipeline dengan Prefect (jalankan kedua ingestion) |

## Cara Jalankan

```bash
# Install dependencies (sekali saja)
pip install -r ../requirements.txt

# Jalankan pipeline ingestion
python prefect_flow.py
```

## Output

```
data/raw/
├── tlc/
│   ├── yellow_tripdata_2025-09.parquet
│   ├── yellow_tripdata_2025-10.parquet
│   ├── yellow_tripdata_2025-11.parquet
│   ├── yellow_tripdata_2025-12.parquet
│   └── yellow_tripdata_2026-01.parquet
└── weather/
    └── nyc_weather_hourly.parquet
```

## Kolom TLC yang diambil

- `tpep_pickup_datetime`, `tpep_dropoff_datetime`
- `passenger_count`, `trip_distance`
- `PULocationID`, `DOLocationID`
- `payment_type`, `fare_amount`, `tip_amount`, `total_amount`
