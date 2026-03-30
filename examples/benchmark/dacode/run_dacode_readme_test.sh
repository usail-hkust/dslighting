#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
TEST_SCRIPT="$SCRIPT_DIR/dacode_readme_test.py"

if [[ $# -ge 1 ]] && [[ -z "${DSLIGHTING_DACODE_DATA:-}" ]]; then
  export DSLIGHTING_DACODE_DATA="$1"
fi

if [[ -z "${DSLIGHTING_DACODE_DATA:-}" && -z "${DACODE_DATA_DIR:-}" ]]; then
  echo "Set DSLIGHTING_DACODE_DATA=/path/to/dacode or pass the data path as the first argument." >&2
  exit 1
fi

if [[ ! -f "$TEST_SCRIPT" ]]; then
  echo "Missing test script: $TEST_SCRIPT" >&2
  exit 1
fi

cd "$REPO_ROOT"
PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BIN" "$TEST_SCRIPT"
