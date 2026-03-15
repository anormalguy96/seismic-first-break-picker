from __future__ import annotations

from collections import Counter
from pathlib import Path
import random

from .data import discover_segment_records, save_json


def _normalize_ratios(train_ratio: float, val_ratio: float) -> tuple[float, float, float]:
    if train_ratio <= 0 or val_ratio < 0 or train_ratio + val_ratio >= 1:
        raise ValueError("Expected train_ratio > 0, val_ratio >= 0, and train_ratio + val_ratio < 1.")
    return train_ratio, val_ratio, 1.0 - train_ratio - val_ratio


def _group_key(record: dict[str, object]) -> tuple[str, int]:
    return str(record["asset_name"]), int(record["shot_id"])


def create_shot_disjoint_splits(
    segments_dir: Path | str,
    out_dir: Path | str,
    manifest_path: Path | str | None = None,
    train_ratio: float = 0.7,
    val_ratio: float = 0.1,
    seed: int = 42,
) -> dict[str, object]:
    train_ratio, val_ratio, test_ratio = _normalize_ratios(train_ratio, val_ratio)
    source_dir = Path(segments_dir)
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest = Path(manifest_path) if manifest_path else None

    records = discover_segment_records(source_dir, manifest)
    if not records:
        raise ValueError(f"No segment records found in {source_dir}")

    shot_groups = sorted({_group_key(record) for record in records})
    rng = random.Random(seed)
    rng.shuffle(shot_groups)

    total_groups = len(shot_groups)
    train_count = int(total_groups * train_ratio)
    val_count = int(total_groups * val_ratio)
    if total_groups >= 3:
        train_count = max(1, min(train_count, total_groups - 2))
        val_count = max(1, min(val_count, total_groups - train_count - 1))
    test_count = total_groups - train_count - val_count
    if test_count <= 0:
        raise ValueError("Split settings do not leave any shots for the test split.")

    group_to_split: dict[tuple[str, int], str] = {}
    for idx, key in enumerate(shot_groups):
        if idx < train_count:
            group_to_split[key] = "train"
        elif idx < train_count + val_count:
            group_to_split[key] = "val"
        else:
            group_to_split[key] = "test"

    split_files = {"train": [], "val": [], "test": []}
    split_shots = {"train": set(), "val": set(), "test": set()}

    ordered_records = sorted(
        records,
        key=lambda item: (str(item["asset_name"]), int(item["shot_id"]), int(item["segment_num"])),
    )
    for record in ordered_records:
        split_name = group_to_split[_group_key(record)]
        split_files[split_name].append(Path(str(record["file"])).name)
        split_shots[split_name].add(_group_key(record))

    for split_name, filenames in split_files.items():
        save_json(target_dir / f"{split_name}_segments.json", filenames)

    split_summary = {
        "seed": seed,
        "ratios": {"train": train_ratio, "val": val_ratio, "test": test_ratio},
        "total_segments": len(records),
        "total_shots": total_groups,
        "splits": {},
        "overlap": {
            "train_val": len(split_shots["train"] & split_shots["val"]),
            "train_test": len(split_shots["train"] & split_shots["test"]),
            "val_test": len(split_shots["val"] & split_shots["test"]),
        },
        "asset_segment_counts": dict(Counter(str(record["asset_name"]) for record in records)),
    }

    for split_name in ("train", "val", "test"):
        shot_counter = Counter(asset for asset, _ in split_shots[split_name])
        split_summary["splits"][split_name] = {
            "segment_count": len(split_files[split_name]),
            "shot_count": len(split_shots[split_name]),
            "asset_shot_counts": dict(shot_counter),
        }

    save_json(target_dir / "split_summary.json", split_summary)

    print(f"Total segments : {len(records)}")
    print(f"Total shots    : {total_groups}")
    for split_name in ("train", "val", "test"):
        info = split_summary["splits"][split_name]
        print(f"{split_name:5s} shots={info['shot_count']:4d} segments={info['segment_count']:4d}")
    print(f"Saved split summary : {target_dir / 'split_summary.json'}")
    return split_summary
