# ScienceBench Example

This directory contains a public launcher for the full ScienceBench benchmark.

## Files

- `sciencebench_readme_test.py`: Python example aligned with the main README benchmark flow
- `run_sciencebench_readme_test.sh`: one-command launcher
- `requirements.extra.txt`: extra packages copied from `dslighting/benchmark/vendor/sciencebench/requirements.extra.txt`

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

benchmark = DSBenchmark("sciencebench", data_dir="/path/to/scienceagentbench")
result = benchmark.run(config=config)

print(result.results_path)
print(result.metadata_path)
```

The launcher defaults to `gpt-4o`. You can override it with `SCIENCEBENCH_MODEL`.

## Setup

Install DSLighting and the ScienceBench extra dependencies:

```bash
pip install -e .
pip install -r examples/benchmark/sciencebench/requirements.extra.txt
```

Some ScienceBench tasks may still require additional task-specific packages that are not listed in the copied extra requirements file. For example, certain tasks may need `tensorflow`.

Point the data path at the extracted ScienceAgentBench root that contains the `sciencebench-*` task folders:

```bash
export DSLIGHTING_SCIENCEBENCH_DATA=/path/to/scienceagentbench
```

For model credentials, you can either keep a repository-level `.env` or place a local `.env` file in this directory. The example loads the repository `.env` first, then `examples/benchmark/sciencebench/.env` if present.

## Run

```bash
cd examples/benchmark/sciencebench
./run_sciencebench_readme_test.sh
```

Or pass the dataset path directly:

```bash
cd examples/benchmark/sciencebench
./run_sciencebench_readme_test.sh /path/to/scienceagentbench
```

You can also choose a specific Python executable:

```bash
cd examples/benchmark/sciencebench
PYTHON_BIN=/path/to/python ./run_sciencebench_readme_test.sh /path/to/scienceagentbench
```

## Output

When launched through the shell wrapper, benchmark artifacts are written under the repository-level `runs/` directory, typically `runs/benchmarks/sciencebench` and `runs/dslighting_workspace`.

## Notes

- This is a full benchmark run, not a smoke test.
- ScienceBench currently contains many tasks, so runtime and cost can be substantial.
