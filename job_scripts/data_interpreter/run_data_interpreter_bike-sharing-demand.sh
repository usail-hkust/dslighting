#!/usr/bin/env bash

set -euo pipefail

DATA_DIR="data/competitions/"
MODEL="${MODEL:-openai/deepseek-ai/DeepSeek-V3.1-Terminus}"

COMPETITION="bike-sharing-demand"

echo "Running data_interpreter on ${COMPETITION}"

python run_benchmark.py \
  --workflow data_interpreter \
  --benchmark mle \
  --data-dir "${DATA_DIR}" \
  --llm-model "${MODEL}" \
  --task-id "${COMPETITION}"
