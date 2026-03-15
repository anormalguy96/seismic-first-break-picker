from pathlib import Path
import argparse

import h5py
import numpy as np

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from seismic_first_break_picker.data import compute_visual_order, robust_normalize, scale_with_segy_rule, to_1d
from seismic_first_break_picker.visualization import save_panel_preview


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, required=True, help="Path to HDF5 file")
    parser.add_argument("--shot_id", type=int, default=None, help="Optional shot id")
    parser.add_argument("--out", type=str, required=True, help="Output PNG path")
    args = parser.parse_args()

    path = Path(args.path)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with h5py.File(path, "r") as handle:
        group = handle["TRACE_DATA/DEFAULT"]
        data = group["data_array"]
        shot_key = "SHOTID" if "SHOTID" in group else "SHOT_PEG"
        shot = to_1d(group[shot_key][:])
        rec_peg = to_1d(group["REC_PEG"][:]).astype(np.float64)
        coord_scale = to_1d(group["COORD_SCALE"][:]) if "COORD_SCALE" in group else None
        rec_x = scale_with_segy_rule(to_1d(group["REC_X"][:]), coord_scale)
        labels_ms = to_1d(group["SPARE1"][:]).astype(np.float64)

        sample_rate_us = float(to_1d(group["SAMP_RATE"][:])[0])
        sample_ms = sample_rate_us / 1000.0

        unique_shots = np.unique(shot)
        chosen_shot = int(unique_shots[0]) if args.shot_id is None else int(args.shot_id)

        idx = np.flatnonzero(shot == chosen_shot)
        if idx.size == 0:
            raise ValueError(f"Shot {chosen_shot} was not found.")

        idx_visual = idx[compute_visual_order(rec_peg[idx], rec_x[idx])]
        idx_sorted = np.sort(idx_visual)
        panel_sorted = np.asarray(data[idx_sorted, :], dtype=np.float32)
        read_pos = {original_idx: pos for pos, original_idx in enumerate(idx_sorted)}
        reorder = np.array([read_pos[original_idx] for original_idx in idx_visual], dtype=np.int64)

        panel = robust_normalize(panel_sorted[reorder].T)
        fb_ms = labels_ms[idx_visual]
        valid = fb_ms > 0
        fb_idx = np.rint(fb_ms / sample_ms).astype(np.int32)

        save_panel_preview(panel, fb_idx, valid, f"Halfmile preview - SHOTID {chosen_shot}", out_path)

        print(f"Shot key         : {shot_key}")
        print(f"Chosen shot id   : {chosen_shot}")
        print(f"Trace count      : {idx_visual.size}")
        print(f"Valid labels     : {int(valid.sum())}")
        print(f"Sample interval  : {sample_ms:.3f} ms")
        print(f"Saved preview to : {out_path}")


if __name__ == "__main__":
    main()
