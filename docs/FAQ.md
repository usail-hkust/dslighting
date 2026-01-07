# FAQ

## Where do I put prepared data?
Use `data/competitions/<competition-id>/prepared/...`.

## How do I run a single task?
Use `run_benchmark.py` with `--task-id <competition>` and `--data-dir`.

## How do I add a new task?
Create a competition folder with `config.yaml` and grading logic, then register it.

## Where are logs saved?
By default: `runs/benchmark_results/<workflow>_on_<benchmark>/<model>/`.
