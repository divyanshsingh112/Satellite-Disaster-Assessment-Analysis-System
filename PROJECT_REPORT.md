# Technical Report — Satellite Disaster Assessment & Analysis System

## 1. Overview & Problem Statement

Rapid post-disaster impact assessment from optical satellite imagery requires comparing pre-disaster (`PRE`) and post-disaster (`POST`) observations in a repeatable, transparent way. Manual inspection of raw raster pairs is slow and error-prone, while opaque metrics without spatial calibration or provenance tracking can mislead responders.

This system provides a scriptable command-line pipeline (`cli.py` and `DL-SatelliteImagery/cli.py`) that:
- Validates and aligns bi-temporal (`PRE` / `POST`) satellite image pairs.
- Quantifies land-cover transitions, vegetation loss, water expansion, and structural change heuristics.
- Computes true metric area (`m²` / `km²`) when GeoTIFF CRS metadata or Ground Sample Distance (`--gsd`) is supplied, falling back strictly to pixel percentages when spatial resolution is absent.
- Produces a configurable `0–100` disaster severity score (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`) with explicit provenance labeling.
- Renders structured terminal reports via a shared Rich presentation layer (`terminal_ui.py`) while preserving plain-text output for piped/non-TTY environments and automated JSON/overlay export.

---

## 2. Pipeline Architecture

```text
PRE + POST Images (PNG / JPG / GeoTIFF)
        │
        ▼
ImageValidator ──► Channel, dtype, dimension, and variance validation
        │
        ▼
ImageAligner ────► Common target sizing, optional ORB alignment, normalization
        │
        ├──► Land-Cover Heuristic (6 classes: Water, Land, Road, Building, Vegetation, Unlabeled)
        ├──► LandChangeMetrics (6×6 transition matrix, vegetation loss %, water expansion %)
        ├──► DamageMetrics (structural-change damage estimation)
        └──► GeospatialAreaCalculator (GeoTIFF CRS / geodesic / GSD / pixel-based area)
        │
        ▼
SeverityEngine ──► Weighted 0–100 score + severity tier + formula explanation
        │
        ▼
DisasterReport ──► Overlay/Heatmap PNGs + JSON schema + Rich/Plain Terminal UI
```

---

## 3. Preprocessing & Geospatial Analytics

### 3.1 Validation & Alignment
- `ImageValidator` checks image arrays for valid rank, channels, non-empty dimensions, and non-zero variance before normalization.
- `ImageAligner` resizes `PRE` and `POST` pairs to a uniform spatial grid, optionally applies ORB feature alignment, and emits structured `AlignmentReport` warnings when inputs are resampled.

### 3.2 Georeferenced Area Calculation
`GeospatialAreaCalculator` supports three operating modes without fabricating metric area when georeferencing is absent:
1. **GeoTIFF CRS**: Extracts coordinate reference system and affine transforms via `rasterio`, handling projected CRS directly in meters and geographic CRS (`EPSG:4326`) with latitude-adjusted geodesic scaling.
2. **User-Supplied GSD (`--gsd`)**: Computes pixel area as $\text{GSD}^2$ in $\text{m}^2$ for standard PNG/JPG imagery.
3. **Pixel-Only Mode**: Reports pixel counts and percentages only.

### 3.3 Severity Scoring Engine
`SeverityEngine` loads weights and tier thresholds from `DL-SatelliteImagery/disaster_assessment/configs/severity_config.yaml` and maps normalized inputs (`0–100`) to `LOW`, `MODERATE`, `HIGH`, or `CRITICAL`, returning a component-by-component breakdown and human-readable formula string.

---

## 4. Terminal Presentation Layer (`terminal_ui.py`)

All terminal formatting is isolated in `DL-SatelliteImagery/disaster_assessment/terminal_ui.py` without modifying underlying computations or JSON schemas:

- **Main Analysis Report (`cli.py --pre/--post`)**:
  - Header banner with timestamp, analysis mode, and damage mode.
  - `Inputs` panel with middle-shortened paths, source/aligned resolution, and GSD (`n/a` when omitted).
  - `Severity` panel with colored gauge bar and dynamic `PARTIAL RESULT` badge whenever any component is unavailable.
  - `Metrics` table tagging each metric as `[MEASURED]`, `[HEURISTIC]`, `[ESTIMATED]`, or `[UNAVAILABLE]` (rendered as `-` instead of `0.00%`).
  - `Model Status` table showing readiness and expected checkpoint filenames.
  - `Warnings` panel with deduplicated, grouped entries (`Alignment`, `Models`, `Accuracy`) and merged `PRE`/`POST` resize notices (hidden when zero warnings exist).
  - Optional `--export-svg <path>` output for documentation and slides.
- **Feature Status (`DL-SatelliteImagery/cli.py feature-status`)**:
  - Top summary bar computing counts dynamically from `FeatureStatusRegistry`.
  - Five categorized tables (`Core Engines`, `Geospatial and GIS`, `Remote Sensing`, `Training and Export`, `Experimental and Optional`).
- **Environment & Fallback Guarantees**:
  - `--plain`, `NO_COLOR`, and non-TTY (piped/redirected) streams reproduce the original plain-text output.
  - Adapts to terminal width (capped at 100 columns, compact layout below 72 columns) and falls back to ASCII box borders when Unicode characters cannot be encoded by the active console.

---

## 5. Verification

The repository includes automated unit and integration tests under `DL-SatelliteImagery/tests/` covering preprocessing, analytics, geospatial resampling, pipeline execution, feature status, and terminal UI formatting/fallbacks:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```
