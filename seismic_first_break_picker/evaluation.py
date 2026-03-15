from __future__ import annotations

from pathlib import Path
import csv
import json

import numpy as np
from tqdm import tqdm

from .correction import predict_corrected_panel
from .data import load_segment, load_split_file
from .metrics import compute_metric_bundle, summarize_error_ms, valid_error_ms
from .visualization import save_comparison_preview


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def evaluate_split(
    segments_dir: Path | str,
    split_json: Path | str,
    artifact: dict[str, object],
    out_dir: Path | str,
) -> dict[str, object]:
    source_dir = Path(segments_dir)
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    filenames = load_split_file(split_json)
    segment_rows: list[dict[str, object]] = []
    segment_details: list[dict[str, object]] = []
    baseline_errors = []
    corrected_errors = []

    for filename in tqdm(filenames, desc="Evaluating test segments"):
        segment = load_segment(source_dir / filename)
        baseline, corrected = predict_corrected_panel(segment["panel"], artifact)

        baseline_bundle = compute_metric_bundle(baseline, segment["fb_idx"], segment["valid"], segment["sample_ms"])
        corrected_bundle = compute_metric_bundle(corrected, segment["fb_idx"], segment["valid"], segment["sample_ms"])

        baseline_errors.append(valid_error_ms(baseline, segment["fb_idx"], segment["valid"], segment["sample_ms"]))
        corrected_errors.append(valid_error_ms(corrected, segment["fb_idx"], segment["valid"], segment["sample_ms"]))

        row = {
            "segment_id": segment["segment_id"],
            "asset_name": segment["asset_name"],
            "shot_id": segment["shot_id"],
            "segment_num": segment["segment_num"],
            "trace_count": int(segment["panel"].shape[1]),
            "valid_trace_count": int(np.sum(segment["valid"])),
            "baseline_mae_ms": baseline_bundle["mae_ms"],
            "baseline_rmse_ms": baseline_bundle["rmse_ms"],
            "baseline_acc_2ms": baseline_bundle["acc_2ms"],
            "baseline_acc_4ms": baseline_bundle["acc_4ms"],
            "baseline_acc_8ms": baseline_bundle["acc_8ms"],
            "corrected_mae_ms": corrected_bundle["mae_ms"],
            "corrected_rmse_ms": corrected_bundle["rmse_ms"],
            "corrected_acc_2ms": corrected_bundle["acc_2ms"],
            "corrected_acc_4ms": corrected_bundle["acc_4ms"],
            "corrected_acc_8ms": corrected_bundle["acc_8ms"],
            "mae_improvement_ms": baseline_bundle["mae_ms"] - corrected_bundle["mae_ms"],
        }
        segment_rows.append(row)
        segment_details.append(
            {
                "row": row,
                "panel": segment["panel"],
                "manual_idx": segment["fb_idx"],
                "valid": segment["valid"],
                "baseline": baseline,
                "corrected": corrected,
            }
        )

    if not segment_rows:
        raise ValueError("No test segments were evaluated.")

    baseline_errors_ms = np.concatenate(baseline_errors)
    corrected_errors_ms = np.concatenate(corrected_errors)
    baseline_summary = summarize_error_ms(baseline_errors_ms)
    corrected_summary = summarize_error_ms(corrected_errors_ms)

    summary = {
        "segment_count": len(segment_rows),
        "baseline": baseline_summary,
        "corrected": corrected_summary,
        "improvement": {
            "mae_ms": baseline_summary["mae_ms"] - corrected_summary["mae_ms"],
            "rmse_ms": baseline_summary["rmse_ms"] - corrected_summary["rmse_ms"],
            "acc_2ms": corrected_summary["acc_2ms"] - baseline_summary["acc_2ms"],
            "acc_4ms": corrected_summary["acc_4ms"] - baseline_summary["acc_4ms"],
            "acc_8ms": corrected_summary["acc_8ms"] - baseline_summary["acc_8ms"],
        },
    }

    metrics_csv = target_dir / "test_segment_metrics.csv"
    summary_json = target_dir / "test_summary.json"
    summary_table_csv = target_dir / "test_summary_table.csv"

    _write_csv(metrics_csv, segment_rows, fieldnames=list(segment_rows[0].keys()))
    _write_csv(
        summary_table_csv,
        [
            {"method": "refined_baseline", **baseline_summary},
            {"method": "ml_corrected", **corrected_summary},
        ],
        fieldnames=["method", "mae_ms", "rmse_ms", "acc_2ms", "acc_4ms", "acc_8ms", "valid_trace_count"],
    )

    ordered = sorted(segment_details, key=lambda item: item["row"]["corrected_mae_ms"])
    representative = {"best": ordered[0], "median": ordered[len(ordered) // 2], "worst": ordered[-1]}
    representative_paths = {}

    for label, item in representative.items():
        out_path = target_dir / "figures" / f"{label}_{item['row']['segment_id']}.png"
        save_comparison_preview(
            panel=item["panel"],
            manual_idx=item["manual_idx"],
            valid=item["valid"],
            baseline_idx=item["baseline"],
            corrected_idx=item["corrected"],
            title=(
                f"{label.title()} example | {item['row']['segment_id']} | "
                f"baseline MAE {item['row']['baseline_mae_ms']:.2f} ms | "
                f"corrected MAE {item['row']['corrected_mae_ms']:.2f} ms"
            ),
            out_path=out_path,
        )
        representative_paths[label] = str(out_path)

    regression = min(segment_rows, key=lambda item: item["mae_improvement_ms"])
    regression_detail = next(detail for detail in segment_details if detail["row"]["segment_id"] == regression["segment_id"])
    regression_path = target_dir / "figures" / f"regression_{regression['segment_id']}.png"
    save_comparison_preview(
        panel=regression_detail["panel"],
        manual_idx=regression_detail["manual_idx"],
        valid=regression_detail["valid"],
        baseline_idx=regression_detail["baseline"],
        corrected_idx=regression_detail["corrected"],
        title=(
            f"Regression example | {regression['segment_id']} | "
            f"baseline MAE {regression['baseline_mae_ms']:.2f} ms | "
            f"corrected MAE {regression['corrected_mae_ms']:.2f} ms"
        ),
        out_path=regression_path,
    )

    summary["representative_figures"] = representative_paths
    summary["regression_figure"] = str(regression_path)
    summary["regression_segment"] = regression
    _write_json(summary_json, summary)

    print(f"Evaluated segments : {summary['segment_count']}")
    print(f"Baseline MAE (ms)  : {summary['baseline']['mae_ms']:.3f}")
    print(f"Corrected MAE (ms) : {summary['corrected']['mae_ms']:.3f}")
    print(f"Summary JSON       : {summary_json}")
    print(f"Summary table CSV  : {summary_table_csv}")
    print(f"Per-segment CSV    : {metrics_csv}")
    return summary
