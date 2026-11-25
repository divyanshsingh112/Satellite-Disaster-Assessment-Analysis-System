"""
Tests for the shared Rich Terminal UI module (terminal_ui.py).
"""

import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from disaster_assessment.analytics.severity_engine import SeverityResult
from disaster_assessment.feature_status import (
    FeatureStatusRegistry,
    Status,
    check_feature_status,
)
from disaster_assessment.inference.building_damage_inference import DamageAssessmentOutput
from disaster_assessment.pipeline.disaster_analyzer import DisasterReport
from disaster_assessment.preprocessing.image_alignment import AlignmentReport
from disaster_assessment.terminal_ui import (
    DryRunTrainingUI,
    build_analysis_renderable,
    build_feature_status_renderable,
    create_console,
    get_effective_width,
    render_analysis_report,
    render_feature_status,
    shorten_path,
    should_use_plain,
    supports_unicode,
)


def _render_to_text(renderable, width: int = 96, force_ascii: bool = False) -> str:
    buf = io.StringIO()
    console, _ = create_console(
        width=width,
        force_ascii=force_ascii,
        force_terminal=True,
        stream=buf,
    )
    console.print(renderable)
    return buf.getvalue()


class _FakeTTY(io.StringIO):
    def __init__(self, encoding: str = "utf-8", is_tty: bool = True):
        super().__init__()
        self._encoding = encoding
        self._is_tty = is_tty

    @property
    def encoding(self):
        return self._encoding

    def isatty(self) -> bool:
        return self._is_tty


class TestPlainAndEnvironmentDetection:
    def test_should_use_plain_flag(self):
        tty = _FakeTTY(is_tty=True)
        assert should_use_plain(plain=True, stream=tty) is True

    def test_should_use_plain_non_tty(self):
        non_tty = _FakeTTY(is_tty=False)
        assert should_use_plain(plain=False, stream=non_tty) is True

    def test_should_use_plain_no_color(self, monkeypatch):
        tty = _FakeTTY(is_tty=True)
        monkeypatch.setenv("NO_COLOR", "1")
        assert should_use_plain(plain=False, stream=tty) is True

    def test_styled_when_tty_and_no_plain(self, monkeypatch):
        tty = _FakeTTY(is_tty=True)
        monkeypatch.delenv("NO_COLOR", raising=False)
        assert should_use_plain(plain=False, stream=tty) is False

    def test_ascii_fallback_detection_for_cp1252(self):
        cp_stream = _FakeTTY(encoding="cp1252", is_tty=True)
        utf_stream = _FakeTTY(encoding="utf-8", is_tty=True)
        assert supports_unicode(cp_stream) is False
        assert supports_unicode(utf_stream) is True

    def test_shorten_path_middle_and_none(self):
        assert shorten_path(None) == "n/a"
        assert shorten_path("") == "n/a"
        short = "sample_images/pre.png"
        assert shorten_path(short, max_len=50) == short
        long_path = r"C:\Users\Administrator\Documents\Satellite\Projects\2026\Floods\RegionA\subregion\very_long_filename_pre_disaster.png"
        out = shorten_path(long_path, max_len=45)
        assert len(out) <= 45
        assert "..." in out
        assert out.endswith("pre_disaster.png")

    def test_effective_width_clamped(self):
        assert get_effective_width(max_width=100) <= 100


