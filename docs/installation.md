# Installation

## Quick Start (Windows PowerShell)

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install core dependencies
pip install -r requirements.txt
```

## Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Optional Geospatial Dependencies

```bash
# Geospatial extras (shapely, geopandas, folium, scipy, scikit-learn)
pip install -e ".[geospatial]"
```

## Verify Installation

```powershell
# Check feature status via CLI
.\.venv\Scripts\python.exe DL-SatelliteImagery/cli.py feature-status

# Run test suite and linter
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

## CLI Usage

```powershell
# Disaster assessment on a PRE/POST pair
.\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png --gsd 250.0

# Single-image land-cover segmentation (heuristic)
.\.venv\Scripts\python.exe cli.py --single sample_images/landcover_tiles/satellite_urban_city.jpg
```
