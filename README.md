# Satellite Disaster Assessment & Analysis System

A PyTorch and geospatial remote-sensing platform for comparing pre-disaster (`PRE`) and post-disaster (`POST`) satellite imagery, estimating land-cover transitions, assessing building damage, calculating georeferenced impact areas, and generating a transparent `0–100` severity score.

## Key Capabilities

- **PRE/POST Disaster Analysis (`cli.py`)**: Aligns image pairs, validates model checkpoints before inference, computes land-cover transitions, building damage, and a weighted `0–100` severity score, and exports JSON reports and colorized overlay maps.
- **Honest Provenance & Safety**: Models are validated prior to inference. Missing or synthetic/unvalidated checkpoints are reported as `UNAVAILABLE` or fall back to clearly labeled heuristics (`HEURISTIC` / `ESTIMATED`), with a `PARTIAL RESULT` indicator when components are unavailable.
- **Geospatial & Metric Area Support**: Supports `--gsd` (meters/pixel) and `--geotiff` inputs for metric area (`m²` / `km²`) calculations alongside pixel-percentage outputs.
- **Rich Terminal UI (`terminal_ui.py`)**: Styled terminal output for the main CLI report, `feature-status`, and training `--dry_run`, with automatic fallback to original plain text on `--plain`, `NO_COLOR`, or non-TTY (piped/redirected) streams, plus optional `--export-svg`.
- **Interactive Gradio Dashboard (`app.py`)**: Web interface for visual pair analysis and single-image land-cover segmentation.

---

## Project Structure

```text
Satellite-Disaster-Assessment-Analysis-System/
├── app.py                              # Gradio web UI launcher
├── cli.py                              # Main CLI (PRE/POST analysis & single-image segmentation)
├── pyproject.toml                      # Package metadata, pytest, pyright, ruff config
├── requirements.txt                    # Core Python dependencies
├── USER_GUIDE.md                       # Detailed usage & workflow guide
├── docs/                               # Architecture, configuration, and setup docs
├── sample_images/                      # Sample PRE/POST pairs, GeoTIFFs, land-cover tiles
├── data/damage_dataset/                # Sample train/val building damage dataset
└── DL-SatelliteImagery/
    ├── cli.py                          # Subcommand CLI (analyze, validate-models, feature-status)
    ├── disaster_assessment/
    │   ├── terminal_ui.py              # Shared Rich terminal UI & plain/ASCII fallbacks
    │   ├── feature_status.py           # Runtime module & weight availability registry
    │   ├── pipeline/disaster_analyzer.py
    │   ├── analytics/                  # Severity engine, area, damage, land-change, spectral, DEM
    │   ├── models/                     # U-Net, Siamese U-Net, Flood U-Net, BuildingDamageUNet
    │   ├── training/train_building_damage.py
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

For NVIDIA CUDA acceleration, install PyTorch and torchvision matching your GPU/CUDA driver from PyTorch's wheel index before installing the remaining packages:

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
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

Run these commands from the repository root (replace `.\.venv\Scripts\python.exe` with `python` if your virtual environment is already activated).

### 1. Automated Test Suite & Linter

```powershell
# Run the full test suite
.\.venv\Scripts\python.exe -m pytest

# Run only the terminal UI tests
.\.venv\Scripts\python.exe -m pytest DL-SatelliteImagery/tests/test_terminal_ui.py

# Run Ruff linter across the codebase
.\.venv\Scripts\python.exe -m ruff check .
```

### 2. Main CLI — PRE/POST Disaster Analysis (`cli.py`)

```powershell
# Default styled terminal report on the bundled sample pair
.\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png

# With Ground Sample Distance (GSD in meters/pixel) for metric area calculations
.\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png --gsd 0.5

# Save JSON report and visualization overlay image
.\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png --gsd 250 --json-out report.json --save-vis overlay.png

# Export styled terminal output as an SVG for slides or documentation
.\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png --export-svg report_terminal.svg

# Plain-text mode (identical to original output; also triggered automatically by NO_COLOR or piping)
.\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png --plain

# Force NO_COLOR in PowerShell
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

# Single-image land-cover segmentation
.\.venv\Scripts\python.exe cli.py --single sample_images/landcover_tiles/satellite_urban_city.jpg --save-vis landcover_overlay.png
```

### 3. Feature Status & Model Validation (`DL-SatelliteImagery/cli.py`)

```powershell
# Categorized feature availability report (styled Rich tables)
.\.venv\Scripts\python.exe DL-SatelliteImagery/cli.py feature-status

# Plain-text feature status report
.\.venv\Scripts\python.exe DL-SatelliteImagery/cli.py feature-status --plain

# Feature status with JSON output
.\.venv\Scripts\python.exe DL-SatelliteImagery/cli.py feature-status --json

# Check model checkpoint validation status
.\.venv\Scripts\python.exe DL-SatelliteImagery/cli.py validate-models --json
```

### 4. Building Damage Training Smoke Test (`train_building_damage.py`)

```powershell
# Styled dry-run smoke test (generates synthetic data under runs/dry_run/ and runs 1 epoch)
.\.venv\Scripts\python.exe DL-SatelliteImagery/disaster_assessment/training/train_building_damage.py --dry_run

# Plain-text dry-run smoke test
.\.venv\Scripts\python.exe DL-SatelliteImagery/disaster_assessment/training/train_building_damage.py --dry_run --plain
```

> **Note:** `--dry_run` writes throwaway synthetic data and checkpoints under `runs/dry_run/`. Delete `runs/dry_run/` after verifying the smoke test.

### 5. Gradio Web Dashboard (`app.py`)

```powershell
.\.venv\Scripts\python.exe app.py
```

Opens locally at `http://127.0.0.1:7860` (or the next free port starting at `7860`).

---

## Documentation

- [USER_GUIDE.md](USER_GUIDE.md) — Step-by-step usage guide for the CLI, terminal UI flags, Gradio app, training, and troubleshooting
- [docs/architecture.md](docs/architecture.md) — Pipeline and system architecture
- [docs/configuration.md](docs/configuration.md) — YAML configuration options
- [docs/installation.md](docs/installation.md) — Optional dependency groups and verification steps
