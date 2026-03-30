# DACode Example

This directory contains a public launcher for the DACode benchmark.

- Download the prepared dataset release from [Google Drive](https://drive.google.com/file/d/1PYwTW2IXSBKRlX57bZE9inOjlpn2zNoV/view?usp=drive_link).
- Upstream benchmark and citation link: [DA-Code (EMNLP 2024)](https://github.com/yiyihum/da-code).

## Files

- `dacode_readme_test.py`: Python example aligned with the `DSBenchmark` flow
- `run_dacode_readme_test.sh`: one-command launcher

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

benchmark = DSBenchmark("dacode", data_dir="/path/to/dacode")
result = benchmark.run(config=config)

print(result.results_path)
print(result.metadata_path)
```

The launcher defaults to `gpt-4o`. You can override it with `DACODE_MODEL`.

## Setup

Install DSLighting:

```bash
pip install -e .
```

Point the data path at the prepared DACode root that contains the `dacode-*` task folders:

```bash
export DSLIGHTING_DACODE_DATA=/path/to/dacode
```

For model credentials, you can either keep a repository-level `.env` or place a local `.env` file in this directory. The example loads the repository `.env` first, then `examples/benchmark/dacode/.env` if present.

## Run

```bash
cd examples/benchmark/dacode
./run_dacode_readme_test.sh
```

Or pass the dataset path directly:

```bash
cd examples/benchmark/dacode
./run_dacode_readme_test.sh /path/to/dacode
```

You can also choose a specific Python executable:

```bash
cd examples/benchmark/dacode
PYTHON_BIN=/path/to/python ./run_dacode_readme_test.sh /path/to/dacode
```

## Output

When launched through the shell wrapper, benchmark artifacts are written under the repository-level `runs/` directory, typically `runs/benchmarks/dacode` and `runs/dslighting_workspace`.
