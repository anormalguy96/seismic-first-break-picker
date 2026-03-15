import argparse
from pathlib import Path

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from seismic_first_break_picker.modeling import train_model_with_validation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_npz", type=str, required=True, help="Training dataset .npz")
    parser.add_argument("--val_npz", type=str, required=True, help="Validation dataset .npz")
    parser.add_argument("--out_model", type=str, required=True, help="Output pickle model path")
    parser.add_argument("--out_report", type=str, required=True, help="Output JSON training report path")
    args = parser.parse_args()

    train_model_with_validation(
        train_npz=Path(args.train_npz),
        val_npz=Path(args.val_npz),
        out_model=Path(args.out_model),
        out_report=Path(args.out_report),
    )


if __name__ == "__main__":
    main()
