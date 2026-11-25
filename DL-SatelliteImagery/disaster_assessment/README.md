# `disaster_assessment` Package

Modular engine for satellite image validation, bi-temporal alignment, geospatial area computation, heuristic land-cover and damage analytics, configurable severity scoring, and terminal reporting.

---

## Directory Layout

```text
disaster_assessment/
├── terminal_ui.py               # Shared Rich terminal UI, theme, and plain/ASCII fallbacks
├── feature_status.py            # Runtime feature availability registry
├── preprocessing/
│   ├── image_validation.py      # Integrity, dimension, and channel checks
│   └── image_alignment.py       # Dimension matching, ORB alignment, color normalization
├── analytics/
│   ├── geospatial_area.py       # GeoTIFF metadata, Projected/Geographic CRS, GSD area engine
│   ├── area_calculator.py       # Pixel-based and percentage area calculator
│   ├── damage_metrics.py        # Structural change damage estimation
│   ├── land_change_metrics.py   # 6-class land-cover transition matrix & metrics
│   └── severity_engine.py       # Configurable 0-100 disaster severity scorer
├── visualization/
│   ├── overlays.py              # Land-cover, change, flood, and damage overlays
│   ├── heatmap.py               # Combined disaster intensity heatmaps
│   └── comparison.py            # Side-by-side and multi-panel comparison grids
├── pipeline/
│   └── disaster_analyzer.py     # Main DisasterAnalyzer orchestrator & DisasterReport
└── configs/
    ├── default.yaml             # Default pipeline configuration
    ├── pipeline.yaml            # Stage settings
    └── severity_config.yaml     # Severity weights & thresholds
```

---

## Georeferenced Area Modes

1. **GeoTIFF (`.tif`/`.tiff`)**: Parses CRS and affine transform via `rasterio`, supporting projected meter-based CRS and geographic (`EPSG:4326`) geodesic scaling.
2. **User-Supplied GSD (`--gsd`)**: Computes metric area (`m²` and `km²`) from `meters_per_pixel` for standard PNG/JPG images.
3. **Pixel-Based Fallback**: Reports pixel counts and percentages when no spatial resolution is supplied.

---

## Python API & CLI Usage

```python
from disaster_assessment.pipeline import DisasterAnalyzer
import numpy as np
from PIL import Image

analyzer = DisasterAnalyzer()
pre = np.array(Image.open("sample_images/pre_disaster.png").convert("RGB"))
post = np.array(Image.open("sample_images/post_disaster.png").convert("RGB"))

report = analyzer.analyze(
    pre_image=pre,
    post_image=post,
    damage_mode="auto",
    meters_per_pixel=0.5,
)

print(report.summary())
print(report.to_dict())
```

```powershell
# Run via CLI
.\.venv\Scripts\python.exe cli.py --pre sample_images/pre_disaster.png --post sample_images/post_disaster.png --gsd 0.5
```
