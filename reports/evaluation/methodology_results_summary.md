# Halfmile Methodology and Results Summary

## Workflow Summary

| Stage | Settings | Verified output |
| --- | --- | --- |
| Raw ingest | Read `TRACE_DATA/DEFAULT`; `SHOTID` with `SHOT_PEG` fallback; apply `COORD_SCALE` and `HT_SCALE` | `1,099,559` traces, `751` samples, `2.0 ms` sampling |
| Segment export | Receiver ordering by `REC_PEG` with `REC_X` fallback; `jump_factor=8.0`; `min_traces=80`; `min_valid_labels=70` | `5,391` exported segments from `689` usable shots |
| Split protocol | Shot-disjoint by `asset_name + shot_id`; seed `42`; `70/10/20` | Train `3,779`, val `526`, test `1,086`; no overlap |
| Baseline picker | Rough pick from thresholded envelope, smooth prior, derivative refinement, final cross-trace smoothing | Refined baseline line per segment |
| Correction dataset | `81 x 5` patch, `405` features, `trace_stride=3`, `max_abs_correction=60` | Train `146,767`, val `21,354`, test `42,072` examples |
| CPU model | `HistGradientBoostingRegressor` candidate search on validation examples | Selected config: `lr=0.04`, `iter=260`, `depth=8`, `leaf=25`, `l2=0.0` |
| Final evaluation | Full-panel inference on held-out test segments; metrics on valid labels only | `1,086` segments, `146,594` valid labeled traces |

## Held-Out Test Results

| Method | MAE (ms) | RMSE (ms) | Acc <= 2 ms | Acc <= 4 ms | Acc <= 8 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Refined baseline | 47.694 | 96.458 | 22.662% | 34.172% | 48.610% |
| ML corrected | 37.213 | 87.026 | 36.186% | 50.193% | 62.340% |
| Improvement | 10.481 | 9.433 | +13.524 pts | +16.021 pts | +13.729 pts |

## Segment-Level Behavior

| Item | Value |
| --- | ---: |
| Test segments | 1,086 |
| Improved segments | 1,048 |
| Worsened segments | 36 |
| Unchanged segments | 2 |
| Improved share | 96.50% |
| Mean per-segment MAE gain | 10.325 ms |
| Median per-segment MAE gain | 7.747 ms |
| Worst regression | -10.083 ms |

## Representative Figures

| Case | Segment | Path |
| --- | --- | --- |
| Best | `Halfmile_shot20301149_seg000` | `reports/evaluation/figures/best_Halfmile_shot20301149_seg000.png` |
| Median | `Halfmile_shot20261181_seg001` | `reports/evaluation/figures/median_Halfmile_shot20261181_seg001.png` |
| Worst | `Halfmile_shot20041590_seg005` | `reports/evaluation/figures/worst_Halfmile_shot20041590_seg005.png` |
| Regression | `Halfmile_shot20121514_seg024` | `reports/evaluation/figures/regression_Halfmile_shot20121514_seg024.png` |
