# Halfmile First-Break Picking

Presentation source for a 25-35 minute technical talk. All metrics and artifact paths below come from the current shot-disjoint Halfmile run in this repository.

## Slide 1. Problem Statement and Goal

- Objective: detect seismic first breaks automatically from labeled HDF5 trace data.
- Business value: first-break quality affects downstream statics, refraction analysis, and tomography workflows.
- Technical requirement: reconstruct usable 2D seismic images from flat trace storage, then predict picks robustly under variable noise and changing line behavior.
- Constraint: this implementation is CPU-only because the local environment has no GPU.

Figure path: none

Speaker notes:
The key point is that the problem is not only a picker problem. The input is not already arranged as clean images; it is a large flat trace table with geometry and labels. A practical solution has to solve organization, leakage control, and evaluation discipline before the model choice matters.

## Slide 2. Dataset Overview and HDF5 Structure

- Target assets in the task: Brunswick, Halfmile, Lalor, Sudbury.
- Local verified asset: Halfmile only.
- Halfmile raw file contains `1,099,559` traces, each with `751` samples at `2.0 ms`.
- Label field is `SPARE1` in milliseconds; `0` or `-1` means unlabeled.
- Halfmile label coverage is `90.33%` with `993,189` labeled traces across `690` shots.
- Relevant geometry fields include `SHOTID`, `SHOT_PEG`, `REC_PEG`, `REC_X`, `REC_Y`, `SOURCE_X`, `SOURCE_Y`, `COORD_SCALE`, and `HT_SCALE`.

Figure path: `reports/evaluation/methodology_results_summary.md`

Speaker notes:
This slide establishes scale. The dataset is large enough that sloppy experimental design can produce misleadingly good numbers. It also explains why the loader had to be made generic: different assets may use slightly different combinations of the same fields, so the ingest stage needs sensible fallbacks.

## Slide 3. Why 2D Seismic Images Must Be Reconstructed

- The HDF5 file stores traces in a flat table, not as final shot images.
- First-break behavior is easier to model when traces are placed in receiver order within each shot.
- Receiver geometry also reveals large gaps that should split one shot into multiple coherent 2D panels.
- Without reconstruction, neighboring traces in memory are not guaranteed to be meaningful neighbors in the image domain.

Figure path: `reports/figures/split_preview_20021449/shot_20021449_segment_00.png`

Speaker notes:
The task description explicitly asks for this reorganization step, and it matters. The ML stage uses local spatial context, so the panel layout has to reflect actual receiver continuity. This is where many shortcut solutions become brittle.

## Slide 4. Halfmile Data Preparation and Segment Export

- Group traces by shot using `SHOTID`, with `SHOT_PEG` fallback for asset readiness.
- Apply SEG-Y scaling rules to coordinates and elevations before using geometry.
- Within each shot, sort by `REC_PEG`; if receiver peg is not informative, fall back to `REC_X`.
- Detect large geometry jumps with `jump_factor=8.0` and split into separate segments.
- Keep only usable segments with at least `80` traces and at least `70` valid labels.

Figure path: `reports/figures/exported_segment_previews/Halfmile_shot20241112_seg003.png`

Speaker notes:
This slide is where I would show the transformation from raw traces to clean panels. The filters are pragmatic rather than academic. Segments that are too short or too sparsely labeled are not useful for either training or honest evaluation.

## Slide 5. Label Coverage and Segmentation Statistics

- Final export produced `5,391` Halfmile segments.
- `689` shots remained after segment filtering; `1` raw shot produced no retained segment.
- Segment trace count ranges from `97` to `201`, with mean `149.51`.
- Valid labels per segment range from `70` to `201`, with mean `135.32`.
- The resulting segments are large enough to preserve local structure but small enough for CPU-friendly repeated inference.

Figure path: `reports/evaluation/methodology_results_summary.md`

Speaker notes:
These numbers matter because they define the operating unit of the pipeline. Every later stage, including the split protocol and the evaluation plots, is segment-based. The segmentation rules also reduce the chance that one pathological receiver gap distorts an entire shot panel.

