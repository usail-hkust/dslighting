#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RUN_STAMP="$(date +%Y%m%d_%H%M%S)"

RUN_ROOT="${RUN_ROOT:-$REPO_ROOT/experiments/benchmark/runs/local_moscibench_dslighting_workspace_debug_$RUN_STAMP}"
LOG_DIR="${LOG_DIR:-$RUN_ROOT/moscibench_react}"
STDOUT_LOG="${STDOUT_LOG:-$RUN_ROOT/stdout.log}"
SUBSET_ROOT="${SUBSET_ROOT:-$RUN_ROOT/data}"
SUBSET_COMPETITIONS="$SUBSET_ROOT/competitions"
PYTHON_BIN="${PYTHON_BIN:-$REPO_ROOT/experiments/.venv312_framework/bin/python}"
ENV_FILE="${DSLIGHTING_ENV_FILE:-$REPO_ROOT/.env}"
TARGET_SCRIPT="$REPO_ROOT/experiments/benchmark/run_moscibench_benchmark_react.py"
LOCAL_DEBUG_PROFILE="${LOCAL_DEBUG_PROFILE:-serial}"

if [[ -z "${SOURCE_MOSCIBENCH_DATA:-}" ]]; then
  if [[ -d "/Users/liufan/projects/data/moscibench/competitions" ]]; then
    SOURCE_MOSCIBENCH_DATA="/Users/liufan/projects/data/moscibench"
  elif [[ -d "/Users/liufan/projects/share/data/moscibench_local/competitions" ]]; then
    SOURCE_MOSCIBENCH_DATA="/Users/liufan/projects/share/data/moscibench_local"
  elif [[ -d "/Users/liufan/projects/share/data/moscibench/competitions" ]]; then
    SOURCE_MOSCIBENCH_DATA="/Users/liufan/projects/share/data/moscibench"
  else
    SOURCE_MOSCIBENCH_DATA="$REPO_ROOT/../data/moscibench_local"
  fi
fi

SOURCE_COMPETITIONS="$SOURCE_MOSCIBENCH_DATA"
if [[ -d "$SOURCE_COMPETITIONS/competitions" ]]; then
  SOURCE_COMPETITIONS="$SOURCE_COMPETITIONS/competitions"
fi

case "$LOCAL_DEBUG_PROFILE" in
  serial)
    : "${SCHEDULER_POLICY:=balanced}"
    : "${MAX_CONCURRENCY:=1}"
    : "${LLM_MAX_CONCURRENCY:=1}"
    : "${ENABLE_TASK_RATE_LIMITING:=true}"
    : "${LLM_TASK_START_RATE:=1.0}"
    : "${SANDBOX_TASK_START_RATE:=1.0}"
    : "${TASK_RATE_BURST_FACTOR:=1.0}"
    ;;
  p03)
    : "${SCHEDULER_POLICY:=balanced}"
    : "${MAX_CONCURRENCY:=8}"
    : "${LLM_MAX_CONCURRENCY:=20}"
    : "${ENABLE_TASK_RATE_LIMITING:=true}"
    : "${LLM_TASK_START_RATE:=10.0}"
    : "${SANDBOX_TASK_START_RATE:=20.0}"
    : "${TASK_RATE_BURST_FACTOR:=2.0}"
    ;;
  custom)
    : "${SCHEDULER_POLICY:=balanced}"
    : "${MAX_CONCURRENCY:=1}"
    : "${LLM_MAX_CONCURRENCY:=1}"
    : "${ENABLE_TASK_RATE_LIMITING:=true}"
    : "${LLM_TASK_START_RATE:=1.0}"
    : "${SANDBOX_TASK_START_RATE:=1.0}"
    : "${TASK_RATE_BURST_FACTOR:=1.0}"
    ;;
  *)
    echo "ERROR: unsupported LOCAL_DEBUG_PROFILE=$LOCAL_DEBUG_PROFILE; use serial, p03, or custom" >&2
    exit 2
    ;;
esac

: "${KEEP_WORKSPACE:=true}"
: "${MAX_STEPS:=10}"

DEFAULT_MOSCI_TASKS=(
  "mosci-pop_genetics-3"
  "mosci-nurse_stress-15"
  "mosci-cyclone-14"
  "mosci-pop_genetics-4"
  "mosci-nurse_stress-6"
  "mosci-nurse_stress-12"
  "mosci-pop_genetics-12"
  "mosci-cyclone-10"
  "mosci-terra-2"
  "mosci-terra-9"
  "mosci-health_spa-15"
  "mosci-massspecgym-15"
)

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "ERROR: python not executable: $PYTHON_BIN" >&2
  echo "Set PYTHON_BIN=/path/to/python if you want to use another local env." >&2
  exit 2
fi

if [[ ! -f "$TARGET_SCRIPT" ]]; then
  echo "ERROR: benchmark script not found: $TARGET_SCRIPT" >&2
  exit 2
fi

if [[ ! -d "$SOURCE_COMPETITIONS" ]]; then
  echo "ERROR: MosciBench competitions root not found: $SOURCE_COMPETITIONS" >&2
  echo "Set SOURCE_MOSCIBENCH_DATA=/path/to/moscibench_local or /path/to/moscibench_local/competitions." >&2
  exit 2
