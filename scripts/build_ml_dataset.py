import argparse
from pathlib import Path

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from seismic_first_break_picker.correction import build_dataset_from_split

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments_dir", type=str, required=True, help="Directory containing exported .npz segment files")
    parser.add_argument("--split_json", type=str, required=True, help="JSON file listing segment filenames to use")
    parser.add_argument("--out_npz", type=str, required=True, help="Output .npz dataset path")
    parser.add_argument("--trace_stride", type=int, default=3, help="Use every Nth valid trace")
    parser.add_argument("--half_width", type=int, default=2, help="Neighbor trace radius")
    parser.add_argument("--half_height", type=int, default=40, help="Time radius around baseline pick")
    parser.add_argument("--max_abs_correction", type=int, default=60, help="Skip examples with larger absolute correction")
    args = parser.parse_args()

    build_dataset_from_split(
        segments_dir=Path(args.segments_dir),
        split_json=Path(args.split_json),
        out_npz=Path(args.out_npz),
        trace_stride=args.trace_stride,
        half_width=args.half_width,
        half_height=args.half_height,
        max_abs_correction=args.max_abs_correction,
    )


if __name__ == "__main__":
    main()