class TestAnalysisReportUI:
    def _make_partial_report(self) -> DisasterReport:
        report = DisasterReport()
        report.alignment = AlignmentReport(
            pre_original_shape=(512, 512, 3),
            post_original_shape=(512, 512, 3),
            output_shape=(256, 256, 3),
            was_resized=True,
        )
        report.change_mode = "unavailable"
        report.flood_mode = "unavailable"
        report.landcover_mode = "heuristic"
        report.damage_mode = "estimated"
        report.vegetation_loss_percentage = 2.45
        report.water_expansion_percentage = 0.0
        report.damage_output = DamageAssessmentOutput(
            damage_mode="estimated",
            model_available=False,
            overall_damage_score=0.0,
        )
        report.severity = SeverityResult(
            total_score=0.2,
            severity_level="LOW",
            explanation="Score = vegetation_loss(2.5% x 0.10 = 0.2) = 0.2",
        )
        report.model_validations = {
            "change_detection": {"status": "WEIGHTS_MISSING", "inference_mode": "unavailable"},
            "flood_detection": {"status": "WEIGHTS_MISSING", "inference_mode": "unavailable"},
            "building_damage": {"status": "WEIGHTS_MISSING", "inference_mode": "estimated"},
        }
        report.warnings = [
            "Alignment: PRE image resized from 512x512 to 256x256",
            "Alignment: POST image resized from 512x512 to 256x256",
            "Alignment: POST image resized from 512x512 to 256x256",  # duplicate
            "Change detection unavailable: no validated trained checkpoint. Change percentage set to 0.0%.",
            "Land-cover uses HSV color heuristic, not a trained segmentation model. Results are approximate.",
            "Severity score excludes unavailable components: change_detection, flood_detection. Actual severity may be higher.",
        ]
        return report

    def test_partial_report_badges_warnings_and_missing_optionals(self):
        report = self._make_partial_report()
        renderable = build_analysis_renderable(
            report,
            pre_path="sample_images/pre_disaster.png",
            post_path="sample_images/post_disaster.png",
            requested_mode="auto",
            gsd=None,
            json_out=None,
            save_vis=None,
            use_unicode=True,
            width=96,
        )
        rendered = _render_to_text(renderable, width=96)
        assert "PARTIAL RESULT" in rendered
        assert "excludes unavailable components" in rendered
        assert "[UNAVAILABLE]" in rendered
        assert "[HEURISTIC]" in rendered
        assert "[ESTIMATED]" in rendered
        assert "siamese_unet.pth" in rendered
        assert "flood_unet.pth" in rendered
        assert "best_damage_model.pth" in rendered
        assert "n/a" in rendered
        assert "PRE & POST images resized from 512x512 to 256x256" in rendered
        assert rendered.count("resized from 512x512 to 256x256") == 1
        assert "Alignment" in rendered
        assert "Models" in rendered
        assert "Accuracy" in rendered
        assert "Outputs & Next Step" not in rendered

    def test_full_trained_report_hides_partial_and_zero_warnings_hides_section(self):
        report = DisasterReport()
        report.alignment = AlignmentReport(
            pre_original_shape=(256, 256, 3),
            post_original_shape=(256, 256, 3),
            output_shape=(256, 256, 3),
        )
        report.change_mode = "trained"
        report.change_percentage = 14.5
        report.flood_mode = "trained"
        report.flood_percentage = 22.0
        report.landcover_mode = "trained"
        report.vegetation_loss_percentage = 8.0
        report.water_expansion_percentage = 12.0
        report.damage_mode = "trained"
        report.damage_output = DamageAssessmentOutput(
            damage_mode="trained",
            model_available=True,
            overall_damage_score=45.0,
            undamaged_percentage=55.0,
            minor_damage_percentage=20.0,
            major_damage_percentage=15.0,
            destroyed_percentage=10.0,
        )
        report.severity = SeverityResult(total_score=58.0, severity_level="HIGH")
        report.model_validations = {
            "change_detection": {"status": "READY", "inference_mode": "trained"},
            "flood_detection": {"status": "READY", "inference_mode": "trained"},
            "building_damage": {"status": "READY", "inference_mode": "trained"},
        }
        report.warnings = []

        renderable = build_analysis_renderable(
            report,
            pre_path="pre.png",
            post_path="post.png",
            requested_mode="trained",
            gsd=0.5,
            use_unicode=False,
            width=60,  # Narrow terminal + ASCII mode
        )
        rendered = _render_to_text(renderable, width=60, force_ascii=True)
        assert "PARTIAL RESULT" not in rendered
        assert "Warnings" not in rendered
        assert "HIGH" in rendered
        assert "[MEASURED]" in rendered

    def test_missing_severity_and_alignment_does_not_crash(self):
        report = DisasterReport()
        report.warnings = []
        renderable = build_analysis_renderable(report, use_unicode=False, width=80)
        rendered = _render_to_text(renderable, width=80, force_ascii=True)
        assert "n/a" in rendered

    def test_plain_mode_reproduces_original_summary_and_exports_svg(self, tmp_path):
        report = self._make_partial_report()
        buf = io.StringIO()
        svg_path = tmp_path / "report.svg"
        render_analysis_report(
            report,
            pre_path="pre.png",
            post_path="post.png",
            requested_mode="auto",
            gsd=None,
            json_out="out.json",
            save_vis="vis.png",
            export_svg=str(svg_path),
            plain=True,
            stream=buf,
        )
        output = buf.getvalue()
        assert "[CLI] Loading PRE image:  pre.png" in output
        assert report.summary() in output
        assert "[CLI] Visualization overlay saved to: vis.png" in output
        assert "[CLI] JSON report saved to: out.json" in output
        assert svg_path.is_file()
        assert "<svg" in svg_path.read_text(encoding="utf-8")


