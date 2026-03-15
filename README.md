# Seismic First-Break Picker

CPU-only first-break picking pipeline for seismic HDF5 assets. The verified run in this workspace targets `Halfmile`; the code path is asset-ready for `Brunswick`, `Lalor`, and `Sudbury`, but those raw files are not present locally and were not executed.

## Problem

The task is to reconstruct 2D seismic images from flat trace storage and automatically pick the first seismic arrival on each trace. The labels are stored in `SPARE1` as milliseconds. Unlabeled traces use `0` or `-1`.

## Verified Halfmile Snapshot

- Raw file: `data/raw/Halfmile3D_add_geom_sorted.hdf5`
- HDF5 group: `TRACE_DATA/DEFAULT`
- Total traces: `1,099,559`
- Samples per trace: `751`
- Sampling interval: `2.0 ms`
- Unique shots: `690`
- Labeled traces: `993,189` (`90.33%`)

## Implemented Method

### 1. Segment export

- Read traces from `TRACE_DATA/DEFAULT`.
- Use `SHOTID` with `SHOT_PEG` fallback.
- Apply SEG-Y style scale handling to coordinates and elevations via `COORD_SCALE` and `HT_SCALE`.
- Reorder each shot by receiver geometry using `REC_PEG` with `REC_X` fallback.
- Split large receiver gaps into 2D segments using `jump_factor=8.0`.
- Keep only segments with at least `80` traces and at least `70` valid labels.

Verified Halfmile export:

- Exported segments: `5,391`
- Usable shots after filtering: `689` (`1` raw shot produced no retained segment)
- Trace count per segment: min `97`, mean `149.51`, max `201`
- Valid labels per segment: min `70`, mean `135.32`, max `201`

### 2. Shot-disjoint split

- Grouping key: `asset_name + shot_id`
- Seed: `42`
- Ratios: `70%` train, `10%` validation, `20%` test
- Overlap check: `0` shot overlaps across all split pairs

Verified Halfmile split:

| Split | Shots | Segments |
| --- | ---: | ---: |
| Train | 482 | 3,779 |
| Validation | 68 | 526 |
| Test | 139 | 1,086 |

### 3. Refined baseline picker

The baseline is a trace-wise heuristic with panel-level smoothing:

- moving-average envelope on each trace
- early-time noise estimate and threshold crossing for a rough pick
- smooth rough picks across traces
- local derivative-based refinement around the smoothed prior
- final median + mean smoothing across the pick line

Implementation lives in `seismic_first_break_picker/baseline.py`.

### 4. ML correction stage

The model does not predict picks from scratch. It learns a correction to the refined baseline.

- Patch centered on the baseline pick
- Patch shape: `81 x 5`
- Flattened feature size: `405`
- `trace_stride=3`
- `max_abs_correction=60` samples

Verified Halfmile datasets:

| Dataset | Examples | Feature shape |
| --- | ---: | --- |
| Train | 146,767 | `(146767, 405)` |
| Validation | 21,354 | `(21354, 405)` |
| Test | 42,072 | `(42072, 405)` |

### 5. CPU-only model selection

Model family: `HistGradientBoostingRegressor`

Why this model:

- works well on dense tabular features
- no GPU dependency
- fast enough for local CPU-only iteration
- stable inference on full panels

Candidate search was run on the validation dataset built from held-out shots. The selected configuration was:

```json
{
  "learning_rate": 0.04,
  "max_iter": 260,
  "max_depth": 8,
  "min_samples_leaf": 25,
  "l2_regularization": 0.0
}
```

Best validation result on correction examples:

- Baseline MAE: `18.769 ms`
- Corrected MAE: `10.643 ms`
- Baseline RMSE: `33.427 ms`
- Corrected RMSE: `22.079 ms`

### 6. Held-out full-segment evaluation

Final reporting is done on full test segments, not on isolated correction examples.

- Test segments evaluated: `1,086`
- Valid labeled traces evaluated: `146,594`
- For each held-out segment, both the refined baseline and ML-corrected pick line are generated over the full panel
- Metrics are computed only on valid labels

Verified Halfmile test results:

