# Configuration

## Centralized Configuration

Configuration files live in `DL-SatelliteImagery/disaster_assessment/configs/`:

- `severity_config.yaml` — Weights, thresholds, and labels for the 0–100 disaster severity engine.
- `default.yaml` — Default pipeline toggles for land-cover, change, flood, and damage estimation.
- `pipeline.yaml` — Pipeline stage settings and memory management options.

## Severity Scoring Example

```yaml
# DL-SatelliteImagery/disaster_assessment/configs/severity_config.yaml
weights:
  flood: 0.40
  building_damage: 0.35
  change: 0.15
  vegetation_loss: 0.10

thresholds:
  low: 20
  moderate: 40
  high: 70
  critical: 100

severity_labels:
  low: "LOW"
  moderate: "MODERATE"
  high: "HIGH"
  critical: "CRITICAL"
```

## CLI Runtime Flags

Runtime options can be supplied directly on the command line without editing YAML files:

- `--gsd <float>`: Ground Sample Distance in meters/pixel for metric area (`m²` / `km²`) outputs.
- `--geotiff <path>`: GeoTIFF file for automatic CRS and pixel resolution extraction.
- `--mode {auto,trained,estimated}`: Controls damage assessment mode (`auto` falls back to structural-change estimation when checkpoints are absent).
- `--plain` / `NO_COLOR=1`: Forces plain-text terminal output without Rich styling.
- `--export-svg <path>`: Exports the styled terminal report as an SVG file.
