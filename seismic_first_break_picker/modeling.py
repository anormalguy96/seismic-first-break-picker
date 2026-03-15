from __future__ import annotations

import os
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

from pathlib import Path
import json
import pickle

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from .correction import load_dataset
from .metrics import summarize_error_ms


DEFAULT_CANDIDATES = [
    {"learning_rate": 0.05, "max_iter": 200, "max_depth": 6, "min_samples_leaf": 30, "l2_regularization": 0.10},
    {"learning_rate": 0.03, "max_iter": 300, "max_depth": 6, "min_samples_leaf": 20, "l2_regularization": 0.05},
    {"learning_rate": 0.08, "max_iter": 160, "max_depth": 5, "min_samples_leaf": 40, "l2_regularization": 0.20},
    {"learning_rate": 0.04, "max_iter": 260, "max_depth": 8, "min_samples_leaf": 25, "l2_regularization": 0.00},
]


def _make_model(config: dict[str, float | int]) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=float(config["learning_rate"]),
        max_iter=int(config["max_iter"]),
        max_depth=int(config["max_depth"]),
        min_samples_leaf=int(config["min_samples_leaf"]),
        l2_regularization=float(config["l2_regularization"]),
        random_state=42,
        verbose=0,
    )


def _candidate_validation_metrics(
    dataset: dict[str, np.ndarray],
    predicted_correction: np.ndarray,
) -> dict[str, float]:
    baseline = dataset["meta_baseline"].astype(np.int32)
    truth = dataset["meta_true"].astype(np.int32)
    sample_ms = dataset["meta_sample_ms"].astype(np.float32)
    corrected = baseline + predicted_correction

    baseline_err = np.abs(baseline - truth) * sample_ms
    corrected_err = np.abs(corrected - truth) * sample_ms
    target_err = np.abs(predicted_correction - dataset["y"])

    baseline_metrics = summarize_error_ms(baseline_err)
    corrected_metrics = summarize_error_ms(corrected_err)

    metrics = {
        "target_mae_samples": float(np.mean(target_err)),
        "target_rmse_samples": float(np.sqrt(np.mean((predicted_correction - dataset["y"]) ** 2))),
        "baseline_mae_ms": baseline_metrics["mae_ms"],
        "baseline_rmse_ms": baseline_metrics["rmse_ms"],
        "baseline_acc_2ms": baseline_metrics["acc_2ms"],
        "baseline_acc_4ms": baseline_metrics["acc_4ms"],
        "baseline_acc_8ms": baseline_metrics["acc_8ms"],
        "corrected_mae_ms": corrected_metrics["mae_ms"],
        "corrected_rmse_ms": corrected_metrics["rmse_ms"],
        "corrected_acc_2ms": corrected_metrics["acc_2ms"],
        "corrected_acc_4ms": corrected_metrics["acc_4ms"],
        "corrected_acc_8ms": corrected_metrics["acc_8ms"],
    }
    metrics["mae_improvement_ms"] = metrics["baseline_mae_ms"] - metrics["corrected_mae_ms"]
    return metrics


def save_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def train_model_with_validation(
    train_npz: Path | str,
    val_npz: Path | str,
    out_model: Path | str,
    out_report: Path | str,
    candidates: list[dict[str, float | int]] | None = None,
) -> tuple[Path, Path]:
    train = load_dataset(train_npz)
    val = load_dataset(val_npz)

    candidate_grid = candidates or DEFAULT_CANDIDATES
    results = []
    best_entry = None

    for candidate_idx, config in enumerate(candidate_grid):
        model = _make_model(config)
        model.fit(train["X"], train["y"])

        predicted_correction = np.rint(model.predict(val["X"])).astype(np.int32)
        metrics = _candidate_validation_metrics(val, predicted_correction)
        entry = {
            "candidate_index": candidate_idx,
            "config": config,
            "validation_metrics": metrics,
        }
        results.append(entry)

        if best_entry is None or metrics["corrected_mae_ms"] < best_entry["validation_metrics"]["corrected_mae_ms"]:
            best_entry = entry

        print(
            f"Candidate {candidate_idx}: "
            f"val corrected MAE={metrics['corrected_mae_ms']:.3f} ms, "
            f"val corrected RMSE={metrics['corrected_rmse_ms']:.3f} ms"
        )

    if best_entry is None:
        raise RuntimeError("No candidate models were trained.")

    x_refit = np.concatenate([train["X"], val["X"]], axis=0)
    y_refit = np.concatenate([train["y"], val["y"]], axis=0)
    final_model = _make_model(best_entry["config"])
    final_model.fit(x_refit, y_refit)

    artifact = {
        "model": final_model,
        "selected_config": best_entry["config"],
        "candidate_results": results,
        "feature_spec": {
            "half_width": int(train["half_width"][0]),
            "half_height": int(train["half_height"][0]),
            "trace_stride": int(train["trace_stride"][0]),
            "max_abs_correction": int(train["max_abs_correction"][0]),
        },
        "dataset_summary": {
            "train_examples": int(train["X"].shape[0]),
            "val_examples": int(val["X"].shape[0]),
            "refit_examples": int(x_refit.shape[0]),
        },
    }

    model_path = Path(out_model)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, "wb") as handle:
        pickle.dump(artifact, handle)

    report_path = Path(out_report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(
        report_path,
        {
            "selected_config": best_entry["config"],
            "dataset_summary": artifact["dataset_summary"],
            "feature_spec": artifact["feature_spec"],
            "candidate_results": results,
        },
    )

    print(f"Selected config : {best_entry['config']}")
    print(f"Saved model     : {model_path}")
    print(f"Saved report    : {report_path}")
    return model_path, report_path


def load_model_artifact(model_pkl: Path | str) -> dict[str, object]:
    with open(model_pkl, "rb") as handle:
        artifact = pickle.load(handle)

    if isinstance(artifact, dict) and "model" in artifact:
        return artifact

    return {
        "model": artifact,
        "selected_config": {},
        "candidate_results": [],
        "feature_spec": {"half_width": 2, "half_height": 40, "trace_stride": 3, "max_abs_correction": 60},
        "dataset_summary": {},
    }
