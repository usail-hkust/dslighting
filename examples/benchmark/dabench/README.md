# DABench Example

This directory contains a public launcher for the full DABench benchmark.

## Files

- `dabench_readme_test.py`: Python example aligned with the main README benchmark flow
- `run_dabench_readme_test.sh`: one-command launcher

## What This Example Runs

```python
from dotenv import load_dotenv
load_dotenv()

from dslighting.api import DSBenchmark
from dslighting.core import ConfigBuilder

config = ConfigBuilder().build_config(
    workflow="aide",
    model="gpt-4o",
)

benchmark = DSBenchmark("dabench", data_dir="/path/to/dabench")
result = benchmark.run(config=config)

print(result.results_path)
print(result.metadata_path)
```

The launcher defaults to `gpt-4o`. You can override it with `DABENCH_MODEL`.

## Setup

Install DSLighting:

```bash
pip install -e .
```

Point the data path at the extracted DABench root that contains the `dabench-*` task folders:

```bash
export DSLIGHTING_DABENCH_DATA=/path/to/dabench
```

For model credentials, you can either keep a repository-level `.env` or place a local `.env` file in this directory. The example loads the repository `.env` first, then `examples/benchmark/dabench/.env` if present.

## Run

```bash
cd examples/benchmark/dabench
./run_dabench_readme_test.sh
```

Or pass the dataset path directly:

```bash
cd examples/benchmark/dabench
./run_dabench_readme_test.sh /path/to/dabench
```

You can also choose a specific Python executable:

```bash
cd examples/benchmark/dabench
PYTHON_BIN=/path/to/python ./run_dabench_readme_test.sh /path/to/dabench
```

## Output

When launched through the shell wrapper, benchmark artifacts are written under the repository-level `runs/` directory, typically `runs/benchmarks/dabench` and `runs/dslighting_workspace`.
