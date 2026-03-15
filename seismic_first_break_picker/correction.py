from __future__ import annotations

from pathlib import Path

import numpy as np
from tqdm import tqdm

from .baseline import pick_first_break_panel_refined, robust_smooth_line
from .data import load_segment, load_split_file


def extract_patch(
    panel: np.ndarray,
    center_trace: int,
    center_time: int,
    half_width: int,
    half_height: int,
) -> np.ndarray:
    time_len, trace_len = panel.shape
    t0 = center_time - half_height
    t1 = center_time + half_height + 1
    x0 = center_trace - half_width
    x1 = center_trace + half_width + 1

    patch = np.zeros((2 * half_height + 1, 2 * half_width + 1), dtype=np.float32)

    src_t0 = max(0, t0)
    src_t1 = min(time_len, t1)
    src_x0 = max(0, x0)
    src_x1 = min(trace_len, x1)

    dst_t0 = src_t0 - t0
    dst_t1 = dst_t0 + (src_t1 - src_t0)
    dst_x0 = src_x0 - x0
    dst_x1 = dst_x0 + (src_x1 - src_x0)

    patch[dst_t0:dst_t1, dst_x0:dst_x1] = panel[src_t0:src_t1, src_x0:src_x1]
    return patch


def _feature_spec_from_artifact(
    artifact: object,
    half_width: int | None = None,
    half_height: int | None = None,
) -> tuple[object, int, int]:
    if isinstance(artifact, dict) and "model" in artifact:
        feature_spec = artifact.get("feature_spec", {})
        return (
            artifact["model"],
            int(feature_spec.get("half_width", half_width if half_width is not None else 2)),
            int(feature_spec.get("half_height", half_height if half_height is not None else 40)),
        )
    if half_width is None or half_height is None:
        return artifact, 2, 40
    return artifact, half_width, half_height


def build_dataset_from_split(
    segments_dir: Path | str,
    split_json: Path | str,
    out_npz: Path | str,
    trace_stride: int = 3,
    half_width: int = 2,
    half_height: int = 40,
    max_abs_correction: int = 60,
) -> Path:
    source_dir = Path(segments_dir)
    target_npz = Path(out_npz)
    target_npz.parent.mkdir(parents=True, exist_ok=True)

    chosen_files = load_split_file(split_json)
    x_rows: list[np.ndarray] = []
    y_rows: list[float] = []

    meta_asset = []
    meta_file = []
    meta_segment_id = []
    meta_shot = []
    meta_segment_num = []
    meta_trace = []
    meta_baseline = []
    meta_true = []
    meta_sample_ms = []

    for filename in tqdm(chosen_files, desc=f"Building {target_npz.stem}"):
        segment = load_segment(source_dir / filename)
        panel = segment["panel"]
        fb_idx = segment["fb_idx"]
        valid = segment["valid"]

        baseline_idx = pick_first_break_panel_refined(panel)
        valid_trace_ids = np.flatnonzero(valid)[::trace_stride]

        for trace_idx in valid_trace_ids:
            true_pick = int(fb_idx[trace_idx])
            base_pick = int(baseline_idx[trace_idx])
            correction = true_pick - base_pick

            if abs(correction) > max_abs_correction:
                continue

            patch = extract_patch(
                panel=panel,
                center_trace=int(trace_idx),
                center_time=base_pick,
                half_width=half_width,
                half_height=half_height,
            )

            x_rows.append(patch.reshape(-1))
            y_rows.append(float(correction))
            meta_asset.append(segment["asset_name"])
            meta_file.append(filename)
            meta_segment_id.append(segment["segment_id"])
            meta_shot.append(segment["shot_id"])
            meta_segment_num.append(segment["segment_num"])
            meta_trace.append(int(trace_idx))
            meta_baseline.append(base_pick)
            meta_true.append(true_pick)
            meta_sample_ms.append(segment["sample_ms"])

    if not x_rows:
        raise ValueError("No training examples were created.")

    payload = {
        "X": np.asarray(x_rows, dtype=np.float32),
        "y": np.asarray(y_rows, dtype=np.float32),
        "meta_asset_name": np.asarray(meta_asset),
        "meta_file": np.asarray(meta_file),
        "meta_segment_id": np.asarray(meta_segment_id),
        "meta_shot_id": np.asarray(meta_shot, dtype=np.int64),
        "meta_segment_num": np.asarray(meta_segment_num, dtype=np.int32),
        "meta_trace_idx": np.asarray(meta_trace, dtype=np.int32),
        "meta_baseline": np.asarray(meta_baseline, dtype=np.int32),
        "meta_true": np.asarray(meta_true, dtype=np.int32),
        "meta_sample_ms": np.asarray(meta_sample_ms, dtype=np.float32),
        "half_width": np.asarray([half_width], dtype=np.int32),
        "half_height": np.asarray([half_height], dtype=np.int32),
        "trace_stride": np.asarray([trace_stride], dtype=np.int32),
        "max_abs_correction": np.asarray([max_abs_correction], dtype=np.int32),
    }

    np.savez_compressed(target_npz, **payload)

    print(f"Saved dataset : {target_npz}")
    print(f"Example count : {len(payload['X'])}")
    print(f"Feature shape : {payload['X'].shape}")
    print(f"Target mean   : {payload['y'].mean():.3f}")
    print(f"Target std    : {payload['y'].std():.3f}")
    return target_npz


def load_dataset(npz_path: Path | str) -> dict[str, np.ndarray]:
    payload = np.load(npz_path, allow_pickle=True)
    return {key: payload[key] for key in payload.files}


def predict_corrected_panel(
    panel: np.ndarray,
    artifact: object,
    half_width: int | None = None,
    half_height: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    model, patch_half_width, patch_half_height = _feature_spec_from_artifact(
        artifact,
        half_width=half_width,
        half_height=half_height,
    )

    baseline = pick_first_break_panel_refined(panel)
    n_traces = panel.shape[1]
    feature_rows = np.empty(
        (n_traces, (2 * patch_half_height + 1) * (2 * patch_half_width + 1)),
        dtype=np.float32,
    )

    for trace_idx in range(n_traces):
        feature_rows[trace_idx] = extract_patch(
            panel=panel,
            center_trace=trace_idx,
            center_time=int(baseline[trace_idx]),
            half_width=patch_half_width,
            half_height=patch_half_height,
        ).reshape(-1)

    correction = np.rint(model.predict(feature_rows)).astype(np.int32)
    corrected = baseline + correction
    corrected = np.clip(corrected, 0, panel.shape[0] - 1)
    corrected = robust_smooth_line(corrected, median_window=7, mean_window=11)
    corrected = np.rint(corrected).astype(np.int32)
    return baseline, corrected