## Slide 6. Baseline First-Break Picker Methodology

- Step 1: compute a smoothed envelope on each trace.
- Step 2: estimate early-time noise and trigger a rough pick using a threshold crossing.
- Step 3: smooth the rough pick line across traces to create a prior.
- Step 4: refine each trace locally with a derivative-based search around the prior.
- Step 5: smooth the final line again to suppress isolated trace noise.

Figure path: `reports/figures/baseline_refined_preview_shot20241112_seg003.png`

Speaker notes:
This baseline is not trivial. It already uses both single-trace and cross-trace information, which makes it a meaningful benchmark. That is important because the correction model is judged against a fairly strong classical method, not against a naive threshold-only picker.

## Slide 7. Why the Baseline Needs Correction

- The refined baseline is consistent on many segments but still drifts under strong noise or structural complexity.
- Errors are often locally systematic rather than random, which makes them good candidates for a learned correction model.
- Predicting a bounded correction is easier on CPU than training a full deep network from scratch.
- This two-stage design also preserves a usable fallback line if the learned stage fails.

Figure path: `reports/evaluation/figures/regression_Halfmile_shot20121514_seg024.png`

Speaker notes:
The key design decision was to learn the residual instead of replacing the entire picker. In this dataset, the baseline often lands in roughly the right neighborhood, and the job becomes local cleanup. That is a better fit for a CPU-first workflow.

## Slide 8. ML Correction Dataset Design

- For each valid trace, build a patch centered on the baseline pick.
- Patch size is `81 x 5`, which captures time context and a small neighborhood of adjacent traces.
- Flatten each patch into `405` tabular features.
- Sample every third valid trace with `trace_stride=3`.
- Discard extreme labels where `|true - baseline| > 60` samples to avoid making the model chase rare outliers.

Figure path: none

Speaker notes:
This is intentionally simple and defensible. The model sees local image texture around the current pick and learns whether the line should move up or down. The patch shape is wide enough to catch cross-trace continuity but still compact enough for fast training.

## Slide 9. CPU-First Model Choice and Training Setup

- Model family: `HistGradientBoostingRegressor`.
- Training datasets: `146,767` train examples and `21,354` validation examples.
- Four small candidate configurations were tested on the validation split.
- Final model is refit on combined train plus validation examples after selection.
- No GPU dependency, no deep learning framework, and no expensive hyperparameter sweep.

Figure path: `reports/evaluation/methodology_results_summary.md`

Speaker notes:
This slide is where I would explicitly justify not using a CNN. With no GPU and only one locally available asset, a classical boosted regressor is a better engineering choice. It is easy to train, easy to inspect, and strong enough to show measurable value on held-out shots.

## Slide 10. Validation Protocol and Leakage Control

- The original risk in this project was segment-level leakage: segments from the same shot can look too similar across train and test.
- The final protocol splits by `asset_name + shot_id`, not by individual segment file.
- Split seed is `42` with ratios `70/10/20`.
- Result: `482` train shots, `68` validation shots, `139` test shots.
- Overlap checks are explicit and all split-pair overlaps are `0`.

Figure path: `data/processed/splits/split_summary.json`

Speaker notes:
This slide is central to the credibility of the results. Once the evaluation became shot-disjoint, the numbers got harder, but they became believable. That tradeoff is worth making because the goal is generalization, not a flattering offline score.

## Slide 11. Validation Selection Results

- Candidate search metric: corrected MAE on validation correction examples.
- Best configuration: `learning_rate=0.04`, `max_iter=260`, `max_depth=8`, `min_samples_leaf=25`, `l2_regularization=0.0`.
- Best validation baseline MAE: `18.769 ms`.
- Best validation corrected MAE: `10.643 ms`.
- Best validation baseline RMSE: `33.427 ms`.
- Best validation corrected RMSE: `22.079 ms`.

Table path: `data/processed/ml_correction_training_report.json`

