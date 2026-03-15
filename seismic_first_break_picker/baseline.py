from __future__ import annotations

import numpy as np


def moving_average_1d(x: np.ndarray, window: int) -> np.ndarray:
    if len(x) == 0:
        return x.copy()
    window = max(1, min(int(window), len(x)))
    if window <= 1:
        return x.copy()
    kernel = np.ones(window, dtype=np.float32) / window
    return np.convolve(x, kernel, mode="same")


def median_filter_1d(x: np.ndarray, window: int) -> np.ndarray:
    if window <= 1:
        return x.copy()
    pad = window // 2
    x_pad = np.pad(x, (pad, pad), mode="edge")
    out = np.empty_like(x)
    for idx in range(len(x)):
        out[idx] = np.median(x_pad[idx : idx + window])
    return out


def robust_smooth_line(
    x: np.ndarray,
    median_window: int = 9,
    mean_window: int = 21,
) -> np.ndarray:
    y = median_filter_1d(x.astype(np.float32), median_window)
    y = moving_average_1d(y, mean_window)
    return y


def rough_pick_one_trace(
    trace: np.ndarray,
    noise_window: int = 100,
    smooth_window: int = 11,
    threshold_scale: float = 4.0,
    min_pick: int = 20,
) -> int:
    x = trace.astype(np.float32)
    env = moving_average_1d(np.abs(x), smooth_window)

    early = env[:noise_window]
    mu = float(np.mean(early))
    sigma = float(np.std(early))
    threshold = mu + threshold_scale * sigma

    candidates = np.where(env[min_pick:] > threshold)[0]
    if len(candidates) == 0:
        return int(np.argmax(env))

    return int(candidates[0] + min_pick)


def refine_pick_near_prior(
    trace: np.ndarray,
    prior_idx: int,
    search_radius: int = 30,
    smooth_window: int = 7,
) -> int:
    x = trace.astype(np.float32)
    env = moving_average_1d(np.abs(x), smooth_window)
    deriv = np.diff(env, prepend=env[0])

    left = max(0, int(prior_idx - search_radius))
    right = min(len(trace), int(prior_idx + search_radius + 1))
    local_deriv = deriv[left:right]

    if len(local_deriv) == 0:
        return int(prior_idx)

    best_local = int(np.argmax(local_deriv))
    return int(left + best_local)


def pick_first_break_panel_refined(panel: np.ndarray) -> np.ndarray:
    n_traces = panel.shape[1]

    rough = np.zeros(n_traces, dtype=np.int32)
    for trace_idx in range(n_traces):
        rough[trace_idx] = rough_pick_one_trace(panel[:, trace_idx])

    prior = robust_smooth_line(rough, median_window=9, mean_window=25)

    refined = np.zeros(n_traces, dtype=np.int32)
    for trace_idx in range(n_traces):
        refined[trace_idx] = refine_pick_near_prior(
            panel[:, trace_idx],
            int(round(prior[trace_idx])),
            search_radius=28,
        )

    refined = robust_smooth_line(refined, median_window=7, mean_window=11)
    return np.rint(refined).astype(np.int32)
