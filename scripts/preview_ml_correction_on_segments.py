from pathlib import Path
import argparse
import json
import random

import numpy as np

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from seismic_first_break_picker.correction import predict_corrected_panel
from seismic_first_break_picker.modeling import load_model_artifact
from seismic_first_break_picker.visualization import save_comparison_preview


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments_dir", type=str, required=True)
    parser.add_argument("--test_split_json", type=str, required=True)
    parser.add_argument("--model_pkl", type=str, required=True)
    parser.add_argument("--out_dir", type=str, required=True)
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()

    segments_dir = Path(args.segments_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(args.test_split_json, "r", encoding="utf-8") as f:
        test_files = json.load(f)

    chosen = random.sample(test_files, k=min(args.count, len(test_files)))

    artifact = load_model_artifact(args.model_pkl)

    for fname in chosen:
        npz_path = segments_dir / fname
        data = np.load(npz_path)

        panel = data["panel"]
        fb_idx = data["fb_idx"].astype(np.int32)
        valid = data["valid"].astype(bool)
        shot_id = int(data["shot_id"][0])
        seg_num = int(data["segment_num"][0])

        baseline, corrected = predict_corrected_panel(panel, artifact)
        out_path = out_dir / f"{npz_path.stem}_comparison.png"
        save_comparison_preview(
            panel=panel,
            manual_idx=fb_idx,
            valid=valid,
            baseline_idx=baseline,
            corrected_idx=corrected,
            title=f"shot {shot_id} | seg {seg_num}",
            out_path=out_path,
        )

        print(f"saved: {out_path}")


if __name__ == "__main__":
    main()
