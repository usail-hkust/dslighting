# Conway's Reverse Game of Life 2020

## Task

Given the final state of a 25×25 Conway’s Game of Life board and the number of steps `delta` taken to reach it, recover a valid starting state that evolves into the supplied ending configuration. The grid wraps on both axes, so neighbors include cells across opposite edges. Any starting board that reproduces the published final board after `delta` steps is considered correct.

## Data

- `train.csv` – 50 000 examples with `id`, `delta`, starting board cells (`start_0` … `start_624`), and final board cells (`stop_0` … `stop_624`).
- `test.csv` – held-out games with `id`, `delta`, and final board cells only.
- `sample_submission.csv` – template showing the expected column order (`id`, `start_0` … `start_624`).

All grids are flattened row-wise (25 × 25 = 625 cells).

## Submission Format

Produce a CSV with one row per `id` containing binary predictions (`0` = dead, `1` = alive) for every `start_*` column:

```
id,start_0,start_1,...,start_624
50000,0,0,...,0
50001,1,0,...,0
```

## Evaluation

Submissions are rolled forward `delta` steps under the Game of Life rules and compared to the provided final boards. Because the simulator enforces binary states, this is equivalent to computing the mean absolute error (MAE) between the predicted and true starting grids. We report accuracy as `1 - MAE`, so higher scores are better and a perfect reconstruction scores `1.0`.