class TestFeatureStatusUI:
    def test_dynamic_counts_and_categories(self):
        registry = FeatureStatusRegistry()
        registry.register("change_detection", Status.READY, "Model validated.")
        registry.register("flood_detection", Status.WEIGHTS_MISSING, "Missing weights.")
        registry.register("area_calculation", Status.READY, "Area calculator ready.")
        registry.register("multispectral_indices", Status.READY, "Indices ready.")
        registry.register("onnx_export", Status.DEPENDENCY_MISSING, "onnx missing.")
        registry.register("digital_twin", Status.EXPERIMENTAL, "Experimental engine.")

        rendered = _render_to_text(
            build_feature_status_renderable(registry, use_unicode=True, width=96),
            width=96,
        )
        assert "Total: 6 modules" in rendered
        assert "READY: 3" in rendered
        assert "WEIGHTS MISSING: 1" in rendered
        assert "EXPERIMENTAL: 1" in rendered
        assert "DEPENDENCY MISSING: 1" in rendered
        assert "Core Engines" in rendered
        assert "Geospatial and GIS" in rendered
        assert "Remote Sensing" in rendered
        assert "Training and Export" in rendered
        assert "Experimental and Optional" in rendered

    def test_plain_feature_status_matches_registry_summary_table(self):
        registry = check_feature_status()
        buf = io.StringIO()
        render_feature_status(registry, plain=True, stream=buf)
        assert buf.getvalue().strip() == registry.summary_table().strip()


class TestDryRunTrainingUI:
    def test_styled_dry_run_output_and_plain_fallback(self):
        tty = _FakeTTY(encoding="utf-8", is_tty=True)
        old_no_color = os.environ.pop("NO_COLOR", None)
        try:
            ui = DryRunTrainingUI(plain=False, stream=tty)
            ui.start(device="cpu", epochs=1, batch_size=4, train_samples=8, val_samples=2)
            with ui.epoch_progress(1, 1, 2) as advance:
                advance()
                advance()
            ui.log_epoch(
                epoch=1,
                epochs=1,
                train_loss=0.95,
                train_miou=18.3,
                train_acc=65.8,
                val_loss=None,
                val_miou=None,
                val_acc=None,
            )
            ui.finish(
                device="cpu",
                train_samples=8,
                val_samples=2,
                best_model_path="runs/dry_run/weights/best_damage_model.pth",
            )
            out = tty.getvalue()
            assert "SMOKE TEST: synthetic data, metrics are not meaningful." in out
            assert "runs/dry_run/" in out
            assert "n/a" in out
        finally:
            if old_no_color is not None:
                os.environ["NO_COLOR"] = old_no_color

    def test_plain_dry_run_reproduces_original_format(self):
        buf = io.StringIO()
        ui = DryRunTrainingUI(plain=True, stream=buf)
        ui.show_data_generation("runs/dry_run/data")
        ui.start(device="cpu", epochs=1, batch_size=4, train_samples=8, val_samples=2)
        ui.log_epoch(
            epoch=1,
            epochs=1,
            train_loss=0.9513,
            train_miou=18.3,
            train_acc=65.8,
            val_loss=1.0595,
            val_miou=0.9,
            val_acc=3.6,
        )
        ui.finish(
            device="cpu",
            train_samples=8,
            val_samples=2,
            best_model_path="runs/dry_run/weights/best_damage_model.pth",
        )
        out = buf.getvalue()
        assert "[Dry Run] Generating synthetic training data in runs/dry_run/data ..." in out
        assert "BUILDING DAMAGE ASSESSMENT TRAINING PIPELINE" in out
        assert "Epoch [01/01] Train Loss: 0.9513 | Train mIoU: 18.3% | Train Acc: 65.8% | Val Loss: 1.0595 | Val mIoU: 0.9% | Val Acc: 3.6%" in out
        assert "Training Complete. Best model saved to: runs/dry_run/weights/best_damage_model.pth" in out