Speaker notes:
I would make it clear here that these are patch-level validation numbers, not the final test numbers. They are used for model selection only. The real claim comes from the next slide, where the full held-out segments are evaluated end to end.

## Slide 12. Quantitative Held-Out Test Results

- Test set contains `1,086` held-out segments from `139` shots.
- Metrics are computed over `146,594` valid labeled traces.
- The ML correction stage improves every reported aggregate metric over the refined baseline.

| Method | MAE (ms) | RMSE (ms) | Acc <= 2 ms | Acc <= 4 ms | Acc <= 8 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Refined baseline | 47.694 | 96.458 | 22.662% | 34.172% | 48.610% |
| ML corrected | 37.213 | 87.026 | 36.186% | 50.193% | 62.340% |
| Improvement | 10.481 | 9.433 | +13.524 pts | +16.021 pts | +13.729 pts |

Table path: `reports/evaluation/test_summary_table.csv`

Speaker notes:
This is the main result slide. The absolute errors are still large enough that there is room for improvement, but the direction is clear: the correction stage materially improves both average error and tolerance-based accuracy on unseen shots.

## Slide 13. Visual Comparison Examples

- Best example: `Halfmile_shot20301149_seg000`, MAE improves from `7.06 ms` to `5.06 ms`.
- Median example: `Halfmile_shot20261181_seg001`, MAE improves from `47.30 ms` to `31.72 ms`.
- Worst example: `Halfmile_shot20041590_seg005`, MAE improves only slightly from `436.57 ms` to `428.82 ms`.
- The model helps most when the baseline is close but locally biased.

Figure path: `reports/evaluation/figures/best_Halfmile_shot20301149_seg000.png`

Additional figure paths:

- `reports/evaluation/figures/median_Halfmile_shot20261181_seg001.png`
- `reports/evaluation/figures/worst_Halfmile_shot20041590_seg005.png`

Speaker notes:
I would walk through these three examples quickly. The point is not to hide difficult cases. The point is to show where the model is strong, where it is merely acceptable, and where the entire two-stage approach still struggles.

## Slide 14. Error Analysis and Failure Cases

- `1,048` of `1,086` test segments improved (`96.50%`).
- `36` segments worsened and `2` were unchanged.
- Mean per-segment MAE gain is `10.325 ms`; median gain is `7.747 ms`.
- Worst regression case is `Halfmile_shot20121514_seg024`, where MAE changes from `54.69 ms` to `64.77 ms`.
- Remaining failures are concentrated in segments where the baseline starts far from the true line.

Figure path: `reports/evaluation/figures/regression_Halfmile_shot20121514_seg024.png`

Speaker notes:
This slide keeps the presentation honest. The correction model is not magic. If the baseline is badly wrong, a small local patch around that bad pick may not contain the information needed to recover the true first break.

## Slide 15. Robustness, Limitations, and No-GPU Tradeoffs

- Strength: the final workflow is reproducible, fast enough on CPU, and uses a leakage-safe split.
- Strength: the code path is modular and shared across export, training, and evaluation.
- Limitation: only one asset was locally available for execution, so cross-asset generalization is not yet validated.
- Limitation: the model learns local residuals and can fail when the baseline is globally misaligned.
- Tradeoff: skipping GPU-oriented deep learning reduced infrastructure cost but also capped model expressiveness.

Figure path: none

Speaker notes:
This is where I would explain the engineering stance. Given the local constraints, it was better to produce a trustworthy CPU pipeline and real held-out results than to add an unvalidated deep model that could not be trained properly in this environment.

## Slide 16. Multi-Asset Readiness and What Remains Unverified

- The loader now supports `SHOTID` with `SHOT_PEG` fallback.
- Coordinate and elevation scaling are handled generically through `COORD_SCALE` and `HT_SCALE`.
- `asset_name` is carried through manifests, splits, datasets, and evaluation outputs.
- The same pipeline should run on Brunswick, Lalor, and Sudbury once their raw HDF5 files are added.
- What remains unverified is not the interface, but the empirical behavior on those assets.

