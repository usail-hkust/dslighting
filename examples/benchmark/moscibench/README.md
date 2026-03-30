# MoSciBench Example

This directory contains a public launcher for the MoSciBench benchmark.

## Files

- `moscibench_readme_test.py`: Python example aligned with the main README benchmark flow
- `run_moscibench_readme_test.sh`: one-command launcher

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

benchmark = DSBenchmark("moscibench", data_dir="/path/to/moscibench/competitions")
result = benchmark.run(config=config)

print(result.results_path)
print(result.metadata_path)
```

The launcher defaults to `gpt-4o`. You can override it with `MOSCIBENCH_MODEL`.

## Setup

Install DSLighting:

```bash
pip install -e .
```

Point the data path at the extracted MoSciBench `competitions/` directory:

```bash
export DSLIGHTING_MOSCIBENCH_DATA=/path/to/moscibench/competitions
```

The public MoSciBench release is deduplicated. Shared family-level public inputs live under `metadata/` in the release root instead of being copied into every task directory. If you need fully self-contained task folders for batch runs, expand the shared files first:

```bash
DATA_ROOT=/path/to/moscibench

for family_dir in "$DATA_ROOT"/metadata/mosci-*; do
  family=$(basename "$family_dir")
  src="$family_dir/prepared/public/"
  [ -d "$src" ] || continue

  for public_dir in "$DATA_ROOT"/competitions/"${family}"-*/prepared/public; do
    [ -d "$public_dir" ] || continue
    rsync -a "$src" "$public_dir/"
  done
done
```

For model credentials, you can either keep a repository-level `.env` or place a local `.env` file in this directory. The example loads the repository `.env` first, then `examples/benchmark/moscibench/.env` if present.

## Run

```bash
cd examples/benchmark/moscibench
./run_moscibench_readme_test.sh
```

Or pass the `competitions/` path directly:

```bash
cd examples/benchmark/moscibench
./run_moscibench_readme_test.sh /path/to/moscibench/competitions
```

You can also choose a specific Python executable:

```bash
cd examples/benchmark/moscibench
PYTHON_BIN=/path/to/python ./run_moscibench_readme_test.sh /path/to/moscibench/competitions
```

## Output

When launched through the shell wrapper, benchmark artifacts are written under the repository-level `runs/` directory, typically `runs/benchmarks/moscibench` and `runs/dslighting_workspace`.
