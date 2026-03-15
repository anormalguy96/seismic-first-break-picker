import argparse
from pathlib import Path

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from seismic_first_break_picker.evaluation import evaluate_split
from seismic_first_break_picker.modeling import load_model_artifact


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments_dir", type=str, required=True, help="Directory with exported segments")
    parser.add_argument("--test_split_json", type=str, required=True, help="JSON list of held-out segment files")
    parser.add_argument("--model_pkl", type=str, required=True, help="Saved model pickle")
    parser.add_argument("--out_dir", type=str, required=True, help="Directory for evaluation outputs")
    args = parser.parse_args()

    artifact = load_model_artifact(Path(args.model_pkl))
    evaluate_split(
        segments_dir=Path(args.segments_dir),
        split_json=Path(args.test_split_json),
        artifact=artifact,
        out_dir=Path(args.out_dir),
    )


if __name__ == "__main__":
    main()
