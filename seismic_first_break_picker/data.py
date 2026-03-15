from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import re

import h5py
import numpy as np
from tqdm import tqdm


@dataclass(frozen=True)
class SegmentRecord:
    segment_id: str
    file: str
    asset_name: str
    shot_id: int
    segment_num: int
    trace_count: int
    sample_count: int
    valid_label_count: int
    split_basis: str


def to_1d(values: np.ndarray) -> np.ndarray:
    return np.asarray(values).reshape(-1)


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def load_json(path: Path) -> object:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_split_file(path: Path | str) -> list[str]:
    return list(load_json(Path(path)))


def scale_with_segy_rule(values: np.ndarray, scale_values: np.ndarray | None) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64)
    if scale_values is None:
        return x

    scale = np.asarray(scale_values, dtype=np.float64).reshape(-1)
    if scale.size == 0:
        return x

    scaled = x.copy()
    for raw_scale in np.unique(scale):
        mask = scale == raw_scale
        if raw_scale == 0:
            factor = 1.0
        elif raw_scale > 0:
            factor = raw_scale
        else:
            factor = 1.0 / abs(raw_scale)
        scaled[mask] = scaled[mask] * factor
    return scaled


def robust_normalize(panel: np.ndarray) -> np.ndarray:
    scale = np.percentile(np.abs(panel), 99)
    if scale <= 1e-8:
        return panel.astype(np.float32)
    normalized = panel / scale
    normalized = np.clip(normalized, -1.0, 1.0)
    return normalized.astype(np.float32)


def compute_visual_order(rec_peg: np.ndarray, rec_x: np.ndarray) -> np.ndarray:
    if np.unique(rec_peg).size > 1:
        return np.argsort(rec_peg, kind="stable")
    return np.argsort(rec_x, kind="stable")


def split_by_large_jumps(values: np.ndarray, jump_factor: float = 8.0) -> list[np.ndarray]:
    if len(values) < 2:
        return [np.arange(len(values))]

    diffs = np.diff(values)
    positive_diffs = diffs[diffs > 0]
    if positive_diffs.size == 0:
        return [np.arange(len(values))]

    typical_gap = np.median(positive_diffs)
    threshold = typical_gap * jump_factor
    split_points = np.where(diffs > threshold)[0] + 1
    return list(np.split(np.arange(len(values)), split_points))


def _first_available_key(group: h5py.Group, *candidates: str) -> str:
    for key in candidates:
        if key in group:
            return key
    raise KeyError(f"None of the keys were found: {candidates}")


def _read_vector(group: h5py.Group, key: str) -> np.ndarray:
    return to_1d(group[key][:])


def _read_scaled_vector(
    group: h5py.Group,
    key: str,
    scale_key: str | None = None,
) -> np.ndarray:
    values = _read_vector(group, key)
    if scale_key is None or scale_key not in group:
        return values.astype(np.float64)
    return scale_with_segy_rule(values, _read_vector(group, scale_key))


def parse_asset_name_from_filename(filename: str) -> str:
    match = re.match(r"(?P<asset>.+)_shot\d+_seg\d+", Path(filename).stem)
    if not match:
        raise ValueError(f"Could not parse asset name from filename: {filename}")
    return match.group("asset")


def parse_shot_id_from_filename(filename: str) -> int:
    match = re.search(r"_shot(?P<shot>\d+)_seg", Path(filename).stem)
    if not match:
        raise ValueError(f"Could not parse shot id from filename: {filename}")
    return int(match.group("shot"))


def discover_segment_records(
    segments_dir: Path,
    manifest_path: Path | None = None,
) -> list[dict[str, object]]:
    if manifest_path is None:
        json_files = sorted(segments_dir.glob("*_segments_manifest.json"))
        manifest_path = json_files[0] if json_files else None

    if manifest_path and manifest_path.exists():
        return list(load_json(manifest_path))

    records = []
    for npz_path in sorted(segments_dir.glob("*.npz")):
        segment = load_segment(npz_path)
        records.append(
            {
                "segment_id": segment["segment_id"],
                "file": str(npz_path),
                "asset_name": segment["asset_name"],
                "shot_id": segment["shot_id"],
                "segment_num": segment["segment_num"],
                "trace_count": int(segment["panel"].shape[1]),
                "sample_count": int(segment["panel"].shape[0]),
                "valid_label_count": int(np.sum(segment["valid"])),
                "split_basis": segment["split_basis"],
            }
        )
    return records


