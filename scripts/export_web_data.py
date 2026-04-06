import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
import base64

from seismic_first_break_picker.correction import predict_corrected_panel
from seismic_first_break_picker.data import load_segment
from seismic_first_break_picker.metrics import compute_metric_bundle
from seismic_first_break_picker.modeling import load_model_artifact

def apply_image_normalization(panel):
    p = panel.copy().astype(float)
    vmin = np.percentile(p, 2)
    vmax = np.percentile(p, 98)
    p = np.clip((p - vmin) / (vmax - vmin), 0, 1)
    return (p * 255).astype(np.uint8)

def main():
    root = Path(__file__).resolve().parent.parent
    interim_dir = root / "data" / "interim"
    processed_dir = root / "data" / "processed"
    reports_dir = root / "reports"
    web_data_dir = root / "web" / "public" / "data"
    
    web_data_dir.mkdir(parents=True, exist_ok=True)
    
    segments_dir = interim_dir / "Halfmile_segments"
    model_path = processed_dir / "ml_correction_model.pkl"
    metrics_path = reports_dir / "evaluation" / "test_segment_metrics.csv"
    
    if not (segments_dir.exists() and model_path.exists() and metrics_path.exists()):
        print("Required artifacts not found. Please run the main pipeline first.")
        return
        
    metrics_df = pd.read_csv(metrics_path)
    
    # Identify key examples
    # 1. Best improvement
    best_row = metrics_df.loc[metrics_df["mae_improvement_ms"].idxmax()]
    # 2. Worst improvement / biggest regression
    worst_row = metrics_df.loc[metrics_df["mae_improvement_ms"].idxmin()]
    # 3. Median improvement
    median_val = metrics_df["mae_improvement_ms"].median()
    median_row = metrics_df.iloc[(metrics_df["mae_improvement_ms"] - median_val).abs().argmin()]
    # 4. Largest absolute baseline error (that got fixed well)
    high_base_err_row = metrics_df.loc[metrics_df["baseline_mae_ms"].idxmax()]
    
    target_segments = {
        "best": best_row["segment_id"],
        "worst": worst_row["segment_id"],
        "median": median_row["segment_id"],
        "high_base_err": high_base_err_row["segment_id"]
    }
    
    artifact = load_model_artifact(model_path)
    
    index_data = []
    
    for label, segment_id in target_segments.items():
        print(f"Exporting {label} ({segment_id})...")
        segment = load_segment(segments_dir / f"{segment_id}.npz")
        baseline_idx, corrected_idx = predict_corrected_panel(segment["panel"], artifact)
        
        # normalize panel to uint8 for much lighter json payload
        # we can just use 1d flattened array in json
        panel_uint8 = apply_image_normalization(segment["panel"])
        
        # also compute metrics on valid traces
        sample_ms = float(segment["sample_ms"])
        valid = segment["valid"].astype(bool)
        
        b_metrics = compute_metric_bundle(baseline_idx, segment["fb_idx"], valid, sample_ms)
        c_metrics = compute_metric_bundle(corrected_idx, segment["fb_idx"], valid, sample_ms)
        
        out_data = {
            "id": segment_id,
            "label": label,
            "shape": list(segment["panel"].shape), # [height, width]
            "sample_ms": sample_ms,
            "panel": panel_uint8.tolist(),
            "valid": valid.tolist(),
            "fb_idx": segment["fb_idx"].tolist(),
            "baseline_idx": baseline_idx.tolist(),
            "corrected_idx": corrected_idx.tolist(),
            "metrics": {
                "baseline_mae": b_metrics["mae_ms"],
                "corrected_mae": c_metrics["mae_ms"],
                "improvement_mae": b_metrics["mae_ms"] - c_metrics["mae_ms"]
            }
        }
        
        with open(web_data_dir / f"{segment_id}.json", "w") as f:
            json.dump(out_data, f)
            
        index_data.append({
            "id": segment_id,
            "label": label,
            "metrics": out_data["metrics"]
        })
        
    with open(web_data_dir / "index.json", "w") as f:
        json.dump(index_data, f)
        
    print(f"Exported {len(target_segments)} segments to {web_data_dir}")

if __name__ == "__main__":
    main()
