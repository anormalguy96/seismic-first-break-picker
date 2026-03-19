# Seismic First-Break Picker

## Project Purpose

This repository implements a reproducible, CPU-only workflow for seismic first-break picking on HDF5 trace assets. The workflow is designed to:

1. read a raw seismic HDF5 file;
2. reconstruct receiver-ordered 2D shot segments from flat trace storage;
3. generate a refined heuristic first-break baseline;
4. train a machine-learning model that predicts a correction to that baseline; and
5. evaluate the final corrected picks on held-out shots.

The implementation is intended for local experimentation, method reporting, and reproducible evaluation. The codebase is asset-ready for `Halfmile`, `Brunswick`, `Lalor`, and `Sudbury`. In the current workspace, only the `Halfmile` raw file is present and has been verified end to end.

## Verified Local Scope

The verified raw asset in this workspace is:

- Raw file: `data/raw/Halfmile3D_add_geom_sorted.hdf5`
- HDF5 group used by the pipeline: `TRACE_DATA/DEFAULT`
- Total traces: `1,099,559`
- Samples per trace: `751`
- Sampling interval: `2.0 ms`
- Unique shots in raw storage: `690`
- Labeled traces: `993,189` (`90.33%`)

This means the README below describes the full production path that was executed locally for `Halfmile`. The same code path should apply to the other listed assets once their raw HDF5 files are added, but those runs remain unverified in this repository state.

## End-to-End Method Summary

The full method proceeds in seven stages.

### Stage 1. Raw Ingest

The pipeline reads trace arrays and metadata from `TRACE_DATA/DEFAULT`. Shot identity is taken from `SHOTID`, with `SHOT_PEG` used as a fallback when necessary. Coordinate and elevation scale factors are applied so that receiver geometry can be interpreted correctly.

### Stage 2. Segment Export

The raw traces are regrouped into 2D shot segments. Within each shot, traces are ordered by receiver geometry using `REC_PEG`, with `REC_X` as a fallback. Large receiver gaps are used to split discontinuous layouts into separate segments. Segments that are too short or too sparsely labeled are discarded.

### Stage 3. Shot-Disjoint Splitting

The exported segments are split at the shot level, not at random segment level. This prevents the same shot from appearing in both training and evaluation data, which would overstate model quality.

### Stage 4. Refined Baseline Picking

The first model-free estimate is a refined heuristic picker. It uses a moving-average envelope, an early-time noise estimate, a threshold-based rough pick, cross-trace smoothing, and local derivative refinement. This stage establishes the baseline that the machine-learning model will correct.

### Stage 5. Correction Dataset Construction

The machine-learning stage does not predict picks from scratch. Instead, it extracts a local patch around the baseline pick on valid traces and learns the residual correction needed to move the baseline toward the ground-truth label.

### Stage 6. Model Training

A `HistGradientBoostingRegressor` is trained on the correction examples. This model family was selected because it is well suited to dense tabular features, requires no GPU support, and remains practical for local CPU-only execution.

### Stage 7. Held-Out Evaluation

The saved model is applied to the full held-out test split. Both the refined baseline and the corrected picks are generated for every segment, and metrics are computed only on traces with valid labels.

## Environment Setup

Install the required Python packages with:

```bash
pip install -r requirements.txt
```

The dependency set is intentionally compact and CPU-oriented:

- `numpy`
- `scipy`
- `pandas`
- `matplotlib`
- `h5py`
- `scikit-learn`
- `tqdm`
- `pyyaml`
- `jupyter`

## Step-by-Step Execution

This section documents the recommended execution order. Each step explains its role, the command to run, and the artifact it produces.

### Step 1. Inspect the Raw HDF5 Asset

The first step is to confirm that the raw file is readable and that the expected keys are present. This is useful before any export job is started because it reveals the basic dimensions, metadata fields, and structure of the asset.

```bash
python scripts/inspect_hdf5.py --path data/raw/Halfmile3D_add_geom_sorted.hdf5
```

This inspection step does not create downstream artifacts. Its purpose is validation and orientation: it confirms the dataset structure, the trace count, the sample count, and the metadata fields that will be used in export.

### Step 2. Export Receiver-Ordered Segments

The export stage converts flat trace storage into usable 2D segments. This is the most important data-preparation step because the downstream baseline picker, correction dataset builder, and evaluator all operate on exported segment files.

```bash
python scripts/export_segments.py --path data/raw/Halfmile3D_add_geom_sorted.hdf5 --out_dir data/interim/Halfmile_segments --asset_name Halfmile
```

The exporter performs the following operations:

- reads traces and metadata from `TRACE_DATA/DEFAULT`;
- determines the shot identifier from `SHOTID`, with `SHOT_PEG` fallback;
- applies `COORD_SCALE` and `HT_SCALE` to geometry-related fields;
- orders traces within each shot by receiver geometry;
- splits shots into multiple segments when the receiver layout contains large gaps;
- removes segments with fewer than `80` traces; and
- removes segments with fewer than `70` valid labels.