def export_segments(
    path: Path | str,
    out_dir: Path | str,
    asset_name: str = "Halfmile",
    jump_factor: float = 8.0,
    min_traces: int = 80,
    min_valid_labels: int = 70,
) -> Path:
    source_path = Path(path)
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, object]] = []

    with h5py.File(source_path, "r") as handle:
        group = handle["TRACE_DATA/DEFAULT"]
        data_array = group["data_array"]

        shot_key = _first_available_key(group, "SHOTID", "SHOT_PEG")
        shot = _read_vector(group, shot_key).astype(np.int64)
        shot_peg = _read_vector(group, "SHOT_PEG").astype(np.int64) if "SHOT_PEG" in group else shot.copy()
        rec_peg = _read_vector(group, "REC_PEG").astype(np.float64) if "REC_PEG" in group else np.arange(len(shot), dtype=np.float64)
        rec_x = _read_scaled_vector(group, "REC_X", "COORD_SCALE") if "REC_X" in group else np.arange(len(shot), dtype=np.float64)
        rec_y = _read_scaled_vector(group, "REC_Y", "COORD_SCALE") if "REC_Y" in group else np.zeros(len(shot), dtype=np.float64)
        rec_ht = _read_scaled_vector(group, "REC_HT", "HT_SCALE") if "REC_HT" in group else np.zeros(len(shot), dtype=np.float64)
        source_x = _read_scaled_vector(group, "SOURCE_X", "COORD_SCALE") if "SOURCE_X" in group else np.zeros(len(shot), dtype=np.float64)
        source_y = _read_scaled_vector(group, "SOURCE_Y", "COORD_SCALE") if "SOURCE_Y" in group else np.zeros(len(shot), dtype=np.float64)
        source_ht = _read_scaled_vector(group, "SOURCE_HT", "HT_SCALE") if "SOURCE_HT" in group else np.zeros(len(shot), dtype=np.float64)
        labels_ms = _read_vector(group, "SPARE1").astype(np.float64)
        sample_rate_us = float(_read_vector(group, "SAMP_RATE")[0])
        sample_ms = sample_rate_us / 1000.0

        unique_shots = np.unique(shot)
        saved_count = 0

        for shot_id in tqdm(unique_shots, desc="Exporting segments"):
            shot_idx = np.flatnonzero(shot == shot_id)
            if shot_idx.size == 0:
                continue

            order = compute_visual_order(rec_peg[shot_idx], rec_x[shot_idx])
            idx_visual = shot_idx[order]

            ordered_rec_peg = rec_peg[idx_visual]
            ordered_rec_x = rec_x[idx_visual]
            if np.unique(ordered_rec_peg).size > 1:
                ordered_values = ordered_rec_peg
                split_basis = "REC_PEG"
            else:
                ordered_values = ordered_rec_x
                split_basis = "REC_X"

            groups = split_by_large_jumps(ordered_values, jump_factor=jump_factor)

            for segment_num, local_group in enumerate(groups):
                if len(local_group) < min_traces:
                    continue

                seg_idx_visual = idx_visual[local_group]
                seg_idx_sorted = np.sort(seg_idx_visual)
                panel_sorted = np.asarray(data_array[seg_idx_sorted, :], dtype=np.float32)

                read_pos = {original_idx: pos for pos, original_idx in enumerate(seg_idx_sorted)}
                reorder = np.array([read_pos[idx] for idx in seg_idx_visual], dtype=np.int64)
                panel = robust_normalize(panel_sorted[reorder].T)

                fb_ms = labels_ms[seg_idx_visual]
                valid = fb_ms > 0
                valid_count = int(np.sum(valid))
                if valid_count < min_valid_labels:
                    continue

                fb_idx = np.full(len(seg_idx_visual), -1, dtype=np.int32)
                fb_idx[valid] = np.rint(fb_ms[valid] / sample_ms).astype(np.int32)

                segment_id = f"{asset_name}_shot{int(shot_id)}_seg{segment_num:03d}"
                out_file = target_dir / f"{segment_id}.npz"

                np.savez_compressed(
                    out_file,
                    panel=panel,
                    fb_ms=fb_ms.astype(np.float32),
                    fb_idx=fb_idx,
                    valid=valid.astype(bool),
                    asset_name=np.array([asset_name]),
                    segment_id=np.array([segment_id]),
                    shot_id=np.array([int(shot_id)], dtype=np.int64),
                    shot_peg=np.array([int(shot_peg[seg_idx_visual[0]])], dtype=np.int64),
                    segment_num=np.array([segment_num], dtype=np.int64),
                    sample_ms=np.array([sample_ms], dtype=np.float32),
                    split_basis=np.array([split_basis]),
                    rec_peg=rec_peg[seg_idx_visual].astype(np.float32),
                    rec_x=rec_x[seg_idx_visual].astype(np.float32),
                    rec_y=rec_y[seg_idx_visual].astype(np.float32),
                    rec_ht=rec_ht[seg_idx_visual].astype(np.float32),
                    source_x=np.array([source_x[seg_idx_visual[0]]], dtype=np.float32),
                    source_y=np.array([source_y[seg_idx_visual[0]]], dtype=np.float32),
                    source_ht=np.array([source_ht[seg_idx_visual[0]]], dtype=np.float32),
                )

                record = SegmentRecord(
                    segment_id=segment_id,
                    file=str(out_file),
                    asset_name=asset_name,
                    shot_id=int(shot_id),
                    segment_num=segment_num,
                    trace_count=int(panel.shape[1]),
                    sample_count=int(panel.shape[0]),
                    valid_label_count=valid_count,
                    split_basis=split_basis,
                )
                manifest.append(asdict(record))
                saved_count += 1

    manifest_path = target_dir / f"{asset_name}_segments_manifest.json"
    save_json(manifest_path, manifest)

    print("")
    print(f"Saved segments : {saved_count}")
    print(f"Manifest file  : {manifest_path}")
    return manifest_path