Figure path: none

Speaker notes:
I would be explicit here: the code is multi-asset ready by design, but the reported numbers are Halfmile numbers only. That distinction matters in a technical review.

## Slide 17. Final Conclusion

- A full CPU-only Halfmile pipeline was built and validated end to end.
- The final workflow reconstructs 2D panels, enforces shot-disjoint evaluation, learns a residual correction, and reports held-out full-segment metrics.
- On held-out Halfmile shots, ML correction improves MAE by `10.48 ms` and RMSE by `9.43 ms` over the refined baseline.
- The current result is submission-ready for a Halfmile-centered demonstration and provides a clean base for multi-asset extension.

Figure path: `reports/evaluation/test_summary_table.csv`

Speaker notes:
I would close by emphasizing credibility over flash. The main contribution is not only a better score; it is a reproducible workflow with leakage control, CPU feasibility, and clear next steps for multi-asset validation.

## Appendix A. Commands Used for the Final Run

```bash
python scripts/export_segments.py --path data/raw/Halfmile3D_add_geom_sorted.hdf5 --out_dir data/interim/Halfmile_segments --asset_name Halfmile
python scripts/split_segments_train_test.py --segments_dir data/interim/Halfmile_segments --manifest_path data/interim/Halfmile_segments/Halfmile_segments_manifest.json --out_dir data/processed/splits --train_ratio 0.7 --val_ratio 0.1 --seed 42
python scripts/build_ml_dataset.py --segments_dir data/interim/Halfmile_segments --split_json data/processed/splits/train_segments.json --out_npz data/processed/ml_train_dataset.npz
python scripts/build_ml_dataset.py --segments_dir data/interim/Halfmile_segments --split_json data/processed/splits/val_segments.json --out_npz data/processed/ml_val_dataset.npz
python scripts/build_ml_dataset.py --segments_dir data/interim/Halfmile_segments --split_json data/processed/splits/test_segments.json --out_npz data/processed/ml_test_dataset.npz
python scripts/train_ml_correction_model.py --train_npz data/processed/ml_train_dataset.npz --val_npz data/processed/ml_val_dataset.npz --out_model data/processed/ml_correction_model.pkl --out_report data/processed/ml_correction_training_report.json
python scripts/evaluate_ml_correction_model.py --segments_dir data/interim/Halfmile_segments --test_split_json data/processed/splits/test_segments.json --model_pkl data/processed/ml_correction_model.pkl --out_dir reports/evaluation
python -m unittest discover -s tests -v
```

## Appendix B. Artifact Inventory

- Split summary: `data/processed/splits/split_summary.json`
- Training report: `data/processed/ml_correction_training_report.json`
- Held-out summary: `reports/evaluation/test_summary.json`
- Held-out summary table: `reports/evaluation/test_summary_table.csv`
- Per-segment metrics: `reports/evaluation/test_segment_metrics.csv`
- Best, median, worst, regression figures: `reports/evaluation/figures/`
- Compact report summary: `reports/evaluation/methodology_results_summary.md`

## Appendix C. Final Hyperparameters

```json
{
  "model": "HistGradientBoostingRegressor",
  "learning_rate": 0.04,
  "max_iter": 260,
  "max_depth": 8,
  "min_samples_leaf": 25,
  "l2_regularization": 0.0,
  "half_width": 2,
  "half_height": 40,
  "trace_stride": 3,
  "max_abs_correction": 60
}
```

## Appendix D. Extra Qualitative Examples

- Best example figure: `reports/evaluation/figures/best_Halfmile_shot20301149_seg000.png`
- Median example figure: `reports/evaluation/figures/median_Halfmile_shot20261181_seg001.png`
- Worst example figure: `reports/evaluation/figures/worst_Halfmile_shot20041590_seg005.png`
- Regression example figure: `reports/evaluation/figures/regression_Halfmile_shot20121514_seg024.png`
