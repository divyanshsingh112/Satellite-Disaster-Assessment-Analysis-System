# System Architecture

## Overview

The Satellite Disaster Assessment & Analysis System provides a modular command-line pipeline for validating, aligning, and analyzing pre- and post-disaster satellite imagery, computing geospatial impact areas and weighted severity scores, and rendering structured terminal and JSON reports.

## Pipeline Dataflow

```text
INPUT DATA (PNG / JPG / GeoTIFF)
    |
VALIDATION (ImageValidator)
    |
PREPROCESSING & ALIGNMENT (ImageAligner: resize, optional ORB alignment, normalization)
    |
LAND-COVER & CHANGE ANALYTICS
    +---> Land-cover estimation (HSV heuristic)
    +---> Structural change & damage estimation (DamageMetrics)
    +---> Land-cover transition matrix (LandChangeMetrics)
    |
GEOSPATIAL AREA & SEVERITY SCORING
    +---> Area calculation (pixel-based, GSD-calibrated, or GeoTIFF CRS/geodesic)
    +---> Severity engine (0-100 weighted score + LOW/MODERATE/HIGH/CRITICAL tier)
    |
RENDERING & CLI OUTPUT
    +---> Visualization maps (OverlayRenderer, HeatmapGenerator, ComparisonRenderer)
    +---> Structured report (DisasterReport.to_dict() JSON / DisasterReport.summary())
    +---> Rich Terminal UI (terminal_ui.py) with plain, NO_COLOR, non-TTY, and ASCII fallbacks
```

## Core Directory Structure

```text
cli.py                                   # Main CLI entrypoint (--pre/--post, --single)
DL-SatelliteImagery/
├── cli.py                               # Subcommand CLI (analyze, feature-status)
└── disaster_assessment/
    ├── __init__.py
    ├── terminal_ui.py                   # Shared Rich terminal UI & fallback helpers
    ├── feature_status.py                # Feature availability registry
    ├── preprocessing/
    │   ├── image_validation.py          # Channel, dtype, dimension, and variance checks
    │   └── image_alignment.py           # Dimension matching, ORB alignment, normalization
    ├── analytics/
    │   ├── area_calculator.py           # Pixel and relative area metrics
    │   ├── geospatial_area.py           # GeoTIFF CRS/affine parsing & geodesic area
    │   ├── damage_metrics.py            # Structural change damage estimation
    │   ├── land_change_metrics.py       # 6x6 land-cover transition matrix
    │   └── severity_engine.py           # Configurable 0-100 disaster severity scorer
    ├── visualization/
    │   ├── overlays.py                  # Land-cover, change, flood, and damage overlays
    │   ├── heatmap.py                   # Combined hazard heatmap generation
    │   └── comparison.py                # Side-by-side and grid views
    ├── pipeline/
    │   └── disaster_analyzer.py         # End-to-end DisasterAnalyzer & DisasterReport
    └── configs/
        ├── default.yaml                 # Default pipeline toggles
        ├── pipeline.yaml                # Pipeline stage configuration
        └── severity_config.yaml         # Severity weights & thresholds
```
