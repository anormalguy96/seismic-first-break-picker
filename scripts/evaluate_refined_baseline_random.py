from pathlib import Path
import argparse
import random
import csv

import numpy as np

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from seismic_first_break_picker.baseline import pick_first_break_panel_refined
from seismic_first_break_picker.metrics import compute_metric_bundle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments_dir", type=str, required=True, help="Directory with exported .npz files")
    parser.add_argument("--sample_count", type=int, default=100, help="How many random segments to evaluate")
    parser.add_argument("--out_csv", type=str, required=True, help="CSV file to save per-segment metrics")
    args = parser.parse_args()

    segments_dir = Path(args.segments_dir)
    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    npz_files = sorted(segments_dir.glob("*.npz"))
    if not npz_files:
        raise ValueError(f"No .npz files found in {segments_dir}")

    chosen = random.sample(npz_files, k=min(args.sample_count, len(npz_files)))

    rows = []

    for npz_path in chosen:
        data = np.load(npz_path)
        panel = data["panel"]
        fb_idx = data["fb_idx"].astype(np.int32)
        valid = data["valid"].astype(bool)
        sample_ms = float(data["sample_ms"][0])
        shot_id = int(data["shot_id"][0])
        segment_num = int(data["segment_num"][0])

        pred_idx = pick_first_break_panel_refined(panel)

        metrics = compute_metric_bundle(pred_idx, fb_idx, valid, sample_ms)
        row = {
            "file": npz_path.name,
            "shot_id": shot_id,
            "segment_num": segment_num,
            "trace_count": int(panel.shape[1]),
            "valid_count": int(valid.sum()),
            "mae_ms": metrics["mae_ms"],
            "rmse_ms": metrics["rmse_ms"],
            "acc_4ms": metrics["acc_4ms"],
            "acc_8ms": metrics["acc_8ms"],
        }
        rows.append(row)

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "shot_id",
                "segment_num",
                "trace_count",
                "valid_count",
                "mae_ms",
                "rmse_ms",
                "acc_4ms",
                "acc_8ms",
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    mae_values = np.array([r["mae_ms"] for r in rows], dtype=np.float64)
    rmse_values = np.array([r["rmse_ms"] for r in rows], dtype=np.float64)
    acc4_values = np.array([r["acc_4ms"] for r in rows], dtype=np.float64)
    acc8_values = np.array([r["acc_8ms"] for r in rows], dtype=np.float64)

    print(f"Evaluated segments : {len(rows)}")
    print(f"Average MAE (ms)   : {mae_values.mean():.3f}")
    print(f"Average RMSE (ms)  : {rmse_values.mean():.3f}")
    print(f"Average <= 4 ms    : {acc4_values.mean():.2f}%")
    print(f"Average <= 8 ms    : {acc8_values.mean():.2f}%")
    print(f"Saved CSV          : {out_csv}")


if __name__ == "__main__":
    main()
