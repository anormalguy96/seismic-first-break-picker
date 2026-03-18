# Notebooks

Starter notebooks for interactive work against the existing Halfmile artifacts in this repository.

- `01_segment_exploration.ipynb` is for manifest stats, segment previews, and geometry sanity checks.
- `02_baseline_and_correction_preview.ipynb` runs the saved correction model on one held-out segment and inspects the local patch input.
- `03_results_review.ipynb` is to review validation candidates, held-out test metrics, and representative figures.

These notebooks assume the current artifacts under `data/interim`, `data/processed`, and `reports/evaluation` are already present.

To rebuild them from raw Halfmile data, you can run:

```bash
python scripts/run_halfmile_pipeline.py --raw_path data/raw/Halfmile3D_add_geom_sorted.hdf5
```
