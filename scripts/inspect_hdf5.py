from pathlib import Path
import argparse

import h5py
import numpy as np

from _bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from seismic_first_break_picker.data import to_1d


def shape_of(dataset) -> tuple[int, ...] | str:
    try:
        return tuple(dataset.shape)
    except Exception:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, required=True, help="Path to .hdf5 file")
    args = parser.parse_args()

    path = Path(args.path)
    with h5py.File(path, "r") as handle:
        group = handle["TRACE_DATA/DEFAULT"]

        print("\n=== Keys in TRACE_DATA/DEFAULT ===")
        for key in group.keys():
            print(f"{key:20s} shape={shape_of(group[key])}")

        print("\n=== Quick stats ===")
        print("data_array shape:", group["data_array"].shape)

        sample_rate_us = to_1d(group["SAMP_RATE"][:])
        sample_num = to_1d(group["SAMP_NUM"][:])
        fb = to_1d(group["SPARE1"][:])
        valid_fb = fb[fb > 0]

        print("sample rate unique:", np.unique(sample_rate_us)[:10])
        print("sample num unique :", np.unique(sample_num)[:10])
        print("valid labels      :", valid_fb.size)
        print("total traces      :", fb.size)
        print("label coverage    :", round(valid_fb.size / fb.size * 100, 2), "%")

        shot_key = "SHOTID" if "SHOTID" in group else "SHOT_PEG"
        shot = to_1d(group[shot_key][:])
        uniq_shots, counts = np.unique(shot, return_counts=True)
        print("shot key          :", shot_key)
        print("unique shots      :", uniq_shots.size)
        print("traces/shot min   :", counts.min())
        print("traces/shot median:", int(np.median(counts)))
        print("traces/shot max   :", counts.max())


if __name__ == "__main__":
    main()
