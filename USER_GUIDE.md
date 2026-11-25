# User Guide — Satellite Disaster Assessment & Analysis System

This guide walks through running the CLI tools, interpreting the terminal reports, training the building-damage model, launching the Gradio dashboard, and running automated tests.

---

## 1. Environment & Quick Check

Activate the virtual environment before running commands, or invoke `.\.venv\Scripts\python.exe` directly on Windows:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python --version
```

```bash
# Linux / macOS
source .venv/bin/activate
python --version
```

Verify PyTorch and CUDA availability (optional GPU acceleration):

```powershell
.\.venv\Scripts\python.exe -c "import torch; print('torch:', torch.__version__, 'cuda:', torch.cuda.is_available())"
```

---

## 2. Running PRE/POST Disaster Analysis (`cli.py`)

### Basic Usage

```powershell
python cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png
```

### All `cli.py` Options

| Flag | Description |
| --- | --- |
| `--pre <path>` | Path to pre-disaster satellite image (`PNG`, `JPG`, `TIF`) |
| `--post <path>` | Path to post-disaster satellite image (`PNG`, `JPG`, `TIF`) |
| `--single <path>` | Run single-image 6-class land-cover segmentation instead of pair analysis |
| `--mode {auto,trained,estimated}` | Building damage mode (`auto` uses validated weights if present, otherwise heuristic) |
| `--gsd <float>` | Ground Sample Distance in meters/pixel (enables `m²` and `km²` flood area output) |
| `--geotiff <path>` | GeoTIFF raster file for CRS and GSD metadata extraction |
| `--json-out <path>` | Save structured JSON analysis report |
| `--save-vis <path>` | Save colorized visualization overlay image |
| `--plain` | Force original plain-text output without Rich styling or ANSI colors |
| `--export-svg <path>` | Export the rendered Rich terminal report as an SVG file |

### Understanding the Terminal Report

1. **Header Banner**: Shows the project name, run timestamp, analysis mode (`Pixel-based`, `GSD-calibrated`, or `GeoTIFF`), and damage mode (`auto -> estimated`, `trained`, etc.).
2. **Inputs Panel**: Displays middle-shortened `PRE` and `POST` paths, original and aligned image resolutions, GSD (or `n/a` if omitted), and optional GeoTIFF path.
3. **Severity Panel**: Displays a `0–100` colored gauge bar (`LOW` green, `MODERATE` yellow, `HIGH` orange, `CRITICAL` red) and the formula explanation.
   - If any model component is unavailable, a **`PARTIAL RESULT`** badge is shown along with which components were excluded from the score.
   - When all models are validated and available, no `PARTIAL RESULT` badge is shown.
4. **Metrics Table**: Reports each metric alongside its provenance badge:
   - `[MEASURED]`: Produced by a validated trained model.
   - `[HEURISTIC]`: Produced by rule-based/HSV heuristics.
   - `[ESTIMATED]`: Produced by structural-change damage estimation.
   - `[UNAVAILABLE]`: Component unavailable; shown dimmed as `-` instead of `0.00%`.
5. **Model Status Table**: Lists `Change Detection`, `Flood Detection`, and `Building Damage`, their validation status (`READY`, `WEIGHTS MISSING`, `DEGENERATE`, etc.), inference mode, and expected/loaded weight filename (`siamese_unet.pth`, `flood_unet.pth`, `best_damage_model.pth`).
6. **Warnings Panel**: Automatically hidden when there are zero warnings. Duplicate warnings are removed, paired `PRE`/`POST` alignment resize messages are merged into one line, and entries are grouped under **Alignment**, **Models**, and **Accuracy**.

### Example Commands

```powershell
# Geospatial-calibrated run with JSON and overlay outputs
python cli.py `
  --pre sample_images/real_satellite_samples/disaster_pre_sentinel2.png `
  --post sample_images/real_satellite_samples/disaster_post_sentinel2.png `
  --gsd 10.0 `
  --json-out sentinel_report.json `
  --save-vis sentinel_overlay.png

# Generate an SVG snapshot of the styled terminal report
python cli.py `
  --pre sample_images/pre_disaster.png `
  --post sample_images/post_disaster.png `
  --export-svg disaster_report.svg

# Single-image land-cover segmentation
python cli.py --single sample_images/landcover_tiles/satellite_forest_canopy.jpg --save-vis forest_seg.png
```

---

## 3. Checking Feature Status & Model Validation (`DL-SatelliteImagery/cli.py`)

Use the subcommand CLI inside `DL-SatelliteImagery/` to inspect module readiness and checkpoint validation:

```powershell
# Categorized feature-status tables with live counts per status
python DL-SatelliteImagery/cli.py feature-status

