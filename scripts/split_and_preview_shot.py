from pathlib import Path
import argparse

import h5py
import numpy as np

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from seismic_first_break_picker.data import (
    compute_visual_order,
    robust_normalize,
    scale_with_segy_rule,
    split_by_large_jumps,
    to_1d,
)
from seismic_first_break_picker.visualization import save_panel_preview


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, required=True, help="Path to HDF5 file")
    parser.add_argument("--shot_id", type=int, required=True, help="Shot ID to inspect")
    parser.add_argument("--out_dir", type=str, required=True, help="Directory for output previews")
    parser.add_argument("--jump_factor", type=float, default=8.0, help="Gap multiplier for splitting")
    parser.add_argument("--min_traces", type=int, default=80, help="Ignore tiny segments")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with h5py.File(args.path, "r") as handle:
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

        idx = np.flatnonzero(shot == args.shot_id)
        if idx.size == 0:
            raise ValueError(f"Shot {args.shot_id} was not found.")

        idx_visual = idx[compute_visual_order(rec_peg[idx], rec_x[idx])]
        ordered_rec_peg = rec_peg[idx_visual]
        ordered_rec_x = rec_x[idx_visual]

        if np.unique(ordered_rec_peg).size > 1:
            ordered_values = ordered_rec_peg
            split_basis = "REC_PEG"
        else:
            ordered_values = ordered_rec_x
            split_basis = "REC_X"

        groups = split_by_large_jumps(ordered_values, jump_factor=args.jump_factor)

        print(f"Shot key        : {shot_key}")
        print(f"Shot ID         : {args.shot_id}")
        print(f"Trace count     : {len(idx_visual)}")
        print(f"Split basis     : {split_basis}")
        print(f"Segment count   : {len(groups)}")
        print("")

        for seg_num, local_group in enumerate(groups):
            if len(local_group) < args.min_traces:
                continue

            seg_idx_visual = idx_visual[local_group]
            seg_idx_sorted = np.sort(seg_idx_visual)
            panel_sorted = np.asarray(data[seg_idx_sorted, :], dtype=np.float32)
            read_pos = {original_idx: pos for pos, original_idx in enumerate(seg_idx_sorted)}
            reorder = np.array([read_pos[original_idx] for original_idx in seg_idx_visual], dtype=np.int64)

            panel = robust_normalize(panel_sorted[reorder].T)
            fb_ms = labels_ms[seg_idx_visual]
            valid = fb_ms > 0
            fb_idx = np.rint(fb_ms / sample_ms).astype(np.int32)

            out_path = out_dir / f"shot_{args.shot_id}_segment_{seg_num:02d}.png"
            save_panel_preview(panel, fb_idx, valid, f"SHOTID {args.shot_id} - segment {seg_num}", out_path)

            print(
                f"segment {seg_num:02d}: "
                f"trace_count={len(seg_idx_visual)}, "
                f"valid_labels={int(valid.sum())}, "
                f"file={out_path.name}"
            )


if __name__ == "__main__":
    main()
