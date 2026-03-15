from __future__ import annotations

from pathlib import Path
import argparse

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from seismic_first_break_picker.correction import build_dataset_from_split
from seismic_first_break_picker.data import export_segments
from seismic_first_break_picker.evaluation import evaluate_split
from seismic_first_break_picker.modeling import load_model_artifact, train_model_with_validation
from seismic_first_break_picker.splits import create_shot_disjoint_splits


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw_path", type=str, required=True, help="Path to the Halfmile raw HDF5 file")
    parser.add_argument("--asset_name", type=str, default="Halfmile", help="Asset label to store in outputs")
    parser.add_argument("--segments_dir", type=str, default="data/interim/Halfmile_segments", help="Exported segment directory")
    parser.add_argument("--splits_dir", type=str, default="data/processed/splits", help="Directory for train/val/test split files")
    parser.add_argument("--processed_dir", type=str, default="data/processed", help="Directory for dataset and model artifacts")
    parser.add_argument("--reports_dir", type=str, default="reports/evaluation", help="Directory for evaluation outputs")
    parser.add_argument("--skip_export", action="store_true", help="Skip segment export and reuse existing exported segments")
    args = parser.parse_args()

    raw_path = Path(args.raw_path)
    segments_dir = Path(args.segments_dir)
    splits_dir = Path(args.splits_dir)
    processed_dir = Path(args.processed_dir)
    reports_dir = Path(args.reports_dir)

    if not args.skip_export:
        export_segments(raw_path, segments_dir, asset_name=args.asset_name)

    create_shot_disjoint_splits(segments_dir=segments_dir, out_dir=splits_dir)

    train_npz = processed_dir / "ml_train_dataset.npz"
    val_npz = processed_dir / "ml_val_dataset.npz"
    test_npz = processed_dir / "ml_test_dataset.npz"
    train_json = splits_dir / "train_segments.json"
    val_json = splits_dir / "val_segments.json"
    test_json = splits_dir / "test_segments.json"

    build_dataset_from_split(segments_dir, train_json, train_npz)
    build_dataset_from_split(segments_dir, val_json, val_npz)
    build_dataset_from_split(segments_dir, test_json, test_npz)

    model_pkl = processed_dir / "ml_correction_model.pkl"
    train_report = processed_dir / "ml_correction_training_report.json"
    train_model_with_validation(train_npz, val_npz, model_pkl, train_report)

    artifact = load_model_artifact(model_pkl)
    evaluate_split(segments_dir=segments_dir, split_json=test_json, artifact=artifact, out_dir=reports_dir)


if __name__ == "__main__":
    main()
