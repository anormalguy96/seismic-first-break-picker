from __future__ import annotations

import numpy as np


def valid_error_ms(
    pred_idx: np.ndarray,
    true_idx: np.ndarray,
    valid: np.ndarray,
    sample_ms: float,
) -> np.ndarray:
    mask = np.asarray(valid, dtype=bool)
    if not np.any(mask):
        return np.empty(0, dtype=np.float32)
    err = np.abs(pred_idx[mask] - true_idx[mask]) * sample_ms
    return err.astype(np.float32)


def mae_ms(pred_idx: np.ndarray, true_idx: np.ndarray, valid: np.ndarray, sample_ms: float) -> float:
    err = valid_error_ms(pred_idx, true_idx, valid, sample_ms)
    return float(np.mean(err)) if err.size else float("nan")


def rmse_ms(pred_idx: np.ndarray, true_idx: np.ndarray, valid: np.ndarray, sample_ms: float) -> float:
    mask = np.asarray(valid, dtype=bool)
    if not np.any(mask):
        return float("nan")
    err = (pred_idx[mask] - true_idx[mask]) * sample_ms
    return float(np.sqrt(np.mean(err**2)))


def within_tol(
    pred_idx: np.ndarray,
    true_idx: np.ndarray,
    valid: np.ndarray,
    sample_ms: float,
    tol_ms: float,
) -> float:
    err = valid_error_ms(pred_idx, true_idx, valid, sample_ms)
    return float(np.mean(err <= tol_ms) * 100.0) if err.size else float("nan")


def compute_metric_bundle(
    pred_idx: np.ndarray,
    true_idx: np.ndarray,
    valid: np.ndarray,
    sample_ms: float,
) -> dict[str, float]:
    return {
        "mae_ms": mae_ms(pred_idx, true_idx, valid, sample_ms),
        "rmse_ms": rmse_ms(pred_idx, true_idx, valid, sample_ms),
        "acc_2ms": within_tol(pred_idx, true_idx, valid, sample_ms, 2.0),
        "acc_4ms": within_tol(pred_idx, true_idx, valid, sample_ms, 4.0),
        "acc_8ms": within_tol(pred_idx, true_idx, valid, sample_ms, 8.0),
    }


def summarize_error_ms(errors_ms: np.ndarray) -> dict[str, float]:
    errors = np.asarray(errors_ms, dtype=np.float32)
    if errors.size == 0:
        return {
            "mae_ms": float("nan"),
            "rmse_ms": float("nan"),
            "acc_2ms": float("nan"),
            "acc_4ms": float("nan"),
            "acc_8ms": float("nan"),
            "valid_trace_count": 0,
        }

    return {
        "mae_ms": float(np.mean(errors)),
        "rmse_ms": float(np.sqrt(np.mean(errors**2))),
        "acc_2ms": float(np.mean(errors <= 2.0) * 100.0),
        "acc_4ms": float(np.mean(errors <= 4.0) * 100.0),
        "acc_8ms": float(np.mean(errors <= 8.0) * 100.0),
        "valid_trace_count": int(errors.size),
    }