For the verified `Halfmile` run, this step produced:

- `5,391` exported segments;
- `689` usable shots after filtering; and
- the manifest file `data/interim/Halfmile_segments/Halfmile_segments_manifest.json`.

### Step 3. Create Shot-Disjoint Train, Validation, and Test Splits

After export, the segment manifest must be partitioned into train, validation, and test subsets. This split is performed at the shot level so that no shot appears in more than one subset.

```bash
python scripts/split_segments_train_test.py --segments_dir data/interim/Halfmile_segments --manifest_path data/interim/Halfmile_segments/Halfmile_segments_manifest.json --out_dir data/processed/splits --train_ratio 0.7 --val_ratio 0.1 --seed 42
```

This command writes JSON lists of segment identifiers for each split and a summary file describing the assignment. The verified `Halfmile` split was:

| Split | Shots | Segments |
| --- | ---: | ---: |
| Train | 482 | 3,779 |
| Validation | 68 | 526 |
| Test | 139 | 1,086 |

The overlap check was `0` for all split pairs, which confirms that the split is fully shot-disjoint.

### Step 4. Build the Machine-Learning Correction Datasets

The next step converts exported segments into learning examples. Each example is centered on a baseline pick and contains a local spatiotemporal patch plus the target correction that would move the baseline toward the true first break.

```bash
python scripts/build_ml_dataset.py --segments_dir data/interim/Halfmile_segments --split_json data/processed/splits/train_segments.json --out_npz data/processed/ml_train_dataset.npz
python scripts/build_ml_dataset.py --segments_dir data/interim/Halfmile_segments --split_json data/processed/splits/val_segments.json --out_npz data/processed/ml_val_dataset.npz
python scripts/build_ml_dataset.py --segments_dir data/interim/Halfmile_segments --split_json data/processed/splits/test_segments.json --out_npz data/processed/ml_test_dataset.npz
```

The default feature specification is:

- `half_width=2`, which yields `5` traces across the patch;
- `half_height=40`, which yields `81` time samples per trace;
- `trace_stride=3`, which reduces near-duplicate adjacent examples; and
- `max_abs_correction=60`, which removes extreme correction targets.

This means each feature vector has shape `81 x 5 = 405`.

For the verified `Halfmile` run, the generated datasets were:

| Dataset | Examples | Feature Shape |
| --- | ---: | --- |
| Train | 146,767 | `(146767, 405)` |
| Validation | 21,354 | `(21354, 405)` |
| Test | 42,072 | `(42072, 405)` |

### Step 5. Train the Correction Model

Once the correction datasets have been created, the training step fits a gradient-boosted regressor on the training set and selects its final configuration using the validation set.

```bash
python scripts/train_ml_correction_model.py --train_npz data/processed/ml_train_dataset.npz --val_npz data/processed/ml_val_dataset.npz --out_model data/processed/ml_correction_model.pkl --out_report data/processed/ml_correction_training_report.json
```

This step writes two important artifacts:

- `data/processed/ml_correction_model.pkl`, which stores the fitted model and feature specification; and
- `data/processed/ml_correction_training_report.json`, which stores the candidate search results and the selected configuration.

For the verified run, the selected configuration was:

```json
{
  "learning_rate": 0.04,
  "max_iter": 260,
  "max_depth": 8,
  "min_samples_leaf": 25,
  "l2_regularization": 0.0
}
```

On the validation correction examples, this configuration reduced:

- MAE from `18.769 ms` to `10.643 ms`; and
- RMSE from `33.427 ms` to `22.079 ms`.

### Step 6. Evaluate the Trained Model on the Held-Out Test Split

The evaluation stage applies the saved model to every segment in the held-out test split. The refined baseline and the corrected pick line are both produced so that the final report can quantify the gain achieved by the correction model.

```bash
python scripts/evaluate_ml_correction_model.py --segments_dir data/interim/Halfmile_segments --test_split_json data/processed/splits/test_segments.json --model_pkl data/processed/ml_correction_model.pkl --out_dir reports/evaluation
```

This evaluation is performed on full segments rather than isolated training examples. Metrics are computed only on valid labeled traces, which is important because unlabeled traces are present in the raw asset and must not affect reported accuracy.

For the verified `Halfmile` run, the held-out test results were:

| Method | MAE (ms) | RMSE (ms) | Acc <= 2 ms | Acc <= 4 ms | Acc <= 8 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Refined baseline | 47.694 | 96.458 | 22.662% | 34.172% | 48.610% |
| ML corrected | 37.213 | 87.026 | 36.186% | 50.193% | 62.340% |
| Improvement | 10.481 | 9.433 | +13.524 pts | +16.021 pts | +13.729 pts |

