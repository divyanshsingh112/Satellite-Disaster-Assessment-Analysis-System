"""
Shared Rich Terminal UI for the Satellite Disaster Assessment System.

Presentation layer only: formats outputs from DisasterReport, FeatureStatusRegistry,
and building damage dry-run training without altering any underlying computation,
JSON schemas, or file outputs.

Supports:
    - Styled Rich panels, tables, gauge bars, and live progress bars
    - Automatic plain-text fallback for --plain, NO_COLOR, and non-TTY streams
    - Terminal width adaptation (capped at 100 columns) including narrow terminals
    - Automatic ASCII box/glyph fallback if Unicode encoding fails (e.g. Windows cp1252)
    - Optional SVG export for presentation slides
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from contextlib import nullcontext
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from rich import box
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback when rich is not installed
    RICH_AVAILABLE = False
    box = None  # type: ignore[assignment]
    Console = None  # type: ignore[assignment,misc]
    Group = None  # type: ignore[assignment,misc]
    Panel = None  # type: ignore[assignment,misc]
    Progress = None  # type: ignore[assignment,misc]
    Table = None  # type: ignore[assignment,misc]
    Text = None  # type: ignore[assignment,misc]


MAX_TERMINAL_WIDTH = 100
NARROW_TERMINAL_THRESHOLD = 72
_UNICODE_PROBE = "╭─│╰╯█░✓✗⚠●◐○◇△▸"


THEME_COLORS: Dict[str, str] = {
    "accent": "cyan",
    "accent_bold": "bold cyan",
    "muted": "dim",
    "low": "green",
    "moderate": "yellow",
    "high": "orange1",
    "critical": "bold red",
    "measured": "bold green",
    "heuristic": "bold yellow",
    "estimated": "bold cyan",
    "unavailable": "dim",
    "ready": "green",
    "weights_missing": "orange1",
    "arch_only": "cyan",
    "experimental": "magenta",
    "dep_missing": "red",
}


def should_use_plain(plain: bool = False, stream: Any = None) -> bool:
    """Return True when styled Rich output should be bypassed for original plain text."""
    if plain or not RICH_AVAILABLE:
        return True
    if os.environ.get("NO_COLOR", "") != "":
        return True
    target = sys.stdout if stream is None else stream
    isatty = getattr(target, "isatty", None)
    if callable(isatty):
        try:
            return not bool(isatty())
        except Exception:
            return True
    return True


def supports_unicode(stream: Any = None) -> bool:
    """Check whether the output stream encoding can represent Unicode box/glyph chars."""
    target = sys.stdout if stream is None else stream
    encoding = getattr(target, "encoding", None) or "ascii"
    try:
        _UNICODE_PROBE.encode(encoding, errors="strict")
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def get_effective_width(max_width: int = MAX_TERMINAL_WIDTH) -> int:
    """Detect terminal width and clamp to [40, max_width]."""
    try:
        cols = shutil.get_terminal_size((80, 24)).columns
    except Exception:
        cols = 80
    return max(40, min(int(cols), max_width))


def is_narrow_terminal(width: Optional[int] = None) -> bool:
    """Return True when terminal width is narrow enough to warrant compact layouts."""
    effective = width if width is not None else get_effective_width()
    return effective < NARROW_TERMINAL_THRESHOLD


def shorten_path(path: Optional[str], max_len: int = 56) -> str:
    """Shorten long filesystem paths in the middle while preserving root and filename."""
    if path is None or str(path).strip() == "":
        return "n/a"
    text = str(path)
    if len(text) <= max_len:
        return text
    if max_len <= 9:
        return text[:max_len]

    ellipsis = "..."
    avail = max_len - len(ellipsis)
    head_len = max(4, avail // 3)
    tail_len = max(4, avail - head_len)
    return f"{text[:head_len]}{ellipsis}{text[-tail_len:]}"


def create_console(
    *,
    record: bool = False,
    width: Optional[int] = None,
    force_ascii: bool = False,
    force_terminal: Optional[bool] = None,
    stream: Any = None,
) -> Tuple[Any, bool]:
    """Create a Rich Console configured for Windows/cross-platform width and encoding."""
    effective_width = width if width is not None else get_effective_width()
    use_unicode = False if force_ascii else supports_unicode(stream)
    is_custom_stream = stream is not None and stream is not sys.stdout
    kwargs: Dict[str, Any] = {
        "width": effective_width,
        "record": record,
        "soft_wrap": False,
    }
    if is_custom_stream or os.environ.get("WT_SESSION") or use_unicode:
        kwargs["legacy_windows"] = False
    if is_custom_stream and width is not None:
        kwargs["_environ"] = {**os.environ, "COLUMNS": str(effective_width)}
    if stream is not None:
        kwargs["file"] = stream
    if force_terminal is not None:
        kwargs["force_terminal"] = force_terminal
    console = Console(**kwargs)
    return console, use_unicode


def _box_style(use_unicode: bool):
    return box.ROUNDED if use_unicode else box.ASCII


def _print_with_fallback(
    render_fn: Callable[[bool, int], Any],
    *,
    width: Optional[int] = None,
    export_svg_path: Optional[str] = None,
    svg_title: str = "Satellite Disaster Assessment",
    stream: Any = None,
    emit_to_stream: bool = True,
) -> None:
    """Render Rich content safely, falling back to ASCII on UnicodeEncodeError."""
    effective_width = width if width is not None else get_effective_width()
    use_unicode = supports_unicode(stream)

    if emit_to_stream:
        console, _ = create_console(
            record=bool(export_svg_path),
            width=effective_width,
            force_ascii=not use_unicode,
            stream=stream,
        )
        renderable = render_fn(use_unicode, effective_width)
        try:
            console.print(renderable)
        except UnicodeEncodeError:
            console, _ = create_console(
                record=bool(export_svg_path),
                width=effective_width,
                force_ascii=True,
                stream=stream,
            )
            renderable = render_fn(False, effective_width)
            console.print(renderable)

        if export_svg_path:
            parent = os.path.dirname(os.path.abspath(export_svg_path))
            if parent:
                os.makedirs(parent, exist_ok=True)
            console.save_svg(export_svg_path, title=svg_title)
    elif export_svg_path:
        # Plain stdout requested/piped, but SVG export was also requested:
        # render off-screen using a recording console without printing to stdout.
        svg_console = Console(
            width=effective_width,
            record=True,
            file=open(os.devnull, "w", encoding="utf-8"),
            force_terminal=True,
        )
        try:
            svg_console.print(render_fn(True, effective_width))
            parent = os.path.dirname(os.path.abspath(export_svg_path))
            if parent:
                os.makedirs(parent, exist_ok=True)
            svg_console.save_svg(export_svg_path, title=svg_title)
        finally:
            svg_console.file.close()


# ---------------------------------------------------------------------------
# 1. Analysis Report UI (cli.py --pre/--post)
# ---------------------------------------------------------------------------

def _severity_style(level: str) -> str:
    lvl = (level or "").upper()
    if lvl == "LOW":
        return THEME_COLORS["low"]
    if lvl == "MODERATE":
        return THEME_COLORS["moderate"]
    if lvl == "HIGH":
        return THEME_COLORS["high"]
    if lvl == "CRITICAL":
        return THEME_COLORS["critical"]
    return "white"


def _source_badge(source: str) -> Text:
    src = source.upper()
    style_map = {
        "MEASURED": THEME_COLORS["measured"],
        "HEURISTIC": THEME_COLORS["heuristic"],
        "ESTIMATED": THEME_COLORS["estimated"],
        "UNAVAILABLE": THEME_COLORS["unavailable"],
    }
    return Text(f"[{src}]", style=style_map.get(src, "white"))


def _model_status_chip(status: str, use_unicode: bool) -> Text:
    st = (status or "UNKNOWN").upper()
    ok_icon = "●" if use_unicode else "*"
    warn_icon = "○" if use_unicode else "-"
    err_icon = "✗" if use_unicode else "!"

    if st == "READY":
        return Text(f"{ok_icon} READY", style="bold green")
    if st == "WEIGHTS_MISSING":
        return Text(f"{warn_icon} WEIGHTS MISSING", style="bold orange1")
    if st in ("DEGENERATE", "VALIDATION_FAILED", "CHECKPOINT_INVALID", "ARCHITECTURE_MISMATCH"):
        return Text(f"{err_icon} {st}", style="bold red")
    return Text(f"{warn_icon} {st}", style="yellow")


def _extract_unavailable_components(report: Any) -> List[str]:
    unavailable: List[str] = []
    if getattr(report, "change_mode", "unavailable") == "unavailable":
        unavailable.append("change_detection")
    if getattr(report, "flood_mode", "unavailable") == "unavailable":
        unavailable.append("flood_detection")
    if getattr(report, "damage_mode", "estimated") == "unavailable":
        unavailable.append("building_damage")
    if getattr(report, "landcover_mode", "heuristic") == "unavailable":
        unavailable.append("land_cover")
    return unavailable


def _format_shape(shape: Optional[Sequence[int]]) -> str:
    if not shape or len(shape) < 2 or not shape[0] or not shape[1]:
        return "n/a"
    return f"{int(shape[1])}x{int(shape[0])}"


def _build_gauge_bar(score: float, level: str, bar_width: int, use_unicode: bool) -> Text:
    clamped = max(0.0, min(100.0, float(score)))
    filled = int(round((clamped / 100.0) * bar_width))
    empty = max(0, bar_width - filled)
    fill_char = "█" if use_unicode else "#"
    empty_char = "░" if use_unicode else "-"
    style = _severity_style(level)

    bar = Text()
    bar.append("[", style="dim")
    bar.append(fill_char * filled, style=style)
    bar.append(empty_char * empty, style="dim")
    bar.append("]", style="dim")
    bar.append(f"  {clamped:5.1f} / 100  ", style=f"bold {style}" if "bold" not in style else style)
    bar.append(f" {level.upper()} ", style=f"bold black on {style.replace('bold ', '')}")
    return bar


def _group_and_deduplicate_warnings(warnings: Iterable[str]) -> Dict[str, List[str]]:
    """Deduplicate warnings, merge PRE/POST alignment pairs, and group under short headings."""
    seen = set()
    unique: List[str] = []
    for raw in warnings:
        w = str(raw).strip()
        if w and w not in seen:
            seen.add(w)
            unique.append(w)

    grouped: Dict[str, List[str]] = {"Alignment": [], "Models": [], "Accuracy": []}

    # Merge PRE & POST alignment resize warnings when both appear
    resize_re = re.compile(
        r"^Alignment:\s*(PRE|POST)\s+image\s+resized\s+from\s+([^\s]+)\s+to\s+([^\s]+)$",
        re.IGNORECASE,
    )
    pre_resize: Optional[Tuple[str, str]] = None
    post_resize: Optional[Tuple[str, str]] = None
    remaining: List[str] = []

    for w in unique:
        m = resize_re.match(w)
        if m:
            side, src_sz, dst_sz = m.group(1).upper(), m.group(2), m.group(3)
            if side == "PRE":
                pre_resize = (src_sz, dst_sz)
            else:
                post_resize = (src_sz, dst_sz)
        else:
            remaining.append(w)

    if pre_resize and post_resize:
        if pre_resize == post_resize:
            grouped["Alignment"].append(
                f"PRE & POST images resized from {pre_resize[0]} to {pre_resize[1]}"
            )
        else:
            grouped["Alignment"].append(
                f"PRE ({pre_resize[0]}) -> {pre_resize[1]} and POST ({post_resize[0]}) -> {post_resize[1]} resized"
            )
    elif pre_resize:
        grouped["Alignment"].append(f"PRE image resized from {pre_resize[0]} to {pre_resize[1]}")
    elif post_resize:
        grouped["Alignment"].append(f"POST image resized from {post_resize[0]} to {post_resize[1]}")

    for w in remaining:
        low = w.lower()
        if low.startswith("alignment:") or low.startswith("geotiff:") or "align" in low or "geotiff" in low:
            cleaned = re.sub(r"^Alignment:\s*", "", w, flags=re.IGNORECASE)
            grouped["Alignment"].append(cleaned)
        elif (
            "checkpoint" in low
            or "weights" in low
            or "validation failed" in low
            or "unavailable:" in low
            or "no trained damage model" in low
        ):
            grouped["Models"].append(w)
        else:
            grouped["Accuracy"].append(w)

    return {k: v for k, v in grouped.items() if v}


def build_analysis_renderable(
    report: Any,
    *,
    pre_path: Optional[str] = None,
    post_path: Optional[str] = None,
    requested_mode: Optional[str] = None,
    gsd: Optional[float] = None,
    geotiff_path: Optional[str] = None,
    json_out: Optional[str] = None,
    save_vis: Optional[str] = None,
    export_svg: Optional[str] = None,
    expected_weights: Optional[Dict[str, str]] = None,
    timestamp: Optional[str] = None,
    use_unicode: bool = True,
    width: int = 96,
):
    """Build the Rich Group renderable for the disaster analysis report."""
    bstyle = _box_style(use_unicode)
    narrow = is_narrow_terminal(width)
    ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path_budget = max(24, width - (26 if narrow else 34))

    # Resolve modes dynamically from report
    resolved_damage_mode = getattr(report, "damage_mode", "estimated") or "estimated"
    if requested_mode and requested_mode != resolved_damage_mode:
        damage_mode_label = f"{requested_mode} -> {resolved_damage_mode}"
    else:
        damage_mode_label = resolved_damage_mode

    georef = getattr(getattr(report, "flood_result", None), "georeference", None)
    if geotiff_path or (georef is not None and getattr(georef, "source_type", "none") == "geotiff"):
        analysis_mode_label = "PRE/POST Pair (GeoTIFF)"
    elif gsd is not None or (georef is not None and getattr(georef, "source_type", "none") == "user_supplied"):
        analysis_mode_label = "PRE/POST Pair (GSD-calibrated)"
    else:
        analysis_mode_label = "PRE/POST Pair (Pixel-based)"

    # --- Header Banner ---
    header_grid = Table.grid(expand=True)
    header_grid.add_column(ratio=1)
    if not narrow:
        header_grid.add_column(justify="right")
        header_grid.add_row(
            Text("Satellite Disaster Assessment System", style="bold cyan"),
            Text(ts, style="dim"),
        )
        header_grid.add_row(
            Text(f"Analysis Mode: {analysis_mode_label}", style="white"),
            Text(f"Damage Mode: {damage_mode_label}", style="bold white"),
        )
    else:
        header_grid.add_row(Text("Satellite Disaster Assessment", style="bold cyan"))
        header_grid.add_row(Text(f"Run: {ts} | Damage: {damage_mode_label}", style="dim"))
        header_grid.add_row(Text(f"Analysis: {analysis_mode_label}", style="white"))

    header_panel = Panel(header_grid, box=bstyle, border_style="cyan", padding=(0, 1))

    # --- Inputs Panel ---
    alignment = getattr(report, "alignment", None)
    pre_res = _format_shape(getattr(alignment, "pre_original_shape", None))
    post_res = _format_shape(getattr(alignment, "post_original_shape", None))
    out_res = _format_shape(getattr(alignment, "output_shape", None))
    if pre_res == "n/a" and post_res == "n/a":
        res_text = "n/a"
    elif pre_res == post_res:
        res_text = f"{pre_res} (PRE & POST)" + (f" -> {out_res} aligned" if out_res != "n/a" and out_res != pre_res else "")
    else:
        res_text = f"PRE {pre_res}, POST {post_res}" + (f" -> {out_res}" if out_res != "n/a" else "")

    eff_gsd = gsd
    if eff_gsd is None and georef is not None:
        eff_gsd = getattr(georef, "pixel_width_m", None)
    gsd_text = f"{eff_gsd} m/px" if eff_gsd is not None else "n/a"

    inputs_table = Table.grid(padding=(0, 2), expand=True)
    inputs_table.add_column(style="bold", width=16 if not narrow else 13)
    inputs_table.add_column(ratio=1)
    inputs_table.add_row("PRE Image", shorten_path(pre_path, path_budget))
    inputs_table.add_row("POST Image", shorten_path(post_path, path_budget))
    inputs_table.add_row("Resolution", res_text)
    inputs_table.add_row("GSD", gsd_text)
    if geotiff_path:
        inputs_table.add_row("GeoTIFF", shorten_path(geotiff_path, path_budget))

    inputs_panel = Panel(
        inputs_table,
        title="[bold]Inputs[/bold]",
        title_align="left",
        box=bstyle,
        border_style="blue",
        padding=(0, 1),
    )

    # --- Severity Panel ---
    unavailable_components = _extract_unavailable_components(report)
    sev = getattr(report, "severity", None)
    sev_lines: List[Any] = []

    if sev is not None:
        bar_width = max(16, min(36, width - (36 if not narrow else 28)))
        sev_lines.append(_build_gauge_bar(sev.total_score, sev.severity_level, bar_width, use_unicode))
        if getattr(sev, "explanation", None):
            sev_lines.append(Text(sev.explanation, style="dim"))
    else:
        sev_lines.append(Text("Severity score: n/a", style="dim"))

    if unavailable_components:
        warn_icon = "⚠ " if use_unicode else "! "
        badge_line = Text()
        badge_line.append(" PARTIAL RESULT ", style="bold black on yellow")
        badge_line.append(
            f"  {warn_icon}Score excludes unavailable components: {', '.join(unavailable_components)}.",
            style="yellow",
        )
        sev_lines.append(Text(""))
        sev_lines.append(badge_line)

    severity_panel = Panel(
        Group(*sev_lines),
        title="[bold]Severity[/bold]",
        title_align="left",
        box=bstyle,
        border_style="yellow" if unavailable_components else _severity_style(sev.severity_level if sev else "LOW").replace("bold ", ""),
        padding=(0, 1),
    )

    # --- Metrics Table ---
    metrics_table = Table(
        title="Metrics",
        title_style="bold",
        title_justify="left",
        box=bstyle,
        border_style="bright_black",
        expand=True,
        show_header=True,
        header_style="bold cyan",
        padding=(0, 1),
    )
    metrics_table.add_column("Metric", style="bold", no_wrap=not narrow)
    metrics_table.add_column("Value", justify="right")
    metrics_table.add_column("Source", justify="center", no_wrap=True)
    if not narrow:
        metrics_table.add_column("Details", style="dim")

    def add_metric_row(name: str, value: str, source: str, details: str = "", dim_value: bool = False):
        val_text = Text(value, style="dim" if dim_value else "white")
        badge = _source_badge(source)
        if narrow:
            metrics_table.add_row(name, val_text, badge)
        else:
            metrics_table.add_row(name, val_text, badge, details)

    # Changed Area
    change_mode = getattr(report, "change_mode", "unavailable")
    if change_mode == "unavailable":
        add_metric_row("Changed Area", "-", "UNAVAILABLE", "Checkpoint missing or invalid", dim_value=True)
    else:
        src = "MEASURED" if change_mode == "trained" else "HEURISTIC"
        add_metric_row("Changed Area", f"{report.change_percentage:.2f}%", src, f"Mode: {change_mode}")

    # Flooded Area
    flood_mode = getattr(report, "flood_mode", "unavailable")
    if flood_mode == "unavailable":
        add_metric_row("Flooded Area", "-", "UNAVAILABLE", "Checkpoint missing or invalid", dim_value=True)
    else:
        src = "MEASURED" if flood_mode == "trained" else "HEURISTIC"
        area_detail = ""
        if getattr(report, "flood_area_m2", None) is not None:
            area_detail = f"{report.flood_area_m2:,.2f} m2 ({report.flood_area_km2:,.6f} km2)"
        else:
            area_detail = getattr(report, "measurement_basis", "")
        add_metric_row("Flooded Area", f"{report.flood_percentage:.2f}%", src, area_detail)

    # Vegetation Loss & Water Expansion (from landcover)
    lc_mode = getattr(report, "landcover_mode", "heuristic")
    if lc_mode == "unavailable":
        add_metric_row("Vegetation Loss", "-", "UNAVAILABLE", "Land-cover unavailable", dim_value=True)
        add_metric_row("Water Expansion", "-", "UNAVAILABLE", "Land-cover unavailable", dim_value=True)
    else:
        lc_src = "MEASURED" if lc_mode == "trained" else "HEURISTIC"
        lc_note = "Trained segmentation" if lc_mode == "trained" else "HSV color heuristic"
        add_metric_row("Vegetation Loss", f"{report.vegetation_loss_percentage:.2f}%", lc_src, lc_note)
        add_metric_row("Water Expansion", f"{report.water_expansion_percentage:.2f}%", lc_src, lc_note)

    # Building Damage
    dmg_out = getattr(report, "damage_output", None)
    bldg_dmg = getattr(report, "building_damage", None)
    dmg_mode = getattr(report, "damage_mode", "estimated")
    if dmg_out is not None:
        dmg_src = "MEASURED" if dmg_out.damage_mode == "trained" else "ESTIMATED"
        if dmg_out.damage_mode == "trained":
            detail = (
                f"Undamaged {dmg_out.undamaged_percentage:.1f}% | "
                f"Minor {dmg_out.minor_damage_percentage:.1f}% | "
                f"Major {dmg_out.major_damage_percentage:.1f}% | "
                f"Destroyed {dmg_out.destroyed_percentage:.1f}%"
            )
        elif dmg_out.estimated_details is not None:
            detail = (
                f"Possible {dmg_out.estimated_details.possible_damage_percentage:.1f}% | "
                f"Severe {dmg_out.estimated_details.severe_damage_percentage:.1f}%"
            )
        else:
            detail = "Structural change heuristic"
        add_metric_row("Building Damage", f"{dmg_out.overall_damage_score:.1f}/100", dmg_src, detail)
    elif bldg_dmg is not None:
        dmg_src = "MEASURED" if dmg_mode == "trained" else "ESTIMATED"
        detail = (
            f"Possible {getattr(bldg_dmg, 'possible_damage_percentage', 0.0):.1f}% | "
            f"Severe {getattr(bldg_dmg, 'severe_damage_percentage', 0.0):.1f}%"
        )
        add_metric_row(
            "Building Damage",
            f"{getattr(bldg_dmg, 'overall_damage_score', 0.0):.1f}/100",
            dmg_src,
            detail,
        )
    else:
        add_metric_row("Building Damage", "-", "UNAVAILABLE", "No damage output", dim_value=True)

    # --- Model Status Table ---
    model_table = Table(
        title="Model Status",
        title_style="bold",
        title_justify="left",
        box=bstyle,
        border_style="bright_black",
        expand=True,
        show_header=True,
        header_style="bold cyan",
        padding=(0, 1),
    )
    model_table.add_column("Model", style="bold", no_wrap=True)
    model_table.add_column("Status", no_wrap=True)
    if not narrow:
        model_table.add_column("Mode", no_wrap=True)
    model_table.add_column("Weight File", style="dim", no_wrap=True)

    default_weight_names = {
        "change_detection": "siamese_unet.pth",
        "flood_detection": "flood_unet.pth",
        "building_damage": "best_damage_model.pth",
    }
    weights_map = expected_weights or default_weight_names
    validations = getattr(report, "model_validations", None) or {}
    model_order = ["change_detection", "flood_detection", "building_damage"]
    for key in validations:
        if key not in model_order:
            model_order.append(key)

    for model_key in model_order:
        val = validations.get(model_key, {})
        st = val.get("status", "UNKNOWN")
        inf_mode = val.get("inference_mode", "n/a")
        w_name = weights_map.get(model_key) or "n/a"
        if w_name != "n/a":
            w_name = os.path.basename(w_name)
        if st == "READY":
            weight_col = f"{w_name} (loaded)"
        else:
            weight_col = w_name

        chip = _model_status_chip(st, use_unicode)
        display_name = model_key.replace("_", " ").title()
        if narrow:
            model_table.add_row(display_name, chip, weight_col)
        else:
            model_table.add_row(display_name, chip, str(inf_mode), weight_col)

    sections: List[Any] = [
        header_panel,
        inputs_panel,
        severity_panel,
        metrics_table,
        model_table,
    ]

    # --- Warnings (hidden when zero warnings) ---
    raw_warnings = getattr(report, "warnings", None) or []
    grouped_warnings = _group_and_deduplicate_warnings(raw_warnings)
    if grouped_warnings:
        bullet = "•" if use_unicode else "-"
        warn_lines: List[Any] = []
        for idx, (group_name, items) in enumerate(grouped_warnings.items()):
            if idx > 0:
                warn_lines.append(Text(""))
            warn_lines.append(Text(group_name, style="bold yellow"))
            for item in items:
                warn_lines.append(Text(f"  {bullet} {item}", style="white"))
        sections.append(
            Panel(
                Group(*warn_lines),
                title="[bold yellow]Warnings[/bold yellow]",
                title_align="left",
                box=bstyle,
                border_style="yellow",
                padding=(0, 1),
            )
        )

    return Group(*sections)


def render_analysis_report(
    report: Any,
    *,
    pre_path: Optional[str] = None,
    post_path: Optional[str] = None,
    requested_mode: Optional[str] = None,
    gsd: Optional[float] = None,
    geotiff_path: Optional[str] = None,
    json_out: Optional[str] = None,
    save_vis: Optional[str] = None,
    export_svg: Optional[str] = None,
    expected_weights: Optional[Dict[str, str]] = None,
    plain: bool = False,
    stream: Any = None,
) -> None:
    """Render the PRE/POST disaster analysis report using Rich or original plain output."""
    use_plain = should_use_plain(plain, stream=stream)
    if use_plain:
        out = sys.stdout if stream is None else stream
        print(f"[CLI] Loading PRE image:  {pre_path}", file=out)
        print(f"[CLI] Loading POST image: {post_path}", file=out)
        print(f"[CLI] Running Disaster Assessment (Mode: {requested_mode}, GSD: {gsd} m/px)...", file=out)
        print("\n" + report.summary(), file=out)
        if save_vis:
            print(f"\n[CLI] Visualization overlay saved to: {save_vis}", file=out)
        if json_out:
            print(f"[CLI] JSON report saved to: {json_out}", file=out)

        if export_svg and RICH_AVAILABLE:
            _print_with_fallback(
                lambda uni, w: build_analysis_renderable(
                    report,
                    pre_path=pre_path,
                    post_path=post_path,
                    requested_mode=requested_mode,
                    gsd=gsd,
                    geotiff_path=geotiff_path,
                    json_out=json_out,
                    save_vis=save_vis,
                    export_svg=export_svg,
                    expected_weights=expected_weights,
                    use_unicode=uni,
                    width=w,
                ),
                export_svg_path=export_svg,
                svg_title="Satellite Disaster Assessment Report",
                emit_to_stream=False,
            )
        return

    _print_with_fallback(
        lambda uni, w: build_analysis_renderable(
            report,
            pre_path=pre_path,
            post_path=post_path,
            requested_mode=requested_mode,
            gsd=gsd,
            geotiff_path=geotiff_path,
            json_out=json_out,
            save_vis=save_vis,
            export_svg=export_svg,
            expected_weights=expected_weights,
            use_unicode=uni,
            width=w,
        ),
        export_svg_path=export_svg,
        svg_title="Satellite Disaster Assessment Report",
        stream=stream,
        emit_to_stream=True,
    )


# ---------------------------------------------------------------------------
# 2. Feature-Status UI (DL-SatelliteImagery/cli.py feature-status)
# ---------------------------------------------------------------------------

FEATURE_CATEGORIES: List[Tuple[str, Tuple[str, ...]]] = [
    (
        "Core Engines",
        (
            "land_cover_segmentation",
            "change_detection",
            "flood_detection",
            "building_damage",
            "severity_scoring",
            "land_change_metrics",
        ),
    ),
    (
        "Geospatial and GIS",
        (
            "area_calculation",
            "large_geotiff_tiling",
            "gis_vector_export",
            "dem_analysis",
            "interactive_map_ui",
        ),
    ),
    (
        "Remote Sensing",
        (
            "multispectral_indices",
            "sar_processing",
            "sar_optical_fusion",
        ),
    ),
    (
        "Training and Export",
        (
            "training_pipeline",
            "onnx_export",
            "foundation_models",
        ),
    ),
    (
        "Experimental and Optional",
        (
            "flood_depth_estimation",
            "rag_copilot",
            "data_ingestion",
            "digital_twin",
        ),
    ),
]


def _status_bucket(status_value: str) -> str:
    """Map FeatureStatus enum string to summary-bar bucket label."""
    val = (status_value or "").upper()
    if val in ("READY", "AVAILABLE", "TRAINED_MODEL", "COMPLETED", "LIVE_DATA_CONNECTED"):
        return "READY"
    if val in ("HEURISTIC_ONLY", "STATIC_DATA_MODE"):
        return "HEURISTIC"
    if val == "WEIGHTS_MISSING":
        return "WEIGHTS MISSING"
    if val == "IMPLEMENTED_ARCHITECTURE":
        return "ARCHITECTURE ONLY"
    if val == "EXPERIMENTAL":
        return "EXPERIMENTAL"
    if val in ("DEPENDENCY_MISSING", "NOT_CONFIGURED", "AUTH_REQUIRED", "INSUFFICIENT_INPUT", "UNAVAILABLE", "FAILED"):
        return "DEPENDENCY MISSING"
    return val or "UNKNOWN"


def _feature_status_style(bucket: str, use_unicode: bool) -> Tuple[str, str]:
    """Return (icon_and_label, rich_style) for a feature status bucket."""
    if bucket == "READY":
        return (f"{'●' if use_unicode else '[OK]'} READY", THEME_COLORS["ready"])
    if bucket == "HEURISTIC":
        return (f"{'◐' if use_unicode else '[H]'} HEURISTIC", THEME_COLORS["heuristic"])
    if bucket == "WEIGHTS MISSING":
        return (f"{'○' if use_unicode else '[W]'} WEIGHTS MISSING", THEME_COLORS["weights_missing"])
    if bucket == "ARCHITECTURE ONLY":
        return (f"{'◇' if use_unicode else '[A]'} ARCH ONLY", THEME_COLORS["arch_only"])
    if bucket == "EXPERIMENTAL":
        return (f"{'△' if use_unicode else '[E]'} EXPERIMENTAL", THEME_COLORS["experimental"])
    if bucket == "DEPENDENCY MISSING":
        return (f"{'✗' if use_unicode else '[!]'} DEP MISSING", THEME_COLORS["dep_missing"])
    return (f"{'?' if use_unicode else '[?]'} {bucket}", "white")


def _truncate_line(text: str, max_len: int) -> str:
    cleaned = " ".join(str(text or "").split())
    if not cleaned:
        return "n/a"
    if len(cleaned) <= max_len:
        return cleaned
    if max_len <= 4:
        return cleaned[:max_len]
    return cleaned[: max_len - 3].rstrip() + "..."


def build_feature_status_renderable(
    registry: Any,
    *,
    use_unicode: bool = True,
    width: int = 96,
):
    """Build the Rich Group renderable for feature-status."""
    bstyle = _box_style(use_unicode)
    narrow = is_narrow_terminal(width)
    all_reports = list(registry.get_all())

    # Compute summary counts dynamically from actual registry entries
    ordered_buckets = [
        "READY",
        "HEURISTIC",
        "WEIGHTS MISSING",
        "ARCHITECTURE ONLY",
        "EXPERIMENTAL",
        "DEPENDENCY MISSING",
    ]
    counts: Dict[str, int] = {b: 0 for b in ordered_buckets}
    for rep in all_reports:
        bucket = _status_bucket(rep.status.value)
        counts[bucket] = counts.get(bucket, 0) + 1

    summary_text = Text()
    summary_text.append(f"Total: {len(all_reports)} modules", style="bold white")
    for bucket, count in counts.items():
        if count == 0 and bucket not in ordered_buckets:
            continue
        _, style = _feature_status_style(bucket, use_unicode)
        summary_text.append("  |  ", style="dim")
        summary_text.append(f"{bucket}: {count}", style=f"bold {style}" if "bold" not in style else style)

    summary_panel = Panel(
        summary_text,
        title="[bold cyan]Feature Status Overview[/bold cyan]",
        title_align="left",
        box=bstyle,
        border_style="cyan",
        padding=(0, 1),
    )

    by_name = {rep.feature: rep for rep in all_reports}
    assigned = set()
    category_tables: List[Any] = [summary_panel]

    desc_max = max(16, width - (52 if not narrow else 40))

    def make_category_table(title: str, reports: List[Any]) -> Any:
        tbl = Table(
            title=title,
            title_style="bold cyan",
            title_justify="left",
            box=bstyle,
            border_style="bright_black",
            expand=True,
            show_header=True,
            header_style="bold",
            padding=(0, 1),
        )
        tbl.add_column("Status", no_wrap=True)
        tbl.add_column("Module", style="bold", no_wrap=not narrow)
        tbl.add_column("Description", style="dim", no_wrap=True, overflow="ellipsis", ratio=1)

        for rep in reports:
            bucket = _status_bucket(rep.status.value)
            label, style = _feature_status_style(bucket, use_unicode)
            mod_name = rep.feature if not narrow else _truncate_line(rep.feature, 20)
            desc = _truncate_line(rep.reason, desc_max)
            tbl.add_row(Text(label, style=style), mod_name, desc)
        return tbl

    for cat_name, feat_names in FEATURE_CATEGORIES:
        items = []
        for fname in feat_names:
            if fname in by_name:
                items.append(by_name[fname])
                assigned.add(fname)
        if cat_name == "Experimental and Optional":
            for rep in all_reports:
                if rep.feature not in assigned:
                    items.append(rep)
                    assigned.add(rep.feature)
        if items:
            category_tables.append(make_category_table(cat_name, items))

    return Group(*category_tables)


def render_feature_status(
    registry: Any,
    *,
    plain: bool = False,
    stream: Any = None,
) -> None:
    """Render the feature-status report using Rich or original plain summary_table."""
    if should_use_plain(plain, stream=stream):
        out = sys.stdout if stream is None else stream
        print(registry.summary_table(), file=out)
        return

    _print_with_fallback(
        lambda uni, w: build_feature_status_renderable(registry, use_unicode=uni, width=w),
        stream=stream,
        emit_to_stream=True,
    )


# ---------------------------------------------------------------------------
# 3. Training Dry-Run UI (train_building_damage.py --dry_run)
# ---------------------------------------------------------------------------

class DryRunTrainingUI:
    """Context/helper for styled --dry_run output with automatic plain fallback."""

    def __init__(
        self,
        *,
        plain: bool = False,
        stream: Any = None,
        data_dir: Optional[str] = None,
    ):
        self.use_plain = should_use_plain(plain, stream=stream)
        self.stream = sys.stdout if stream is None else stream
        self.data_dir = data_dir
        self.width = get_effective_width()
        self.use_unicode = supports_unicode(self.stream)
        self.epoch_records: List[Dict[str, Any]] = []
        self._progress: Optional[Any] = None
        self._epoch_task_id: Optional[Any] = None
        self._batch_task_id: Optional[Any] = None
        self._console: Optional[Any] = None

    def show_data_generation(self, data_dir: str) -> None:
        self.data_dir = data_dir
        if self.use_plain:
            print(f"[Dry Run] Generating synthetic training data in {data_dir} ...", file=self.stream)

    def start(
        self,
        *,
        device: Any,
        epochs: int,
        batch_size: int,
        train_samples: int,
        val_samples: int,
        resume_path: Optional[str] = None,
        start_epoch: int = 1,
    ) -> None:
        if self.use_plain:
            if resume_path:
                print(f"[Training] Resumed from {resume_path} (epoch {start_epoch})", file=self.stream)
            print(f"\n{'='*60}", file=self.stream)
            print("  BUILDING DAMAGE ASSESSMENT TRAINING PIPELINE", file=self.stream)
            print(f"  Device: {device} | Epochs: {epochs} | Batch Size: {batch_size}", file=self.stream)
            print(f"  Training samples: {train_samples}", file=self.stream)
            print(f"{'='*60}\n", file=self.stream)
            return

        console, uni = create_console(width=self.width, force_ascii=not self.use_unicode, stream=self.stream)
        self._console = console
        self.use_unicode = uni
        bstyle = _box_style(uni)

        banner_lines = Group(
            Text("SMOKE TEST: synthetic data, metrics are not meaningful.", style="bold black on yellow"),
            Text(
                f"Device: {device}  |  Epochs: {epochs}  |  Batch Size: {batch_size}  |  "
                f"Train: {train_samples}  |  Val: {val_samples}",
                style="cyan",
            ),
        )
        panel = Panel(
            banner_lines,
            title="[bold cyan]Building Damage Training (Dry Run)[/bold cyan]",
            title_align="left",
            box=bstyle,
            border_style="yellow",
            padding=(0, 1),
        )
        try:
            console.print(panel)
        except UnicodeEncodeError:
            self._console, self.use_unicode = create_console(width=self.width, force_ascii=True, stream=self.stream)
            self._console.print(
                Panel(
                    banner_lines,
                    title="[bold cyan]Building Damage Training (Dry Run)[/bold cyan]",
                    title_align="left",
                    box=box.ASCII,
                    border_style="yellow",
                    padding=(0, 1),
                )
            )

    def epoch_progress(self, epoch: int, total_epochs: int, total_batches: int):
        """Return a context manager providing a live per-epoch batch progress updater."""
        if self.use_plain or self._console is None:
            return nullcontext(lambda advance=1: None)

        progress = Progress(
            SpinnerColumn(spinner_name="dots" if self.use_unicode else "line"),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=None),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self._console,
            transient=True,
        )
        task_id = progress.add_task(f"Epoch {epoch:02d}/{total_epochs:02d}", total=max(total_batches, 1))

        class _ProgressCtx:
            def __enter__(self_ctx):
                progress.__enter__()
                return lambda advance=1: progress.update(task_id, advance=advance)

            def __exit__(self_ctx, exc_type, exc, tb):
                progress.__exit__(exc_type, exc, tb)

        return _ProgressCtx()

    def log_epoch(
        self,
        *,
        epoch: int,
        epochs: int,
        train_loss: float,
        train_miou: float,
        train_acc: float,
        val_loss: Optional[float],
        val_miou: Optional[float],
        val_acc: Optional[float],
    ) -> None:
        if self.use_plain:
            val_msg = ""
            if val_loss is not None and val_miou is not None and val_acc is not None:
                val_msg = f" | Val Loss: {val_loss:.4f} | Val mIoU: {val_miou:.1f}% | Val Acc: {val_acc:.1f}%"
            print(
                f"Epoch [{epoch:02d}/{epochs:02d}] "
                f"Train Loss: {train_loss:.4f} | Train mIoU: {train_miou:.1f}% | Train Acc: {train_acc:.1f}%"
                f"{val_msg}",
                file=self.stream,
            )
            return

        self.epoch_records.append(
            {
                "epoch": f"{epoch:02d}/{epochs:02d}",
                "train_loss": f"{train_loss:.4f}",
                "train_miou": f"{train_miou:.1f}%",
                "train_acc": f"{train_acc:.1f}%",
                "val_loss": f"{val_loss:.4f}" if val_loss is not None else "n/a",
                "val_miou": f"{val_miou:.1f}%" if val_miou is not None else "n/a",
                "val_acc": f"{val_acc:.1f}%" if val_acc is not None else "n/a",
            }
        )

    def finish(
        self,
        *,
        device: Any,
        train_samples: int,
        val_samples: int,
        best_model_path: str,
    ) -> None:
        if self.use_plain:
            print(f"\n✓ Training Complete. Best model saved to: {best_model_path}", file=self.stream)
            return

        narrow = is_narrow_terminal(self.width)
        path_budget = max(24, self.width - (24 if narrow else 32))

        def _build_finish(uni: bool) -> Any:
            bstyle = _box_style(uni)
            epoch_table = Table(
                title="Epoch Results (Synthetic Smoke Test)",
                title_style="bold",
                title_justify="left",
                box=bstyle,
                border_style="bright_black",
                expand=True,
                show_header=True,
                header_style="bold cyan",
                padding=(0, 1),
            )
            epoch_table.add_column("Epoch", justify="center", no_wrap=True)
            epoch_table.add_column("Train Loss", justify="right")
            epoch_table.add_column("Train mIoU", justify="right")
            epoch_table.add_column("Train Acc", justify="right")
            epoch_table.add_column("Val Loss", justify="right")
            epoch_table.add_column("Val mIoU", justify="right")
            epoch_table.add_column("Val Acc", justify="right")

            for rec in self.epoch_records:
                epoch_table.add_row(
                    rec["epoch"],
                    rec["train_loss"],
                    rec["train_miou"],
                    rec["train_acc"],
                    rec["val_loss"],
                    rec["val_miou"],
                    rec["val_acc"],
                )

            summary_grid = Table.grid(padding=(0, 2), expand=True)
            summary_grid.add_column(style="bold", width=18 if not narrow else 14)
            summary_grid.add_column(ratio=1)
            summary_grid.add_row("Device", str(device))
            summary_grid.add_row("Samples", f"Train: {train_samples} | Val: {val_samples}")
            summary_grid.add_row("Checkpoint", shorten_path(best_model_path, path_budget))

            summary_panel = Panel(
                summary_grid,
                title="[bold green]Dry Run Summary[/bold green]",
                title_align="left",
                box=bstyle,
                border_style="green",
                padding=(0, 1),
            )

            reminder_icon = "⚠ " if uni else "! "
            reminder = Text(
                f"{reminder_icon}Reminder: runs/dry_run/ contains synthetic smoke-test artifacts and should be deleted when done.",
                style="yellow",
            )
            return Group(epoch_table, summary_panel, reminder)

        console = self._console or create_console(width=self.width, force_ascii=not self.use_unicode, stream=self.stream)[0]
        try:
            console.print(_build_finish(self.use_unicode))
        except UnicodeEncodeError:
            fb_console, _ = create_console(width=self.width, force_ascii=True, stream=self.stream)
            self.use_unicode = False
            fb_console.print(_build_finish(False))