| Method | MAE (ms) | RMSE (ms) | Acc <= 2 ms | Acc <= 4 ms | Acc <= 8 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Refined baseline | 47.694 | 96.458 | 22.662% | 34.172% | 48.610% |
| ML corrected | 37.213 | 87.026 | 36.186% | 50.193% | 62.340% |
| Improvement | 10.481 | 9.433 | +13.524 pts | +16.021 pts | +13.729 pts |

Per-segment behavior on the held-out test set:

- Improved segments: `1,048 / 1,086` (`96.50%`)
- Worsened segments: `36 / 1,086` (`3.31%`)
- Unchanged segments: `2 / 1,086`
- Mean per-segment MAE gain: `10.325 ms`
- Median per-segment MAE gain: `7.747 ms`
- Worst regression: `-10.083 ms`

Representative figures:

- Best: `reports/evaluation/figures/best_Halfmile_shot20301149_seg000.png`
- Median: `reports/evaluation/figures/median_Halfmile_shot20261181_seg001.png`
- Worst: `reports/evaluation/figures/worst_Halfmile_shot20041590_seg005.png`
- Regression case: `reports/evaluation/figures/regression_Halfmile_shot20121514_seg024.png`

## Repository Layout

- `seismic_first_break_picker/`: shared package for loading, export, baseline picking, correction features, model training, evaluation, and plots
- `scripts/`: thin CLIs
- `tests/`: lightweight regression tests for split integrity, patch extraction, metrics, and model reload
- `reports/evaluation/`: held-out metrics, summary tables, and representative figures
- `reports/presentation/`: presentation source

## Reproducible Commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the full Halfmile pipeline in one command:

```bash
python scripts/run_halfmile_pipeline.py --raw_path data/raw/Halfmile3D_add_geom_sorted.hdf5
```

Step-by-step commands:

```bash
python scripts/export_segments.py --path data/raw/Halfmile3D_add_geom_sorted.hdf5 --out_dir data/interim/Halfmile_segments --asset_name Halfmile
python scripts/split_segments_train_test.py --segments_dir data/interim/Halfmile_segments --manifest_path data/interim/Halfmile_segments/Halfmile_segments_manifest.json --out_dir data/processed/splits --train_ratio 0.7 --val_ratio 0.1 --seed 42
python scripts/build_ml_dataset.py --segments_dir data/interim/Halfmile_segments --split_json data/processed/splits/train_segments.json --out_npz data/processed/ml_train_dataset.npz
python scripts/build_ml_dataset.py --segments_dir data/interim/Halfmile_segments --split_json data/processed/splits/val_segments.json --out_npz data/processed/ml_val_dataset.npz
python scripts/build_ml_dataset.py --segments_dir data/interim/Halfmile_segments --split_json data/processed/splits/test_segments.json --out_npz data/processed/ml_test_dataset.npz
python scripts/train_ml_correction_model.py --train_npz data/processed/ml_train_dataset.npz --val_npz data/processed/ml_val_dataset.npz --out_model data/processed/ml_correction_model.pkl --out_report data/processed/ml_correction_training_report.json
python scripts/evaluate_ml_correction_model.py --segments_dir data/interim/Halfmile_segments --test_split_json data/processed/splits/test_segments.json --model_pkl data/processed/ml_correction_model.pkl --out_dir reports/evaluation
```

Inspect the raw HDF5 file:

```bash
python scripts/inspect_hdf5.py --path data/raw/Halfmile3D_add_geom_sorted.hdf5
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Output Artifacts

Primary outputs:

- `data/interim/Halfmile_segments/Halfmile_segments_manifest.json`
- `data/processed/splits/split_summary.json`
- `data/processed/ml_train_dataset.npz`
- `data/processed/ml_val_dataset.npz`
- `data/processed/ml_test_dataset.npz`
- `data/processed/ml_correction_model.pkl`
- `data/processed/ml_correction_training_report.json`
- `reports/evaluation/test_summary.json`
- `reports/evaluation/test_summary_table.csv`
- `reports/evaluation/test_segment_metrics.csv`
- `reports/evaluation/methodology_results_summary.md`
- `reports/presentation/final_presentation.md`

## Limits

- Final verified results are for `Halfmile` only.
- The other three assets are supported at the code level but remain unverified until their raw HDF5 files are added locally.
- This iteration is intentionally CPU-only.
- Older segment-random metrics are historical only and should not be reported as final performance.