At the segment level, the correction model improved `1,048` of `1,086` held-out segments, which corresponds to `96.50%` of the test set.

### Step 7. Review the Generated Reports and Figures

After evaluation, the primary report directory is `reports/evaluation`. This directory contains machine-readable summaries, per-segment metrics, and representative figures that illustrate best, median, worst, and regression cases.

Representative figure outputs include:

- `reports/evaluation/figures/best_Halfmile_shot20301149_seg000.png`
- `reports/evaluation/figures/median_Halfmile_shot20261181_seg001.png`
- `reports/evaluation/figures/worst_Halfmile_shot20041590_seg005.png`
- `reports/evaluation/figures/regression_Halfmile_shot20121514_seg024.png`

The accompanying narrative summary is stored in `reports/evaluation/methodology_results_summary.md`.

## Single-Command Pipeline Execution

If a one-command run is preferable, the repository includes a wrapper script that performs export, splitting, dataset construction, training, and evaluation in sequence.

```bash
python scripts/run_halfmile_pipeline.py --raw_path data/raw/Halfmile3D_add_geom_sorted.hdf5
```

If exported segments already exist and should be reused, the export stage can be skipped:

```bash
python scripts/run_halfmile_pipeline.py --raw_path data/raw/Halfmile3D_add_geom_sorted.hdf5 --skip_export
```

This wrapper is appropriate for a clean end-to-end run. The step-by-step commands remain preferable when intermediate inspection or troubleshooting is required.

## Notebook Workflow

The `notebooks/` directory provides a guided interactive layer on top of the pipeline artifacts:

- `notebooks/01_segment_exploration.ipynb` reviews exported segments and their labels;
- `notebooks/02_baseline_and_correction_preview.ipynb` examines the baseline picker and the correction model on concrete examples; and
- `notebooks/03_results_review.ipynb` reviews evaluation outputs, summary tables, and representative figures.

These notebooks are intended for interpretation and presentation. The canonical batch workflow remains the script-based pipeline described above.

## Repository Structure

The repository is organized so that the package code, scripts, reports, tests, and notebooks serve distinct roles.

| Path | Role |
| --- | --- |
| `seismic_first_break_picker/` | Core package for export, baseline picking, correction features, model training, metrics, evaluation, and plotting |
| `scripts/` | Command-line entry points for inspection, export, splitting, dataset construction, training, preview, and evaluation |
| `data/` | Raw input, exported segment artifacts, processed datasets, and saved models |
| `reports/evaluation/` | Final metric summaries, per-segment tables, and evaluation figures |
| `reports/presentation/` | Presentation source materials |
| `notebooks/` | Interactive exploration and result-review notebooks |
| `tests/` | Lightweight regression tests for core pipeline behavior |

## Primary Output Artifacts

| Artifact | Meaning |
| --- | --- |
| `data/interim/Halfmile_segments/Halfmile_segments_manifest.json` | Manifest of all retained exported segments |
| `data/processed/splits/train_segments.json` | Train split segment list |
| `data/processed/splits/val_segments.json` | Validation split segment list |
| `data/processed/splits/test_segments.json` | Test split segment list |
| `data/processed/splits/split_summary.json` | Split statistics and overlap checks |
| `data/processed/ml_train_dataset.npz` | Training correction dataset |
| `data/processed/ml_val_dataset.npz` | Validation correction dataset |
| `data/processed/ml_test_dataset.npz` | Test correction dataset |
| `data/processed/ml_correction_model.pkl` | Saved trained correction model |
| `data/processed/ml_correction_training_report.json` | Training and model-selection report |
| `reports/evaluation/test_summary.json` | Aggregate held-out evaluation metrics |
| `reports/evaluation/test_summary_table.csv` | Tabular summary of held-out metrics |
| `reports/evaluation/test_segment_metrics.csv` | Per-segment evaluation metrics |
| `reports/evaluation/methodology_results_summary.md` | Narrative summary of method and results |

## Testing

The repository includes focused regression tests for the most important invariants in the pipeline.

Run the test suite with:

```bash
python -m unittest discover -s tests -v
```

The current tests verify:

- shot-disjoint splitting does not create overlap across train, validation, and test sets;
- patch extraction pads correctly at boundaries;
- metrics ignore unlabeled traces; and
- a trained model artifact can be saved, reloaded, and used for full-panel corrected prediction.

These tests are intentionally lightweight. They do not replace full end-to-end reruns on the real `Halfmile` asset, but they do protect the core mechanics of the workflow.

## Current Limitations

- Only the `Halfmile` asset has been executed and verified in the present workspace.
- The pipeline is intentionally CPU-only in this iteration.
- Unlabeled traces are present in the source data and must always be excluded from metric computation.
- Historical random-segment evaluations should not be treated as final results; the shot-disjoint held-out evaluation is the authoritative reporting path.

## Licence

This project is licenced under the [MIT License](LICENSE). See  for details.