def load_segment(npz_path: Path | str) -> dict[str, object]:
    path = Path(npz_path)
    payload = np.load(path, allow_pickle=True)

    asset_name = str(payload["asset_name"][0]) if "asset_name" in payload else parse_asset_name_from_filename(path.name)
    segment_id = str(payload["segment_id"][0]) if "segment_id" in payload else path.stem
    split_basis = str(payload["split_basis"][0]) if "split_basis" in payload else "unknown"

    return {
        "panel": payload["panel"].astype(np.float32),
        "fb_ms": payload["fb_ms"].astype(np.float32),
        "fb_idx": payload["fb_idx"].astype(np.int32),
        "valid": payload["valid"].astype(bool),
        "asset_name": asset_name,
        "segment_id": segment_id,
        "shot_id": int(payload["shot_id"][0]) if "shot_id" in payload else parse_shot_id_from_filename(path.name),
        "segment_num": int(payload["segment_num"][0]) if "segment_num" in payload else 0,
        "sample_ms": float(payload["sample_ms"][0]),
        "split_basis": split_basis,
        "rec_peg": payload["rec_peg"].astype(np.float32) if "rec_peg" in payload else None,
        "rec_x": payload["rec_x"].astype(np.float32) if "rec_x" in payload else None,
        "rec_y": payload["rec_y"].astype(np.float32) if "rec_y" in payload else None,
        "rec_ht": payload["rec_ht"].astype(np.float32) if "rec_ht" in payload else None,
        "source_x": float(payload["source_x"][0]) if "source_x" in payload else float("nan"),
        "source_y": float(payload["source_y"][0]) if "source_y" in payload else float("nan"),
        "source_ht": float(payload["source_ht"][0]) if "source_ht" in payload else float("nan"),
    }
