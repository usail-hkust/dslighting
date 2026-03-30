import os
from pathlib import Path

from dotenv import load_dotenv


EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parents[2]

load_dotenv(REPO_ROOT / ".env")
load_dotenv(EXAMPLE_DIR / ".env", override=True)

from dslighting.api import DSBenchmark
from dslighting.core import ConfigBuilder


data_dir = os.getenv("DSLIGHTING_MOSCIBENCH_DATA") or os.getenv("MOSCIBENCH_DATA_DIR")
if not data_dir:
    raise SystemExit(
        "Set DSLIGHTING_MOSCIBENCH_DATA (or MOSCIBENCH_DATA_DIR) to the extracted "
        "MoSciBench 'competitions/' directory."
    )

model = os.getenv("MOSCIBENCH_MODEL", "gpt-4o")

config = ConfigBuilder().build_config(
    workflow="aide",
    model=model,
)

benchmark = DSBenchmark(
    "moscibench",
    data_dir=data_dir,
)
result = benchmark.run(config=config)

print(result.results_path)
print(result.metadata_path)
