import argparse
from pathlib import Path

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from seismic_first_break_picker.splits import create_shot_disjoint_splits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments_dir", type=str, required=True, help="Directory containing exported .npz segment files")
    parser.add_argument("--manifest_path", type=str, default=None, help="Optional manifest JSON path")
    parser.add_argument("--train_ratio", type=float, default=0.7, help="Shot-level train ratio")
    parser.add_argument("--val_ratio", type=float, default=0.1, help="Shot-level validation ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--out_dir", type=str, required=True, help="Directory to save split json files")
    args = parser.parse_args()

    create_shot_disjoint_splits(
        segments_dir=Path(args.segments_dir),
        out_dir=Path(args.out_dir),
        manifest_path=Path(args.manifest_path) if args.manifest_path else None,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
