# Satellite Disaster Assessment & Analysis System

A Python remote-sensing and geospatial analysis tool for comparing pre-disaster (`PRE`) and post-disaster (`POST`) satellite imagery via the command line, computing land-cover transitions, geospatial impact areas, and a weighted `0–100` disaster severity score.

## Capabilities

- **Image Validation & Alignment**: Validates input images, normalizes dimensions, and aligns `PRE` and `POST` pairs.
- **Rule-Based & Heuristic Analytics**: Computes land-cover estimation (HSV heuristic), vegetation loss, water expansion, structural change estimation, and a configurable `0–100` severity score.
- **Geospatial Area Calculation**: Supports optional `--gsd` (meters/pixel) and `--geotiff` inputs to report impact area in `m²` and `km²` alongside pixel percentages.
- **Rich Terminal UI (`terminal_ui.py`)**: Displays a styled terminal report (header banner, inputs, colored severity gauge, `PARTIAL RESULT` indicator when components are unavailable, provenance badges, component status table, and deduplicated grouped warnings) with automatic plain-text fallback on `--plain`, `NO_COLOR`, or piped/non-TTY output, plus optional `--export-svg`.
- **Feature Readiness CLI**: Summarizes module availability across categories via `feature-status`.

---

## Project Structure

```text
Satellite-Disaster-Assessment-Analysis-System/
├── cli.py                              # Main CLI (PRE/POST analysis & single-image segmentation)
├── pyproject.toml                      # Project metadata, pytest, pyright, and ruff configuration
├── requirements.txt                    # Core Python dependencies
├── USER_GUIDE.md                       # CLI & terminal UI usage guide
├── PROJECT_REPORT.md                   # Technical overview and verification summary
├── docs/                               # Architecture, configuration, and installation guides
├── sample_images/                      # Sample PRE/POST pairs, GeoTIFFs, and land-cover tiles
└── DL-SatelliteImagery/
    ├── cli.py                          # Subcommand CLI (analyze, feature-status)
    ├── disaster_assessment/
    │   ├── terminal_ui.py              # Shared Rich terminal UI & plain/ASCII fallbacks
    │   ├── feature_status.py           # Runtime feature availability registry
    │   ├── pipeline/disaster_analyzer.py
    │   ├── preprocessing/              # Image validation and alignment
    │   ├── analytics/                  # Area, geospatial area, land-change, severity engine
    │   ├── visualization/              # Overlays, heatmaps, and comparison grids
    │   └── configs/                    # YAML configuration files
    └── tests/                          # Automated pytest suite
```

---

## Installation & Environment Setup

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Terminal Test Prompts & Commands

Run all commands from the repository root (replace `.\.venv\Scripts\python.exe` with `python` if your virtual environment is already activated).

### 1. Automated Tests & Linter

```powershell
# Run the full test suite
.\.venv\Scripts\python.exe -m pytest

# Run only the terminal UI tests
.\.venv\Scripts\python.exe -m pytest DL-SatelliteImagery/tests/test_terminal_ui.py

# Run Ruff linter
.\.venv\Scripts\python.exe -m ruff check .
```

### 2. Main CLI — PRE/POST Disaster Analysis (`cli.py`)

```powershell
# Styled Rich terminal report on the default sample pair
.\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png

# With Ground Sample Distance (GSD in meters/pixel) for metric area calculations
.\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png --gsd 0.5

# Save JSON report and colorized overlay image
.\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png --gsd 250 --json-out report.json --save-vis overlay.png

# Export the styled terminal report as an SVG
.\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png --export-svg report_terminal.svg

# Plain-text mode (reproduces original output; also triggered by NO_COLOR or piping)
.\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png --plain

# Test NO_COLOR behavior in PowerShell
$env:NO_COLOR="1"; .\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png; Remove-Item Env:NO_COLOR
```

**Additional Bundled Sample Pairs:**

```powershell
# Hurricane pair
.\.venv\Scripts\python.exe cli.py --pre sample_images/disaster_pairs/hurricane_pre.jpg --post sample_images/disaster_pairs/hurricane_post.jpg

# Earthquake pair
.\.venv\Scripts\python.exe cli.py --pre sample_images/disaster_pairs/earthquake_pre.jpg --post sample_images/disaster_pairs/earthquake_post.jpg

# Bushfire pair
.\.venv\Scripts\python.exe cli.py --pre sample_images/disaster_pairs/bushfire_pre.jpg --post sample_images/disaster_pairs/bushfire_post.jpg

# Sentinel-2 real satellite pair
.\.venv\Scripts\python.exe cli.py --pre sample_images/real_satellite_samples/disaster_pre_sentinel2.png --post sample_images/real_satellite_samples/disaster_post_sentinel2.png --gsd 10.0

# Single-image land-cover segmentation (heuristic)
.\.venv\Scripts\python.exe cli.py --single sample_images/landcover_tiles/satellite_urban_city.jpg --save-vis landcover_overlay.png
```

### 3. Feature Status CLI (`DL-SatelliteImagery/cli.py`)

```powershell
# Categorized feature availability tables (styled Rich output)
.\.venv\Scripts\python.exe DL-SatelliteImagery/cli.py feature-status

# Plain-text feature status report
.\.venv\Scripts\python.exe DL-SatelliteImagery/cli.py feature-status --plain

# Feature status with JSON output
.\.venv\Scripts\python.exe DL-SatelliteImagery/cli.py feature-status --json
```

---

## Documentation

- [USER_GUIDE.md](USER_GUIDE.md) — Detailed CLI usage, terminal report breakdown, and troubleshooting
- [docs/architecture.md](docs/architecture.md) — Pipeline and system architecture
- [docs/configuration.md](docs/configuration.md) — YAML configuration reference
- [docs/installation.md](docs/installation.md) — Environment setup and verification
