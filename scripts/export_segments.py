from pathlib import Path
import argparse

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from seismic_first_break_picker.data import export_segments


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, required=True, help="Path to HDF5 file")
    parser.add_argument("--out_dir", type=str, required=True, help="Output directory for .npz files")
    parser.add_argument("--asset_name", type=str, default="Halfmile", help="Asset name")
    parser.add_argument("--jump_factor", type=float, default=8.0, help="Gap multiplier for splitting")
    parser.add_argument("--min_traces", type=int, default=80, help="Minimum traces per segment")
    parser.add_argument("--min_valid_labels", type=int, default=70, help="Minimum valid labels per segment")
    args = parser.parse_args()

    export_segments(
        path=Path(args.path),
        out_dir=Path(args.out_dir),
        asset_name=args.asset_name,
        jump_factor=args.jump_factor,
        min_traces=args.min_traces,
        min_valid_labels=args.min_valid_labels,
    )


if __name__ == "__main__":
    main()
