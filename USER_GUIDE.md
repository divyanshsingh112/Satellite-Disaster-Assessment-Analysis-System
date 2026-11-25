# User Guide — Terminal CLI

This guide covers using the command-line tools for pre/post satellite disaster assessment, inspecting feature availability, interpreting the Rich terminal output, and running the automated test suite.

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

---

## 2. Running PRE/POST Disaster Analysis (`cli.py`)

### Basic Command

```powershell
python cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png
```

### CLI Flags

| Flag | Description |
| --- | --- |
| `--pre <path>` | Path to pre-disaster satellite image (`PNG`, `JPG`, `TIF`) |
| `--post <path>` | Path to post-disaster satellite image (`PNG`, `JPG`, `TIF`) |
| `--single <path>` | Run single-image 6-class land-cover segmentation (heuristic) |
| `--mode {auto,trained,estimated}` | Assessment mode (`auto` uses heuristic/estimated fallbacks when checkpoints are absent) |
| `--gsd <float>` | Ground Sample Distance in meters/pixel (enables `m²` and `km²` area output) |
| `--geotiff <path>` | GeoTIFF raster file for CRS and GSD metadata extraction |
| `--json-out <path>` | Save structured JSON analysis report |
| `--save-vis <path>` | Save colorized visualization overlay image |
| `--plain` | Force original plain-text output without Rich styling or ANSI colors |
| `--export-svg <path>` | Export the rendered Rich terminal report as an SVG file |

### Reading the Terminal Report

1. **Header Banner**: Project name, run timestamp, analysis mode (`Pixel-based`, `GSD-calibrated`, or `GeoTIFF`), and damage mode.
2. **Inputs Panel**: Middle-shortened `PRE` and `POST` paths, original and aligned resolutions, GSD (`n/a` when omitted), and optional GeoTIFF path.
3. **Severity Panel**: Displays the `0–100` colored gauge bar (`LOW` green, `MODERATE` yellow, `HIGH` orange, `CRITICAL` red) and the score breakdown formula.
   - When any component is unavailable, a **`PARTIAL RESULT`** badge is shown along with the excluded components.
4. **Metrics Table**: Displays each metric with its provenance badge:
   - `[MEASURED]`: Measured from a validated component.
   - `[HEURISTIC]`: Computed using color-space/rule-based heuristics.
   - `[ESTIMATED]`: Computed using structural-change estimation.
   - `[UNAVAILABLE]`: Component unavailable; displayed dimmed as `-` instead of `0.00%`.
5. **Model Status Table**: Shows component availability status and expected weight filenames.
6. **Warnings Panel**: Hidden automatically when there are zero warnings. Duplicate warnings are removed, paired `PRE`/`POST` resize notices are merged into one line, and entries are grouped under **Alignment**, **Models**, and **Accuracy**.

### Common CLI Examples

```powershell
# Geospatial-calibrated run with JSON and overlay outputs
python cli.py `
  --pre sample_images/real_satellite_samples/disaster_pre_sentinel2.png `
  --post sample_images/real_satellite_samples/disaster_post_sentinel2.png `
  --gsd 10.0 `
  --json-out sentinel_report.json `
  --save-vis sentinel_overlay.png

# Export an SVG snapshot of the styled terminal report
python cli.py `
  --pre sample_images/pre_disaster.png `
  --post sample_images/post_disaster.png `
  --export-svg disaster_report.svg

# Single-image land-cover segmentation
python cli.py --single sample_images/landcover_tiles/satellite_forest_canopy.jpg --save-vis forest_seg.png
```

---

## 3. Checking Feature Availability (`DL-SatelliteImagery/cli.py`)

Use `feature-status` to inspect which platform modules are operational, heuristic-only, or awaiting configuration:

```powershell
# Categorized feature-status tables with live counts per status
python DL-SatelliteImagery/cli.py feature-status

# Original plain-text feature table
python DL-SatelliteImagery/cli.py feature-status --plain

# Include raw JSON feature dictionary
python DL-SatelliteImagery/cli.py feature-status --json
```

Modules are grouped into five categories with dynamically computed status counts at the top:
- **Core Engines**
- **Geospatial and GIS**
- **Remote Sensing**
- **Training and Export**
- **Experimental and Optional**

You can also run pair analysis via the subcommand CLI to write a directory containing `report.json`, `summary.txt`, and PNG output maps:

```powershell
python DL-SatelliteImagery/cli.py analyze `
  --pre sample_images/pre_disaster.png `
  --post sample_images/post_disaster.png `
  --gsd 0.5 `
  --output results_dir/
```

---

## 4. Plain Mode, `NO_COLOR`, Pipes, and Terminal Adaptation

All terminal UI rendering goes through `DL-SatelliteImagery/disaster_assessment/terminal_ui.py` and adapts automatically:

- **Plain mode (`--plain`)**: Reproduces the original pre-Rich plain text output.
- **`NO_COLOR`**: Setting `NO_COLOR=1` disables Rich styling and outputs plain text.
- **Piped or redirected output (`> report.txt` or `| Out-String`)**: Non-TTY streams automatically receive plain text with no ANSI escape sequences.
- **Width & Encoding**: Styled output adapts to terminal width (capped at `100` columns), switches to compact columns on narrow terminals (`< 72` columns), and falls back to ASCII box borders (`+`, `-`, `|`) if the console encoding cannot encode Unicode characters.

---

## 5. Running Tests & Linting

```powershell
# Full pytest suite
.\.venv\Scripts\python.exe -m pytest

# Targeted CLI / pipeline / status tests
.\.venv\Scripts\python.exe -m pytest DL-SatelliteImagery/tests/test_terminal_ui.py
.\.venv\Scripts\python.exe -m pytest DL-SatelliteImagery/tests/test_pipeline.py
.\.venv\Scripts\python.exe -m pytest DL-SatelliteImagery/tests/test_feature_status.py

# Lint check
.\.venv\Scripts\python.exe -m ruff check .
```

---

## 6. Troubleshooting

- **`PARTIAL RESULT` / `WEIGHTS MISSING` in CLI output**: Expected when optional `.pth` checkpoints are not present; unavailable components display `-` instead of `0.00%` and are excluded from the severity score.
- **Python environment errors on Windows**: Run scripts with `.\.venv\Scripts\python.exe` rather than a global system Python installation.
- **Saving styled output for slides**: Use `--export-svg <path>` on `cli.py` rather than shell redirection (`>`), since redirecting stdout activates plain-text mode.
