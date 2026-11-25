# DL-SatelliteImagery — Core CLI & Assessment Package

Modular Python package powering pre/post satellite disaster assessment, geospatial area calculation, land-cover transition metrics, severity scoring, and Rich terminal reporting.

---

## Quick CLI Commands

Run from the repository root:

```powershell
# PRE/POST disaster assessment
.\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png --gsd 0.5

# Feature availability report
.\.venv\Scripts\python.exe DL-SatelliteImagery/cli.py feature-status

# Plain-text feature report
.\.venv\Scripts\python.exe DL-SatelliteImagery/cli.py feature-status --plain
```

---

## Core Modules

| Module | Responsibility |
| :--- | :--- |
| [`disaster_assessment/terminal_ui.py`](./disaster_assessment/terminal_ui.py) | Shared Rich terminal UI, gauge bars, badges, warning grouping, plain/ASCII fallbacks |
| [`disaster_assessment/feature_status.py`](./disaster_assessment/feature_status.py) | Runtime status registry for platform capabilities |
| [`disaster_assessment/pipeline/disaster_analyzer.py`](./disaster_assessment/pipeline/disaster_analyzer.py) | End-to-end `DisasterAnalyzer` orchestrator and `DisasterReport` |
| [`disaster_assessment/preprocessing/`](./disaster_assessment/preprocessing/) | Input validation, dimension alignment, and normalization |
| [`disaster_assessment/analytics/`](./disaster_assessment/analytics/) | Pixel & GeoTIFF geodesic area, land-change transitions, damage heuristics, severity engine |
| [`disaster_assessment/visualization/`](./disaster_assessment/visualization/) | Colorized overlays, hazard heatmaps, and comparison grids |

---

## Testing & Linting

```powershell
.\.venv\Scripts\python.exe -m pytest DL-SatelliteImagery/tests
.\.venv\Scripts\python.exe -m ruff check .
```
