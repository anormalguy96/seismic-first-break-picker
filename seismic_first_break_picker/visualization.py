from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def save_panel_preview(
    panel: np.ndarray,
    fb_idx: np.ndarray,
    valid: np.ndarray,
    title: str,
    out_path: Path,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(12, 5))
    plt.imshow(panel, cmap="gray", aspect="auto", origin="upper")
    if np.any(valid):
        plt.plot(np.where(valid)[0], fb_idx[valid], color="red", linewidth=1.2, label="Manual")
        plt.legend()
    plt.title(title)
    plt.xlabel("Trace index")
    plt.ylabel("Time sample")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def save_comparison_preview(
    panel: np.ndarray,
    manual_idx: np.ndarray,
    valid: np.ndarray,
    baseline_idx: np.ndarray,
    corrected_idx: np.ndarray,
    title: str,
    out_path: Path,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(12, 5))
    plt.imshow(panel, cmap="gray", aspect="auto", origin="upper")
    if np.any(valid):
        plt.plot(np.where(valid)[0], manual_idx[valid], color="red", linewidth=1.2, label="Manual")
    plt.plot(np.arange(len(baseline_idx)), baseline_idx, color="cyan", linewidth=1.0, label="Baseline")
    plt.plot(np.arange(len(corrected_idx)), corrected_idx, color="lime", linewidth=1.0, label="Corrected")
    plt.title(title)
    plt.xlabel("Trace index")
    plt.ylabel("Time sample")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