# Original plain-text feature table
python DL-SatelliteImagery/cli.py feature-status --plain

# Include raw JSON feature dictionary
python DL-SatelliteImagery/cli.py feature-status --json

# Inspect model checkpoint validation details
python DL-SatelliteImagery/cli.py validate-models
python DL-SatelliteImagery/cli.py validate-models --json
```

`feature-status` computes module counts dynamically across five categories:
- **Core Engines**
- **Geospatial and GIS**
- **Remote Sensing**
- **Training and Export**
- **Experimental and Optional**

You can also run pair analysis via the subcommand CLI to dump a full output directory (`report.json`, `summary.txt`, and all intermediate PNG maps):

```powershell
python DL-SatelliteImagery/cli.py analyze `
  --pre sample_images/pre_disaster.png `
  --post sample_images/post_disaster.png `
  --gsd 0.5 `
  --output results_dir/
```

---

## 4. Training & Dry-Run Smoke Testing (`train_building_damage.py`)

### Smoke Test (`--dry_run`)

Run a 1-epoch synthetic smoke test to verify the training pipeline end-to-end:

```powershell
# Styled output with live per-epoch progress bar, results table, and summary
python DL-SatelliteImagery/disaster_assessment/training/train_building_damage.py --dry_run

# Plain-text output
python DL-SatelliteImagery/disaster_assessment/training/train_building_damage.py --dry_run --plain
```

`--dry_run` displays a **`SMOKE TEST: synthetic data, metrics are not meaningful.`** banner and saves synthetic inputs/checkpoints to `runs/dry_run/` so real datasets and weights are untouched. Remember to delete `runs/dry_run/` after inspection:

```powershell
Remove-Item -Recurse -Force runs/dry_run
```

> Checkpoints produced with `--dry_run` are tagged `synthetic_data=True` and are automatically refused by `ModelValidator` at inference time.

### Training on a Dataset

```powershell
python DL-SatelliteImagery/disaster_assessment/training/train_building_damage.py `
  --data_dir data/damage_dataset `
  --epochs 10 `
  --batch_size 4 `
  --lr 0.001
```

---

## 5. Launching the Gradio Web Interface (`app.py`)

```powershell
python app.py
```

Open `http://127.0.0.1:7860` in your browser to upload `PRE`/`POST` image pairs, adjust GSD or GeoTIFF inputs, view overlays/heatmaps, and inspect severity breakdowns interactively.

---

## 6. Plain Mode, `NO_COLOR`, Pipes, and Narrow Terminals

All three redesigned terminal commands share `DL-SatelliteImagery/disaster_assessment/terminal_ui.py` and automatically adapt to your environment:

- **Plain mode (`--plain`)**: Reproduces the original pre-Rich text output.
- **`NO_COLOR`**: Setting `NO_COLOR=1` disables Rich styling and falls back to plain text.
- **Piped or redirected output (`> report.txt` or `| Out-String`)**: Non-TTY streams automatically receive the original plain-text format with no ANSI escape codes.
- **Terminal width & encoding**: Styled output clamps to at most `100` columns, switches to compact columns below `72` columns, and automatically falls back to ASCII box borders (`+`, `-`, `|`) if the active Windows console encoding cannot represent Unicode box characters.

---

## 7. Running Tests & Linting

```powershell
# Full pytest suite
.\.venv\Scripts\python.exe -m pytest

# Targeted tests
.\.venv\Scripts\python.exe -m pytest DL-SatelliteImagery/tests/test_terminal_ui.py
.\.venv\Scripts\python.exe -m pytest DL-SatelliteImagery/tests/test_pipeline.py
.\.venv\Scripts\python.exe -m pytest DL-SatelliteImagery/tests/test_feature_status.py

# Lint check
.\.venv\Scripts\python.exe -m ruff check .
```

---

## 8. Troubleshooting

- **Models show `WEIGHTS MISSING` / `PARTIAL RESULT`**: Place validated checkpoints (`siamese_unet.pth`, `flood_unet.pth`, `building_damage/best_damage_model.pth`) under `DL-SatelliteImagery/disaster_assessment/weights/`. Without them, change and flood detection remain `UNAVAILABLE` and building damage uses the structural-change heuristic.
- **PyTorch DLL load error on Windows**: Run scripts with `.\.venv\Scripts\python.exe` rather than a global system Python installation.
- **Need to redirect styled output or capture slides**: Use `--export-svg <path>` on `cli.py` instead of shell redirection, since shell redirection switches stdout to plain mode.
