#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
RUN_STAMP="$(date +%Y%m%d_%H%M%S)"

# This wrapper is for local verification of the ReAct observation/output-contract fix.
# It intentionally delegates to the existing MosciBench debug launcher so the benchmark
# entrypoint and summary logic stay in one place.
export SOURCE_MOSCIBENCH_DATA="${SOURCE_MOSCIBENCH_DATA:-/Users/liufan/projects/data/moscibench}"
export LOCAL_DEBUG_PROFILE="${LOCAL_DEBUG_PROFILE:-serial}"
export KEEP_WORKSPACE="${KEEP_WORKSPACE:-true}"
export MAX_STEPS="${MAX_STEPS:-10}"
export RUN_ROOT="${RUN_ROOT:-$REPO_ROOT/experiments/benchmark/runs/local_moscibench_react_output_contract_debug_$RUN_STAMP}"

# Presets for local verification. Override with either:
#   MOSCI_TASK_PRESET=quick|extended|long_io|full
#   MOSCI_TASKS="mosci-a-1 mosci-b-2"   # explicit list always wins
: "${MOSCI_TASK_PRESET:=extended}"
if [[ -z "${MOSCI_TASKS:-}" ]]; then
  case "$MOSCI_TASK_PRESET" in
    quick)
      export MOSCI_TASKS="mosci-pop_genetics-3 mosci-nurse_stress-15 mosci-cyclone-14 mosci-pop_genetics-4"
      ;;
    extended)
      export MOSCI_TASKS="mosci-pop_genetics-3 mosci-nurse_stress-15 mosci-cyclone-14 mosci-pop_genetics-4 mosci-nurse_stress-6 mosci-nurse_stress-12 mosci-pop_genetics-12 mosci-cyclone-10 mosci-terra-2 mosci-terra-9 mosci-health_spa-15 mosci-massspecgym-15"
      ;;
    long_io)
      export MOSCI_TASKS="mosci-nurse_stress-15 mosci-nurse_stress-6 mosci-nurse_stress-12 mosci-pop_genetics-3 mosci-pop_genetics-4 mosci-pop_genetics-12"
      ;;
    full)
      export MOSCI_TASKS="all"
      ;;
    *)
      echo "ERROR: unsupported MOSCI_TASK_PRESET=$MOSCI_TASK_PRESET; use quick, extended, long_io, or full" >&2
      exit 2
      ;;
  esac
fi

cat <<EOF
repo_root=$REPO_ROOT
source_moscibench_data=$SOURCE_MOSCIBENCH_DATA
profile=$LOCAL_DEBUG_PROFILE
task_preset=$MOSCI_TASK_PRESET
tasks=$MOSCI_TASKS
run_root=$RUN_ROOT
max_steps=$MAX_STEPS
keep_workspace=$KEEP_WORKSPACE
EOF

exec bash "$SCRIPT_DIR/run_local_moscibench_dslighting_workspace_debug.sh"
