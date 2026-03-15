from pathlib import Path
import argparse

import numpy as np

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from seismic_first_break_picker.baseline import pick_first_break_panel_refined
from seismic_first_break_picker.metrics import compute_metric_bundle
from seismic_first_break_picker.visualization import save_comparison_preview


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--npz", type=str, required=True, help="Path to one exported .npz segment")
    parser.add_argument("--out", type=str, required=True, help="Output PNG path")
    args = parser.parse_args()

    npz_path = Path(args.npz)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    data = np.load(npz_path)
    panel = data["panel"]
    fb_idx = data["fb_idx"].astype(np.int32)
    valid = data["valid"].astype(bool)
    sample_ms = float(data["sample_ms"][0])
    shot_id = int(data["shot_id"][0])
    segment_num = int(data["segment_num"][0])

    pred_idx = pick_first_break_panel_refined(panel)

    metrics = compute_metric_bundle(pred_idx, fb_idx, valid, sample_ms)
    save_comparison_preview(
        panel=panel,
        manual_idx=fb_idx,
        valid=valid,
        baseline_idx=pred_idx,
        corrected_idx=pred_idx,
        title=f"Refined baseline | shot {shot_id} | seg {segment_num}",
        out_path=out_path,
    )

    print(f"file        : {npz_path.name}")
    print(f"panel shape : {panel.shape}")
    print(f"sample_ms   : {sample_ms}")
    print(f"valid count : {int(valid.sum())}")
    print(f"MAE (ms)    : {metrics['mae_ms']:.3f}")
    print(f"RMSE (ms)   : {metrics['rmse_ms']:.3f}")
    print(f"<= 4 ms     : {metrics['acc_4ms']:.2f}%")
    print(f"<= 8 ms     : {metrics['acc_8ms']:.2f}%")
    print(f"saved plot  : {out_path}")


if __name__ == "__main__":
    main()
