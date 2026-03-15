from pathlib import Path
import argparse
import random

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from seismic_first_break_picker.data import load_segment
from seismic_first_break_picker.visualization import save_panel_preview


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments_dir", type=str, required=True, help="Directory with exported .npz files")
    parser.add_argument("--out_dir", type=str, required=True, help="Directory to save preview images")
    parser.add_argument("--count", type=int, default=5, help="How many random segments to preview")
    args = parser.parse_args()

    segments_dir = Path(args.segments_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    npz_files = sorted(segments_dir.glob("*.npz"))
    if not npz_files:
        raise ValueError(f"No .npz files found in {segments_dir}")

    chosen = random.sample(npz_files, k=min(args.count, len(npz_files)))

    print(f"Found {len(npz_files)} exported segments")
    print(f"Previewing {len(chosen)} random segments")
    print("")

    for npz_path in chosen:
        item = load_segment(npz_path)
        panel = item["panel"]
        fb_idx = item["fb_idx"]
        valid = item["valid"]

        title = f"shot {item['shot_id']} | seg {item['segment_num']}"
        out_path = out_dir / f"{npz_path.stem}.png"

        save_panel_preview(panel, fb_idx, valid, title, out_path)

        print(f"file           : {npz_path.name}")
        print(f"panel shape    : {panel.shape}")
        print(f"valid labels   : {int(valid.sum())}")
        print(f"sample_ms      : {item['sample_ms']}")
        print(f"preview        : {out_path.name}")
        print("")


if __name__ == "__main__":
    main()
