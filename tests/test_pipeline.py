from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

import numpy as np

from seismic_first_break_picker.correction import extract_patch, predict_corrected_panel
from seismic_first_break_picker.data import load_split_file
from seismic_first_break_picker.metrics import compute_metric_bundle, summarize_error_ms, valid_error_ms
from seismic_first_break_picker.modeling import load_model_artifact, train_model_with_validation
from seismic_first_break_picker.splits import create_shot_disjoint_splits


class SplitTests(unittest.TestCase):
    def test_shot_disjoint_split_has_no_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            segments_dir = root / "segments"
            splits_dir = root / "splits"
            segments_dir.mkdir()

            manifest = [
                {
                    "segment_id": f"Halfmile_shot{shot_id}_seg{segment_num:03d}",
                    "file": str(segments_dir / f"Halfmile_shot{shot_id}_seg{segment_num:03d}.npz"),
                    "asset_name": "Halfmile",
                    "shot_id": shot_id,
                    "segment_num": segment_num,
                    "trace_count": 100,
                    "sample_count": 751,
                    "valid_label_count": 90,
                    "split_basis": "REC_PEG",
                }
                for shot_id in range(100, 110)
                for segment_num in range(2)
            ]

            manifest_path = segments_dir / "Halfmile_segments_manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            summary = create_shot_disjoint_splits(
                segments_dir=segments_dir,
                out_dir=splits_dir,
                manifest_path=manifest_path,
                train_ratio=0.6,
                val_ratio=0.2,
                seed=42,
            )

            self.assertEqual(summary["overlap"]["train_val"], 0)
            self.assertEqual(summary["overlap"]["train_test"], 0)
            self.assertEqual(summary["overlap"]["val_test"], 0)

            assigned = (
                load_split_file(splits_dir / "train_segments.json")
                + load_split_file(splits_dir / "val_segments.json")
                + load_split_file(splits_dir / "test_segments.json")
            )
            self.assertEqual(len(assigned), len(manifest))
            self.assertEqual(len(set(assigned)), len(manifest))


class FeatureTests(unittest.TestCase):
    def test_extract_patch_zero_pads_boundaries(self) -> None:
        panel = np.arange(16, dtype=np.float32).reshape(4, 4)
        patch = extract_patch(panel, center_trace=0, center_time=0, half_width=1, half_height=1)

        expected = np.array(
            [
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
                [0.0, 4.0, 5.0],
            ],
            dtype=np.float32,
        )
        np.testing.assert_allclose(patch, expected)


class MetricTests(unittest.TestCase):
    def test_metrics_ignore_unlabeled_traces(self) -> None:
        pred = np.array([10, 14, 20], dtype=np.int32)
        truth = np.array([12, 15, 99], dtype=np.int32)
        valid = np.array([True, True, False])

        bundle = compute_metric_bundle(pred, truth, valid, sample_ms=2.0)
        errors = valid_error_ms(pred, truth, valid, sample_ms=2.0)
        summary = summarize_error_ms(errors)

        self.assertAlmostEqual(bundle["mae_ms"], 3.0)
        self.assertAlmostEqual(bundle["rmse_ms"], float(np.sqrt((4.0**2 + 2.0**2) / 2.0)))
        self.assertEqual(summary["valid_trace_count"], 2)
        self.assertAlmostEqual(summary["acc_4ms"], 100.0)


class ModelingTests(unittest.TestCase):
    def test_model_round_trip_saves_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            train_npz = root / "train.npz"
            val_npz = root / "val.npz"
            model_pkl = root / "model.pkl"
            report_json = root / "report.json"

            rng = np.random.default_rng(42)
            x_train = rng.normal(size=(40, 9)).astype(np.float32)
            y_train = np.zeros(40, dtype=np.float32)
            x_val = rng.normal(size=(12, 9)).astype(np.float32)
            y_val = np.zeros(12, dtype=np.float32)

            train_payload = {
                "X": x_train,
                "y": y_train,
                "meta_baseline": np.zeros(len(x_train), dtype=np.int32),
                "meta_true": np.rint(y_train).astype(np.int32),
                "meta_sample_ms": np.full(len(x_train), 2.0, dtype=np.float32),
                "half_width": np.array([1], dtype=np.int32),
                "half_height": np.array([1], dtype=np.int32),
                "trace_stride": np.array([1], dtype=np.int32),
                "max_abs_correction": np.array([10], dtype=np.int32),
            }
            val_payload = {
                "X": x_val,
                "y": y_val,
                "meta_baseline": np.zeros(len(x_val), dtype=np.int32),
                "meta_true": np.rint(y_val).astype(np.int32),
                "meta_sample_ms": np.full(len(x_val), 2.0, dtype=np.float32),
                "half_width": np.array([1], dtype=np.int32),
                "half_height": np.array([1], dtype=np.int32),
                "trace_stride": np.array([1], dtype=np.int32),
                "max_abs_correction": np.array([10], dtype=np.int32),
            }

            np.savez_compressed(train_npz, **train_payload)
            np.savez_compressed(val_npz, **val_payload)

            train_model_with_validation(
                train_npz=train_npz,
                val_npz=val_npz,
                out_model=model_pkl,
                out_report=report_json,
                candidates=[
                    {
                        "learning_rate": 0.1,
                        "max_iter": 10,
                        "max_depth": 3,
                        "min_samples_leaf": 2,
                        "l2_regularization": 0.0,
                    }
                ],
            )

            artifact = load_model_artifact(model_pkl)
            pred = artifact["model"].predict(x_val)
            panel = rng.normal(size=(12, 5)).astype(np.float32)
            baseline, corrected = predict_corrected_panel(panel, artifact)

            self.assertTrue(model_pkl.exists())
            self.assertTrue(report_json.exists())
            self.assertEqual(int(artifact["feature_spec"]["half_width"]), 1)
            self.assertEqual(pred.shape[0], x_val.shape[0])
            self.assertEqual(baseline.shape, (panel.shape[1],))
            self.assertEqual(corrected.shape, (panel.shape[1],))
            self.assertTrue(np.all(corrected >= 0))
            self.assertTrue(np.all(corrected < panel.shape[0]))


if __name__ == "__main__":
    unittest.main()