fi

mkdir -p "$SUBSET_COMPETITIONS" "$LOG_DIR"

tasks=()
if [[ "${MOSCI_TASKS:-}" == "all" ]]; then
  while IFS= read -r task; do
    tasks+=("$task")
  done < <(find "$SOURCE_COMPETITIONS" -maxdepth 1 -type d -name 'mosci-*' -exec basename {} \; | sort)
elif [[ -n "${MOSCI_TASKS:-}" ]]; then
  normalized_tasks="${MOSCI_TASKS//,/ }"
  read -r -a tasks <<< "$normalized_tasks"
else
  tasks=("${DEFAULT_MOSCI_TASKS[@]}")
fi

if [[ "${#tasks[@]}" -eq 0 ]]; then
  echo "ERROR: no MosciBench tasks selected" >&2
  exit 2
fi

for task in "${tasks[@]}"; do
  src="$SOURCE_COMPETITIONS/$task"
  dst="$SUBSET_COMPETITIONS/$task"
  if [[ ! -d "$src" ]]; then
    echo "ERROR: selected task not found: $src" >&2
    exit 2
  fi
  if [[ ! -e "$dst" ]]; then
    ln -s "$src" "$dst"
  fi
done

export DSLIGHTING_REPO="$REPO_ROOT"
export DSLIGHTING_ENV_FILE="$ENV_FILE"
export DSLIGHTING_MOSCIBENCH_DATA="$SUBSET_ROOT"
export BENCHMARK_LOG_DIR="$LOG_DIR"
export KEEP_WORKSPACE
export MAX_STEPS
export SCHEDULER_POLICY
export MAX_CONCURRENCY
export LLM_MAX_CONCURRENCY
export ENABLE_TASK_RATE_LIMITING
export LLM_TASK_START_RATE
export SANDBOX_TASK_START_RATE
export TASK_RATE_BURST_FACTOR

cat <<EOF
repo_root=$REPO_ROOT
python_bin=$PYTHON_BIN
env_file=$DSLIGHTING_ENV_FILE
source_competitions=$SOURCE_COMPETITIONS
subset_competitions=$SUBSET_COMPETITIONS
run_root=$RUN_ROOT
log_dir=$LOG_DIR
stdout_log=$STDOUT_LOG
profile=$LOCAL_DEBUG_PROFILE
tasks=${tasks[*]}
max_steps=$MAX_STEPS
keep_workspace=$KEEP_WORKSPACE
scheduler_policy=$SCHEDULER_POLICY
max_concurrency=$MAX_CONCURRENCY
llm_max_concurrency=$LLM_MAX_CONCURRENCY
llm_task_start_rate=$LLM_TASK_START_RATE
sandbox_task_start_rate=$SANDBOX_TASK_START_RATE
task_rate_burst_factor=$TASK_RATE_BURST_FACTOR
EOF

if [[ "${DRY_RUN:-false}" == "true" ]]; then
  echo "DRY_RUN=true; not starting benchmark."
  exit 0
fi

set +e
"$PYTHON_BIN" "$TARGET_SCRIPT" 2>&1 | tee "$STDOUT_LOG"
exit_code="${PIPESTATUS[0]}"
set -e

echo
echo "=== Local MosciBench DSLighting Debug Summary ==="
"$PYTHON_BIN" - "$LOG_DIR" "$RUN_ROOT" <<'PY'
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

log_dir = Path(sys.argv[1])
run_root = Path(sys.argv[2])

metadata_files = sorted(log_dir.glob("moscibench_metadata_*.json"))
result_files = sorted(log_dir.glob("moscibench_results_*.csv"))

print(f"run_root={run_root}")
print(f"log_dir={log_dir}")
print(f"metadata_path={metadata_files[-1] if metadata_files else 'N/A'}")
print(f"results_path={result_files[-1] if result_files else 'N/A'}")

if metadata_files:
    metadata = json.loads(metadata_files[-1].read_text())
    score = metadata.get("score", {})
    submissions = metadata.get("submissions", {})
    print(f"total_tasks={metadata.get('total_tasks')}")
    print(f"actual_accuracy={score.get('actual_average')}")
    print(f"scored_task_count={score.get('scored_task_count')}")
    print(f"missing_submission_count={submissions.get('missing_submission_count')}")
    print(f"failed_submission_count={submissions.get('failed_submission_count')}")

if result_files:
    missing_rows = []
    with result_files[-1].open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    for row in rows:
        if str(row.get("submission_exists", "")).lower() != "true":
            missing_rows.append(row)
    print(f"result_rows={len(rows)}")
    print(f"missing_rows={len(missing_rows)}")
    for row in missing_rows[:20]:
        print(
            "missing_submission "
            f"competition_id={row.get('competition_id')} "
            f"submission_path={row.get('submission_path')} "
            f"error={row.get('error_message')}"
        )

    existing_rows = [
        row for row in rows if str(row.get("submission_exists", "")).lower() == "true"
    ]
    for row in existing_rows[:20]:
        print(
            "existing_submission "
            f"competition_id={row.get('competition_id')} "
            f"submission_path={row.get('submission_path')} "
            f"score={row.get('score')}"
        )
PY

exit "$exit_code"
