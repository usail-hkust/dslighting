# MLE-Bench Competitions

This directory hosts the official competition definitions for the MLE-Bench workflow. Each competition bundles the metadata required for orchestration together with the scripts used to prepare data, validate submissions, and score results.

## Adding a New Competition

To register an additional competition, add a new folder under `mlebench/competitions/<competition-name>` and include the following files:

1. `config.yaml` – top-level competition metadata (IDs, task type, modality, scoring, and expected file layout).
2. `description.md` – human-readable overview: problem statement, dataset details, and submission format.
3. `prepare.py` – data preparation hook that downloads/loads the raw data and materializes the prepared artifacts into the public/private directories defined in `config.yaml`.
4. `grade.py` – scoring logic that consumes a submission and the private ground-truth labels, then returns the configured metric.
5. `checksums.yaml` – SHA256 hashes for every artifact emitted by `prepare.py` to guard against accidental drift.
6. `leaderboard.csv` – optional sample leaderboard with historical submissions or reference baselines.

Place the actual dataset (usually `.npy`, `.csv`, or other assets) inside the paired DSFlow repository at `DSFlow/data/competitions/<competition-name>`. Follow the public/private split defined by the configuration:

- `prepared/public/` – files exposed to participants (e.g., train/test splits, sample submissions). Avoid packaging executable code in this directory.
- `prepared/private/` – labels or other hidden assets required exclusively for scoring.

Once the folder structure and data are in place:

1. Run `prepare.py` to materialize the prepared assets.
2. Verify referential integrity by regenerating `checksums.yaml`.
3. Load the competition through `run_benchmark.py` (see the ethanol competition summary) to ensure preparation, loading, and grading complete successfully.

## Supported Modalities

- Time series – sequential data where samples are represented as `(N, T, F)` tensors (N: number of samples, T: time steps, F: feature dimensions).

## Available Competitions

| Competition            | Task Type | Input Shape          | Output Shape           | Metric      | Samples (train/test) |
|------------------------|-----------|----------------------|------------------------|-------------|----------------------|
| handwriting            | Classification | `(N, 152, 3)`   | `(N,)` labels          | Accuracy    | 150 / 850            |
| ethanol-concentration  | Classification | `(N, 1751, 3)`  | `(N,)` labels          | Accuracy    | 261 / 263            |
| ili                    | Forecasting    | `(N, 36, 7)`    | `(N, 24, 7)` sequence  | MSE / MAE   | 617 / 170            |

These competitions demonstrate how to translate diverse time-series problems into the MLE-Bench format, from short handwritten gesture classification to long multivariate ethanol spectroscopy and influenza forecasting tasks.
